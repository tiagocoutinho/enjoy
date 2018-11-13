# -*- coding: utf-8 -*-
#
# This file is part of the enjoy project
#
# Copyright (c) 2018 Tiago Coutinho
# Distributed under the MIT. See LICENSE for more info.

from __future__ import print_function
from __future__ import division

import fcntl
import ctypes
import struct

from . import enums


class timeval(ctypes.Structure):
    _fields_ = [
        ("tv_sec", ctypes.c_long),
        ("tv_usec", ctypes.c_long)
    ]


class input_event(ctypes.Structure):
    _fields_ = [
        ('time', timeval),
        ('type', ctypes.c_uint16),
        ('code', ctypes.c_uint16),
        ('value', ctypes.c_int32),
    ]


class input_id(ctypes.Structure):
    _fields_ = [
        ('bustype', ctypes.c_uint16),
        ('vendor', ctypes.c_uint16),
        ('product', ctypes.c_uint16),
        ('version', ctypes.c_uint16),
    ]


class input_absinfo(ctypes.Structure):
    _fields_ = [
        ('value', ctypes.c_int32),
        ('minimum', ctypes.c_int32),
        ('maximum', ctypes.c_int32),
        ('fuzz', ctypes.c_int32),
        ('flat', ctypes.c_int32),
        ('resolution', ctypes.c_int32),
    ]

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


EVDEV_MAGIC = ord(b'E')

_S_BUFF = 512

EVIOCGVERSION = _IOR(EVDEV_MAGIC, 0x01, ctypes.sizeof(ctypes.c_int))
EVIOCGID = _IOR(EVDEV_MAGIC, 0x02, ctypes.sizeof(input_id))
EVIOCGNAME = _IOR(EVDEV_MAGIC, 0x06, _S_BUFF)
EVIOCGPHYS = _IOR(EVDEV_MAGIC, 0x07, _S_BUFF)
EVIOCGUNIQ = _IOR(EVDEV_MAGIC, 0x08, _S_BUFF)
#EVIOCGPROP = _IOR(EVDEV_MAGIC, 0x09, )
EVIOCGKEY = _IOR(EVDEV_MAGIC, 0x18, (enums.Key.KEY_MAX.value+7)//8)
EVIOCGLED = _IOR(EVDEV_MAGIC, 0x19, (enums.Led.LED_MAX.value+7)//8)
EVIOCGSND = _IOR(EVDEV_MAGIC, 0x1a, (enums.Sound.SND_MAX.value+7)//8)
EVIOCGSW = _IOR(EVDEV_MAGIC, 0x1b, (enums.Switch.SW_MAX.value+7)//8)


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


def _test_bit(mask, bit):
    return ord(mask[bit//8]) & (1 << (bit % 8))


def keys(fd):
    max = enums.Key.KEY_MAX.value
    result = ctypes.create_string_buffer((max+7)//8)
    fcntl.ioctl(fd, EVIOCGKEY, result)
    return [bit for bit in range(max) if _test_bit(result, bit)]


def leds(fd):
    max = enums.Led.LED_MAX.value
    result = ctypes.create_string_buffer((max+7)//8)
    fcntl.ioctl(fd, EVIOCGLED, result)
    return [bit for bit in range(max) if _test_bit(result, bit)]


def sounds(fd):
    max = enums.Sound.SND_MAX.value
    result = ctypes.create_string_buffer((max+7)//8)
    fcntl.ioctl(fd, EVIOCGSND, result)
    return [bit for bit in range(max) if _test_bit(result, bit)]


def switches(fd):
    max = enums.Switch.SW_MAX.value
    result = ctypes.create_string_buffer((max+7)//8)
    fcntl.ioctl(fd, EVIOCGSW, result)
    return [bit for bit in range(max) if _test_bit(result, bit)]


if __name__ == '__main__':
    import os
    import sys
    fd = os.open(sys.argv[1], os.O_RDWR | os.O_NONBLOCK)
    print('version:', version(fd))
    print('ID: bus={0.bustype} vendor={0.vendor} product={0.product} version={0.version}'
          .format(device_id(fd)))
    print('name:', name(fd))
    print('physical_location:', physical_location(fd))
    print('UID:', uid(fd))
    print('key state:', keys(fd))
