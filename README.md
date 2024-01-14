# NVIDIA GPU Fan Controller for linux

A Python based standalone (and a litle 'opinionated') implementation of NVIDIA GPUs fan controller.

```
python3 nvidia_fan_controller.py
```

This script uses an adhoc heuristic algorithm, increasing the GPU fan speed based on its temperature and utilization. The implementation keeps GPU 'silent' while idle: all GPUs temperature are smaller than a certain threshold (default is 40 degrees Celsius) and GPUs utilization are less than 10%.

## Dependencies

The `nvidia_fan_controller.py` script does not depend on any other python libraries. It does, however, require the following two command-line utilities:

- `nvidia-settings`
- `nvidia-smi`

Please make sure that these are installed on your system.

Also, make sure that you've enabled manual fan control on your system. This can be done by using the `nvidia-xconfig` command-line utility:

```
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
