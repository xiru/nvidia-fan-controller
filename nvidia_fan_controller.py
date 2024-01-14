#!/usr/bin/env python3

import logging
import subprocess
import re
import argparse
from time import sleep


logger = logging.getLogger('nvidia-fan-controller')


def run_cmd(cmd):
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


def get_measurements():
    stdout = run_cmd(['nvidia-smi', '--query-gpu=index,temperature.gpu,fan.speed,utilization.gpu', '--format=csv,noheader'])
    measurements = re.findall(r'(\d+), (\d+), (\d+) %, (\d+) %', stdout, flags=re.MULTILINE)
    return [tuple(map(int, values)) for values in measurements]   # [(index, temperature, fan_speed, utilization)]


def disable_manual_gpu_fan_control():
    logger.debug("disabling manual gpu fan control")
    run_cmd(['nvidia-settings', '--assign', 'GPUFanControlState=0'])


def set_fan_speed(index, fan_speed):
    config = f'[fan-{index:d}]/GPUTargetFanSpeed={fan_speed:d}'
    logger.info("Setting new fan speed: %s", config)
    run_cmd(['nvidia-settings', '--assign', 'GPUFanControlState=1', '--assign', config])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--interval-secs', type=int, default=5,
                        help="number of seconds between consecutive updates")
    parser.add_argument('--log-level', choices=('DEBUG', 'INFO', 'WARN'), default='INFO',
                        help="verbosity level")
    args = parser.parse_args()

    logging.basicConfig(level=getattr(logging, args.log_level))

    measurements = get_measurements()

    if not measurements:
        raise RuntimeError("no gpu detected")

    while True:

        # check if all gpus are idle
        idle = True
        for _, temperature, _, utilization in measurements:
            if temperature > 40 or utilization > 10:
                idle = False
                break
        if idle:
            disable_manual_gpu_fan_control()
        else:

            for index, temperature, fan_speed, _ in measurements:

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
                    set_fan_speed(index, new_fan_speed)

        sleep(args.interval_secs)

        measurements = get_measurements()


if __name__ == '__main__':
    try:
        main()
    finally:
        disable_manual_gpu_fan_control()
