#
# This file is part of the enjoy project
#
# Copyright (c) 2021 Tiago Coutinho
# Distributed under the GPLv3 license. See LICENSE for more info.

import shutil
import asyncio

import typer
import beautifultable

from enjoy.input import InputDevice, EventType, list_devices, async_event_stream


app = typer.Typer()


def name(code):
    return code.name.split("_", 1)[-1]


def names(codes, sep=" "):
    return sep.join(name(code) for code in codes)


def create_state(dev):
    state = {}
    for event_type, codes in dev.capabilities.items():
        if event_type == EventType.EV_KEY:
            state["keys"] = dev.active_keys
            state["pressed"] = names(state["keys"])
        elif event_type == EventType.EV_ABS:
            state["abs"] = {
                name(code): "{:3d}".format(dev.get_abs_info(code).value)
                for code in codes
            }
        elif event_type == EventType.EV_FF:
            # TODO
            pass
    return state


def create_state_template(state):
    template = []
    if "abs" in state:
        if "X" in state['abs']:
            template.append("X: {abs[X]} Y:{abs[Y]} Z:{abs[Z]}")
        if "RX" in state['abs']:
            template.append("RX: {abs[RX]} RY:{abs[RY]} RZ:{abs[RZ]}")
    if "keys" in state:
        template.append("{pressed}")
    return " | ".join(template)


@app.command()
def table():
    table = beautifultable.BeautifulTable()
    table.maxwidth = shutil.get_terminal_size().columns
    for path in list_devices():
        with InputDevice(path) as dev:
            caps = ", ".join(name(cap) for cap in dev.capabilities)
            table.rows.append((dev.name, path, caps))
    typer.echo(table)


@app.command()
def listen(path: str):
    CLEAR_LINE = "\r\x1b[0K"
    async def event_loop():
        async for event in async_event_stream(device.fileno()):
            if event.type == EventType.EV_KEY:
                keys = state["keys"]
                (keys.add if event.value else keys.discard)(event.code)
                state["pressed"] = names(keys)
            elif event.type == EventType.EV_ABS:
                state["abs"][name(event.code)] = f"{event.value:3d}"
            elif event.type == EventType.EV_FF:
                # TODO
                pass
            else:
                continue
            print(CLEAR_LINE + template.format(**state), end="", flush=True)

    with InputDevice(path) as device:
        state = create_state(device)
        template = create_state_template(state)
        asyncio.run(event_loop())


@app.command()
def info(path: str):
    with InputDevice(path) as dev:
        typer.echo(dev.name)
        for cap, items in dev.capabilities.items():
            items = ", ".join(item.name.rsplit("_", 1)[-1] for item in items)
            typer.echo("{}: {}".format(cap.name, items))


if __name__ == "__main__":
    app()
