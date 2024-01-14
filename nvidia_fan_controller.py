#!/usr/bin/env python3

import logging
import subprocess
import re
import argparse
from time import sleep


logger = logging.getLogger('nvidia-fan-controller')


class NVidiaFanController(object):

    def __init__(self, interval_secs=2):
        self.fan_control = False
        self.interval_secs = interval_secs
        self.lookup()

    def _run_cmd(self, cmd):
        logger.debug("Running cmd: %s", ' '.join(cmd))
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        p.wait()

        if p.returncode:
            logger.critical("Unable to run cmd: %s", ' '.join(cmd))
            if p.stderr is not None:
                for line_bytes in p.stderr.readlines():
                    line = line_bytes.decode().strip()
                    if line:
                        logger.error("Caught process stderr: %s", line)
            raise subprocess.CalledProcessError(p.returncode, cmd)

        return '' if p.stdout is None else p.stdout.read().decode()

    def get_measurements(self):
        ''' retrieve metrics using nvidia-smi as [(index, temperature, fan_speed, utilization)]
        '''
        stdout = self._run_cmd(['nvidia-smi', '--query-gpu=index,temperature.gpu,fan.speed,utilization.gpu', '--format=csv,noheader'])
        measurements = [tuple(map(int, values)) for values in re.findall(r'(\d+), (\d+), (\d+) %, (\d+) %', stdout, flags=re.MULTILINE)]
        if not measurements:
            raise RuntimeError("no gpu detected")
        return measurements

    def lookup(self):
        self.measurements = self.get_measurements()

    def disable_manual_gpu_fan_control(self):
        if self.fan_control:
            logger.debug("Disabling manual gpu fan control")
            self._run_cmd(['nvidia-settings', '--assign', 'GPUFanControlState=0'])
            self.fan_control = False

    def set_fan_speed(self, index, fan_speed):
        logger.info("Setting new fan speed %s on gpu %d", fan_speed, index)
        config = f'[fan-{index:d}]/GPUTargetFanSpeed={fan_speed:d}'
        self._run_cmd(['nvidia-settings', '--assign', 'GPUFanControlState=1', '--assign', config])
        self.fan_control = True

    def idle(self):
        ''' check if all gpus are idle
        '''
        for _, temperature, _, utilization in self.measurements:
            if temperature > 40 or utilization > 10:
                return False
        return True

    def _run(self):
        while True:
            if self.idle():
                self.disable_manual_gpu_fan_control()
            else:
                for index, temperature, fan_speed, _ in self.measurements:
                    # predictable (hardcoded) fan speed ramp
                    if temperature > 60:
                        new_fan_speed = 100
                    elif temperature > 55:
                        new_fan_speed = 90
                    elif temperature > 50:
                        new_fan_speed = 75
                    elif temperature > 45:
                        new_fan_speed = 60
                    else:
                        new_fan_speed = 30
                    if abs(new_fan_speed - fan_speed) > 2:
                        self.set_fan_speed(index, new_fan_speed)
            sleep(self.interval_secs)
            self.lookup()

    def run(self):
        try:
            self._run()
        except KeyboardInterrupt:
            pass
        finally:
            self.disable_manual_gpu_fan_control()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--interval-secs', type=int, default=5,
                        help="number of seconds between consecutive updates")
    parser.add_argument('--log-level', choices=('DEBUG', 'INFO', 'WARN'), default='INFO',
                        help="verbosity level")
    args = parser.parse_args()

    logging.basicConfig(level=getattr(logging, args.log_level))

    NVidiaFanController(args.interval_secs).run()
