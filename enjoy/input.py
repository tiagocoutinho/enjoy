# -*- coding: utf-8 -*-
#
# This file is part of the enjoy project
#
# Copyright (c) 2021 Tiago Coutinho
# Distributed under the GPLv3 license. See LICENSE for more info.

from __future__ import division
from __future__ import print_function

import os
import enum
import glob
import stat
import fcntl
import ctypes
import select
import struct
import asyncio

from ._input import *

# --------------------------------------------------------------------------
# Just some shortcuts
# --------------------------------------------------------------------------

int_size = ctypes.sizeof(ctypes.c_int)
event_size = ctypes.sizeof(input_event)

# --------------------------------------------------------------------------
#                       Linux ioctl numbers made easy
# --------------------------------------------------------------------------

_IOC_NRBITS = 8
_IOC_TYPEBITS = 8

# architecture specific
_IOC_SIZEBITS = 14
_IOC_DIRBITS = 2

_IOC_NRMASK = (1 << _IOC_NRBITS) - 1
_IOC_TYPEMASK = (1 << _IOC_TYPEBITS) - 1
_IOC_SIZEMASK = (1 << _IOC_SIZEBITS) - 1
_IOC_DIRMASK = (1 << _IOC_DIRBITS) - 1

_IOC_NRSHIFT = 0
_IOC_TYPESHIFT = _IOC_NRSHIFT + _IOC_NRBITS
_IOC_SIZESHIFT = _IOC_TYPESHIFT + _IOC_TYPEBITS
_IOC_DIRSHIFT = _IOC_SIZESHIFT + _IOC_SIZEBITS

_IOC_NONE = 0
_IOC_WRITE = 1
_IOC_READ = 2


def _IOC(dir, type, nr, size):
    if isinstance(size, str):
        size = struct.calcsize(size)
    return (
        dir << _IOC_DIRSHIFT
        | type << _IOC_TYPESHIFT
        | nr << _IOC_NRSHIFT
        | size << _IOC_SIZESHIFT
    )


def _IO(type, nr):
    return _IOC(_IOC_NONE, type, nr, 0)


def _IOR(type, nr, size):
    return _IOC(_IOC_READ, type, nr, size)


def _IOW(type, nr, size):
    return _IOC(_IOC_WRITE, type, nr, size)


def _IOWR(type, nr, size):
    return _IOC(_IOC_READ | _IOC_WRITE, type, nr, size)


def _enum_max(enu):
    # danger: assuming last enum element is _MAX (ex: Key is KEY_MAX)
    if isinstance(enu, enum.Enum):
        enu = type(enu)
    return tuple(enu)[-1]


def _enum_bit_size(enu):
    return _enum_max(enu) // 8 + 1


class input_mt_request_layout:
    __slots__ = ('code', 'values')

    def __init__(self, code, values):
        self.code = code
        self.values = values


EVDEV_MAGIC = ord(b'E')

_S_BUFF = 512

EVIOCGVERSION = _IOR(EVDEV_MAGIC, 0x01, int_size)
EVIOCGID = _IOR(EVDEV_MAGIC, 0x02, ctypes.sizeof(input_id))
EVIOCGREP = _IOR(EVDEV_MAGIC, 0x03, 2*ctypes.sizeof(ctypes.c_uint))
EVIOCGNAME = _IOR(EVDEV_MAGIC, 0x06, _S_BUFF)
EVIOCGPHYS = _IOR(EVDEV_MAGIC, 0x07, _S_BUFF)
EVIOCGUNIQ = _IOR(EVDEV_MAGIC, 0x08, _S_BUFF)
#EVIOCGPROP = _IOR(EVDEV_MAGIC, 0x09, _S_BUFF)
EVIOCGKEY = _IOR(EVDEV_MAGIC, 0x18, _enum_bit_size(Key))
EVIOCGLED = _IOR(EVDEV_MAGIC, 0x19, _enum_bit_size(Led))
EVIOCGSND = _IOR(EVDEV_MAGIC, 0x1a, _enum_bit_size(Sound))
EVIOCGSW = _IOR(EVDEV_MAGIC, 0x1b, _enum_bit_size(Switch))


