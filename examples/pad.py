import time
from enjoy.input import find_gamepads

pad = next(find_gamepads())
abs = pad.absolute

with pad:
    while True:
        print(
            f"X:{abs.x:>3} | Y:{abs.y:>3} | RX:{abs.rx:>3} | RY:{abs.ry:>3}",
            end="\r",
            flush=True,
        )
        time.sleep(0.1)
