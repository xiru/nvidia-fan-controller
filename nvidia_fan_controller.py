#!/usr/bin/env python3

import sys
import logging
import subprocess
import re
import argparse
from time import sleep


logger = logging.getLogger('nvidia-fan-controller')


class NVidiaFanController(object):

    def __init__(self, interval_secs, base_temp):
        self.interval_secs = interval_secs
        self.base_temp = base_temp
        self.fan_control = False
        self._lookup()

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
        ''' retrieve metrics using nvidia-smi as [(index, temperature, utilization)]
        '''
        stdout = self._run_cmd(['nvidia-smi', '--query-gpu=index,temperature.gpu,utilization.gpu', '--format=csv,noheader'])
        measurements = [tuple(map(int, values)) for values in re.findall(r'(\d+), (\d+), (\d+) %', stdout, flags=re.MULTILINE)]
        if not measurements:
            raise RuntimeError("no gpu detected")
        return measurements

    def _lookup(self):
        self.measurements = self.get_measurements()

    def disable_manual_gpu_fan_control(self):
        if self.fan_control:
            logger.debug("Disabling manual gpu fan control")
            self._run_cmd(['nvidia-settings', '--assign', 'GPUFanControlState=0'])
            self.fan_control = False

    def set_fan_speed(self, fan_speed):
        logger.info("Setting new fan speed: %d", fan_speed)
        self._run_cmd(['nvidia-settings', '--assign', 'GPUFanControlState=1', '--assign', f'GPUTargetFanSpeed={fan_speed}'])
        self.fan_control = True

    @property
    def idle(self):
        # TODO: consider GPUs idle when this condition happens during 5 minutes.
        for _, temperature, utilization in self.measurements:
            if temperature > self.base_temp or utilization > 10:
                return False
        return True

    @property
    def max_temperature(self):
        return max([m[1] for m in self.measurements])

    def _run(self):
        while True:
            if self.idle:
                self.disable_manual_gpu_fan_control()
            else:
                temperature = self.max_temperature

                # predictable fan speed ramp
                if temperature > self.base_temp + 20:
                    new_fan_speed = 100
                elif temperature > self.base_temp + 15:
                    new_fan_speed = 90
                elif temperature > self.base_temp + 10:
                    new_fan_speed = 75
                elif temperature > self.base_temp + 5:
                    new_fan_speed = 60
                else:
                    new_fan_speed = 30

                # TODO: don't keep trying to set the same fan speed repeatedly
                self.set_fan_speed(new_fan_speed)

            sleep(self.interval_secs)
            self._lookup()

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
    parser.add_argument('--base-temp', type=int, default=40,
                        help="base temperature used for fan speed ramp (degrees Celsius)")
    parser.add_argument('--log-level', choices=('DEBUG', 'INFO', 'WARN'), default='INFO',
                        help="verbosity level")
    args = parser.parse_args()

    logging.basicConfig(level=getattr(logging, args.log_level))

    if args.base_temp < 35 or args.base_temp > 60:
        msg = f"Invalid base temperature: {args.base_temp}. Acceptable range is [35-60] degrees Celsius."
        logger.error(msg)
        sys.exit(1)

    NVidiaFanController(args.interval_secs, args.base_temp).run()
