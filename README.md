# enjoy

[![Pypi Version](https://img.shields.io/pypi/v/enjoy.svg)](https://pypi.python.org/pypi/enjoy)
[![Python Versions](https://img.shields.io/pypi/pyversions/enjoy.svg)](https://pypi.python.org/pypi/enjoy)

Pure python, concurrency agnostic, access to linux input system. Useful for controlling game pads, joysticks

## Command line

```
$ python -m enjoy.cli table
+------------------------------------------------+--------------------+-------------------------+
|        Sony PLAYSTATION(R)3 Controller         | /dev/input/event26 | SYN, KEY, ABS, MSC, FF  |
+------------------------------------------------+--------------------+-------------------------+
...


$ python -m enjoy.cli listen /dev/input/event26
X: 129 Y:126 Z:  0 | RX: 128 RY:128 RZ:  0 | EAST WEST
```

## API

API not documented yet. Just this example:

```python
import time
from enjoy.input import find_gamepads

pad = next(find_gamepads())
abs = pad.absolute

with pad:
	while True:
		print(f"X:{abs.x:>3} | Y:{abs.y:>3} | RX:{abs.rx:>3} | RY:{abs.ry:>3}", end="\r", flush=True)
		time.sleep(0.1)
```