def EVIOCGMTSLOTS(nb_slots):
    return _IOR(EVDEV_MAGIC, 0x0a, (nb_slots+1) * ctypes.sizeof(ctypes.c_int32))


def EVIOCGBIT(event_type_value, size):
    return _IOR(EVDEV_MAGIC, 0x20 + event_type_value, size)


def EVIOCGABS(abs_type_value):
    return _IOR(EVDEV_MAGIC, 0x40 + abs_type_value,
                ctypes.sizeof(input_absinfo))


def EVIOCSABS(abs_type_value):
    raise NotImplementedError


EVIOCSFF = _IOW(EVDEV_MAGIC, 0x80, ctypes.sizeof(ff_effect))
EVIOCRMFF = _IOW(EVDEV_MAGIC, 0x81, int_size)
EVIOCGEFFECTS = _IOR(EVDEV_MAGIC, 0x84, int_size)
EVIOCGRAB = _IOW(EVDEV_MAGIC, 0x90, int_size)
EVIOCGMASK = _IOR(EVDEV_MAGIC, 0x92, ctypes.sizeof(input_mask))
EVIOCSMASK = _IOW(EVDEV_MAGIC, 0x93, ctypes.sizeof(input_mask))


def grab(fd):
    fcntl.ioctl(fd, EVIOCGRAB, 1)


def release(fd):
    fcntl.ioctl(fd, EVIOCGRAB, 0)


def version(fd):
    result = ctypes.c_int()
    fcntl.ioctl(fd, EVIOCGVERSION, result)
    return result.value


def device_id(fd):
    result = input_id()
    fcntl.ioctl(fd, EVIOCGID, result)
    return result


def name(fd):
    result = ctypes.create_string_buffer(_S_BUFF)
    fcntl.ioctl(fd, EVIOCGNAME, result)
    return result.value.decode()


def physical_location(fd):
    result = ctypes.create_string_buffer(_S_BUFF)
    fcntl.ioctl(fd, EVIOCGPHYS, result)
    return result.value.decode()


def uid(fd):
    result = ctypes.create_string_buffer(_S_BUFF)
    fcntl.ioctl(fd, EVIOCGUNIQ, result)
    return result.value.decode()


