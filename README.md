# Nvidia GPU Fan Controller for linux

A simple **standalone python script** to keep your Nvidia GPUs below a given temperature, e.g.

```
python3 nvidia_fan_controller.py --target-temperature 60
```

This script uses a simple [PID-controller](https://en.wikipedia.org/wiki/PID_controller) to regulate
the fan speed.


## Dependencies

The `nvidia_fan_controller.py` script does not depend on any other python libraries. It does,
however, require the following two command-line utilities:

- `nvidia-settings`
- `nvidia-smi`

Please make sure that these are installed on your system.

Also, make sure that you've enabled manual fan control on your system. This can be done by using the
`nvidia-xconfig` command-line utility:

```
nvidia-xconfig --cool-bits=4
```


## Contributing

To check the script for inconsistencies, I run:

```
virtualenv .venv
source .venv/bin/activate
pip install pycodestyle
pycodestyle --max-line-length=160 nvidia_fan_controller.py
DISPLAY=:0 python3 nvidia_fan_controller.py --log-level DEBUG
```
