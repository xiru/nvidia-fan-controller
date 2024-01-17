# NVIDIA GPU Fan Controller for linux

A simplified (and a litle 'opinionated') Python based implementation of NVIDIA GPUs fan controller.

```
$ DISPLAY=:0 python3 nvidia_fan_controller.py --help
usage: nvidia_fan_controller.py [-h] [--interval-secs INTERVAL_SECS] [--base-temp BASE_TEMP] [--log-level {DEBUG,INFO,WARN}]

options:
  -h, --help            show this help message and exit
  --interval-secs INTERVAL_SECS
                        number of seconds between consecutive updates
  --base-temp BASE_TEMP
                        base temperature used for fan speed ramp (degrees Celsius)
  --log-level {DEBUG,INFO,WARN}
                        verbosity level
```

This script uses an adhoc heuristic algorithm, increasing the GPU fan speed based on GPUs temperature and utilization. The implementation keeps GPUs 'silent' when idle: all GPUs temperature are smaller than a certain threshold (default is 40 degrees Celsius) and GPUs utilization are less than 10%. When GPUs are busy and getting hot, the highest GPU temperature is used to decide how fast ALL the fans should spin.

## Dependencies

The `nvidia_fan_controller.py` script does not depend on any other python libraries. It does, however, require the following two command-line utilities:

- `nvidia-settings`
- `nvidia-smi`

Please make sure that these are installed on your system.

Also, make sure that you've enabled manual fan control on your system. This can be done by using the `nvidia-xconfig` command-line utility:

```
nvidia-xconfig --enable-all-gpus
nvidia-xconfig --cool-bits=4
```

## Credits

Thanks Kristian Holsheimer for [nvidia-fan-controller](https://github.com/KristianHolsheimer/nvidia-fan-controller) original code.

## Contributing

To check the script for inconsistencies, I run:

```
virtualenv .venv
source .venv/bin/activate
pip install pycodestyle
pycodestyle --max-line-length=160 nvidia_fan_controller.py
DISPLAY=:0 python3 nvidia_fan_controller.py --log-level DEBUG
```