def _bit(array, bit):
    return ord(array[bit//8]) & (1 << (bit % 8))


def _active(fd, code, dtype):
    result = ctypes.create_string_buffer(_enum_bit_size(dtype))
    fcntl.ioctl(fd, code, result)
    return {item for item in dtype if _bit(result, item)}


def active_keys(fd):
    return _active(fd, EVIOCGKEY, Key)


def active_leds(fd):
    return _active(fd, EVIOCGLED, Led)


def active_sounds(fd):
    return _active(fd, EVIOCGSND, Sound)


def active_switches(fd):
    return _active(fd, EVIOCGSW, Switch)


def abs_info(fd, abs_code):
    result = input_absinfo()
    fcntl.ioctl(fd, EVIOCGABS(abs_code), result)
    return result


def available_event_types(fd):
    nb_bytes = _enum_bit_size(EventType)
    result = ctypes.create_string_buffer(nb_bytes)
    fcntl.ioctl(fd, EVIOCGBIT(0, nb_bytes), result)
    return {ev_type for ev_type in EventType if _bit(result, ev_type)}


def event_type_capabilities(fd, event_type):
    if event_type == EventType.EV_SYN:
        # cannot query EventType.EV_SYN so just return all possibilities
        return list(Synchronization)[:-1] # remove SYN_MAX
    elif event_type == EventType.EV_REP:
        # nothing in particular to report
        return []
    event_code_type = EVENT_TYPE_MAP[event_type]
    nb_bytes = _enum_bit_size(event_code_type)
    event_codes_bits = ctypes.create_string_buffer(nb_bytes)
    fcntl.ioctl(fd, EVIOCGBIT(event_type, nb_bytes), event_codes_bits)
    return {c for c in event_code_type if _bit(event_codes_bits, c)}


def auto_repeat_settings(fd):
    result = (ctypes.c_uint*2)()
    fcntl.ioctl(fd, EVIOCGREP, result)
    return {rep: result[rep] for rep in AutoRepeat}


def capabilities(fd):
    event_types = available_event_types(fd)
    return { event_type: event_type_capabilities(fd, event_type)
             for event_type in event_types }


def capabilities_str(caps, indent=''):
    lines = []
    sub_indent = indent if indent else '  '
    for cap, values in caps.items():
        lines.append('{}{}:'.format(indent, cap.name))
        lines.extend((2*sub_indent + value.name for value in values))
    return '\n'.join(lines)


def get_input_mask(fd, event_type):
    event_code_type = EVENT_TYPE_MAP[event_type]
    nb_bytes = _enum_bit_size(event_code_type)
    event_codes_bits = ctypes.create_string_buffer(nb_bytes)
    result = input_mask()
    result.type = event_type
    result.codes_size = nb_bytes
    result.codes_ptr = ctypes.cast(event_codes_bits, ctypes.c_void_p)
    fcntl.ioctl(fd, EVIOCGMASK, result)
    return result, event_codes_bits


def read_event(fd, read=os.read):
    data = read(fd, event_size)
    if len(data) < event_size:
        raise ValueError
    return input_event.from_buffer_copy(data)


def list_devices(base_dir='/dev/input'):
    '''List readable character devices in ``input_device_dir``.'''
    fns = glob.glob('{}/event*'.format(base_dir))
    return list(filter(is_device, fns))


def is_device(fn):
    '''Check if ``fn`` is a readable and writable character device.'''

    if not os.path.exists(fn):
        return False

    m = os.stat(fn)[stat.ST_MODE]
    if not stat.S_ISCHR(m):
        return False

    if not os.access(fn, os.R_OK | os.W_OK):
        return False

    return True


def _build_struct_type(struct, funcs=None):
    name = ''.join(map(str.capitalize, struct.__name__.split('_')))
    field_names = [f[0] for f in struct._fields_]
    klass = collections.namedtuple(name, field_names)
    if funcs is None:
        funcs = {}
    _identity = lambda o, v: v
    def from_struct(s):
        fields = {name: funcs.get(name, _identity)(s, getattr(s, name))
                  for name in field_names}
        return klass(**fields)
    klass.from_struct = from_struct
    return klass


InputId = _build_struct_type(input_id,
                               dict(bustype=lambda o, v: Bus(v)))
InputEvent = _build_struct_type(input_event,
                                dict(time=lambda o, t: t.tv_sec + (t.tv_usec)*1e-6,
                                     type=lambda o, t: EventType(t),
                                     code=lambda o, c: EVENT_TYPE_MAP[o.type](c)))


class InputFile(object):

    def __init__(self, path):
        self.path = path
        self._fd = None

    def open(self):
        self.close()
        self._fd = os.open(self.path, flags=os.O_RDWR | os.O_NONBLOCK)

    def close(self):
        if self._fd is not None:
            os.close(self._fd)
            self._fd = None

    def fileno(self):
        return self._fd

    def read(self, n):
        return os.read(self._fd, n)

    def write(self, data):
        return os.write(self._fd, data)


class _Type:

    _event_type = None

    def __init__(self, device=None):
        self.device = device

    def __get__(self, obj, type=None):
        if self._event_type not in obj.capabilities:
            name = EVENT_TYPE_MAP[self._event_type].__name__.lower()
            raise ValueError('device has no {!r} capability'.format(name))
        return self.__class__(obj)

    def _check_code(self, code):
        if code not in self.device.capabilities[self._event_type]:
            raise ValueError('device has no {!r} capability'.format(code.name))


class _Abs(_Type):

    _event_type = EventType.EV_ABS

    def __getitem__(self, code):
        self._check_code(code)
        return self.device.get_abs_info(code).value

    def __getattr__(self, key):
        name = 'ABS_' + key.upper()
        try:
            return self[Absolute[name]]
        except KeyError:
            return super().__getattr__(key)

    def __dir__(self):
        return [k.name[4:].lower() for k in self.device.capabilities[self._event_type]]


class _Keys(_Type):

    _event_type = EventType.EV_KEY

    def __dir__(self):
        return [k.name for k in self.device.capabilities[self._event_type]]

    def __getitem__(self, code):
        self._check_code(code)
        return code in self.device.active_keys

    def __getattr__(self, name):
        try:
            return self[Key[name.upper()]]
        except KeyError:
            return super().__getattr__(name)


class InputDevice(object):

    absolute = _Abs()
    keys = _Keys()

    def __init__(self, path):
        self._caps = None
        self._fileobj = InputFile(path)

    def __enter__(self):
        self._fileobj.open()
        return self

    def __exit__(self, exc_type, exc_value, tb):
        self.close()

    def fileno(self):
        return self._fileobj.fileno()

    def open(self):
        self._fileobj.open()

    def close(self):
        self._fileobj.close()

    @property
    def uid(self):
        return uid(self._fileobj)

    @property
    def name(self):
        return name(self._fileobj)

    @property
    def version(self):
        return version(self._fileobj)

    @property
    def physical_location(self):
        return physical_location(self._fileobj)

    @property
    def device_id(self):
        return device_id(self._fileobj)

    @property
    def capabilities(self):
        if self._caps is None:
            self._caps = capabilities(self._fileobj)
        return self._caps

    @property
    def active_keys(self):
        return active_keys(self._fileobj)

    def get_abs_info(self, abs_code):
        return abs_info(self._fileobj, abs_code)

    @property
    def x(self):
        return self.get_abs_info(Absolute.ABS_X).value

    @property
    def y(self):
        return self.get_abs_info(Absolute.ABS_Y).value

    @property
    def z(self):
        return self.get_abs_info(Absolute.ABS_Z).value

    @property
    def rx(self):
        return self.get_abs_info(Absolute.ABS_RX).value

    @property
    def ry(self):
        return self.get_abs_info(Absolute.ABS_RY).value

    @property
    def rz(self):
        return self.get_abs_info(Absolute.ABS_RZ).value

    def read_event(self):
        """
        Read event.
        Event must be available to read or otherwise will raise an error
        """
        return InputEvent.from_struct(read_event(self._fileobj.fileno()))


def event_stream(fd):
    while True:
        select.select((fd,), (), ())
        yield InputEvent.from_struct(read_event(fd))


async def async_event_stream(fd, maxsize=1000):
    loop = asyncio.get_event_loop()
    queue = asyncio.Queue(maxsize=maxsize)
    loop.add_reader(fd, lambda: queue.put_nowait(read_event(fd)))
    try:
        while True:
            yield InputEvent.from_struct(await queue.get())
    finally:
        loop.remove_reader(fd)


def find_gamepads():
    for path in list_devices():
        with InputDevice(path) as dev:
            caps = dev.capabilities
        if EventType.EV_ABS in caps and Key.BTN_GAMEPAD in caps.get(EventType.EV_KEY, ()):
            yield dev


def find_keyboards():
    for path in list_devices():
        with InputDevice(path) as dev:
            caps = dev.capabilities
        key_caps = caps.get(EventType.EV_KEY, ())
        if Key.KEY_A in key_caps and Key.KEY_CAPSLOCK in key_caps:
            yield dev


def main():
    import sys
    with InputDevice(sys.argv[1]) as dev:
        print('version:', version(dev))
        print('ID: bus={0.bustype} vendor={0.vendor} product={0.product} ' \
              'version={0.version}'
              .format(device_id(dev)))
        print('name:', name(dev))
        print('physical_location:', physical_location(dev))
    #    print('UID:', uid(fd))
        print('capabilities:\n{}'.format(capabilities_str(capabilities(dev),
                                                          indent='  ')))
        print('key state:', active_keys(dev))

    return dev


if __name__ == '__main__':
    dev = main()
