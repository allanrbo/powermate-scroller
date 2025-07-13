#!/usr/bin/env python3
import os, fcntl, struct, time

SCROLL_MULTIPLIER = 2      # 1 = default speed, 2-4 feel natural, >6 can jump

SRC_DEV = "/dev/input/by-id/usb-Griffin_Technology__Inc._Griffin_PowerMate-event-if00"
UINPUT  = "/dev/uinput"

EV_SYN, EV_KEY, EV_REL = 0x00, 0x01, 0x02
SYN_REPORT, REL_DIAL, REL_WHEEL = 0, 0x07, 0x08
BTN_0, BTN_LEFT = 0x100, 0x110
UI_SET_EVBIT, UI_SET_KEYBIT, UI_SET_RELBIT = 0x40045564, 0x40045565, 0x40045566
UI_DEV_CREATE, UI_DEV_DESTROY = 0x5501, 0x5502

def emit(fd, etype, code, value):
    t = time.time()
    sec, usec = int(t), int((t - int(t)) * 1000000)
    os.write(fd, struct.pack("llHHi", sec, usec, etype, code, value))

def make_uinput():
    fd = os.open(UINPUT, os.O_WRONLY | os.O_NONBLOCK)
    fcntl.ioctl(fd, UI_SET_EVBIT, EV_REL)
    fcntl.ioctl(fd, UI_SET_RELBIT, REL_WHEEL)
    fcntl.ioctl(fd, UI_SET_EVBIT, EV_KEY)
    fcntl.ioctl(fd, UI_SET_KEYBIT, BTN_LEFT)
    name = b"PowerMate-Scroller"
    header = struct.pack(
        "80sHHHHi", name.ljust(80, b"\0"), 3, 0x077d, 0x0410, 1, 0
    )
    os.write(fd, header + bytes(4 * 64 * 4))
    fcntl.ioctl(fd, UI_DEV_CREATE)
    return fd

def main():
    src = os.open(SRC_DEV, os.O_RDONLY)
    ui  = make_uinput()
    fmt = "llHHi"
    sz  = struct.calcsize(fmt)
    try:
        while True:
            data = os.read(src, sz)
            if len(data) < sz:
                continue
            sec, usec, etype, code, value = struct.unpack(fmt, data)
            if etype == EV_REL and code == REL_DIAL and value:
                emit(ui, EV_REL, REL_WHEEL, -value*SCROLL_MULTIPLIER)
                emit(ui, EV_SYN, SYN_REPORT, 0)
            elif etype == EV_KEY and code == BTN_0:
                emit(ui, EV_KEY, BTN_LEFT, value*SCROLL_MULTIPLIER)
                emit(ui, EV_SYN, SYN_REPORT, 0)
    finally:
        fcntl.ioctl(ui, UI_DEV_DESTROY)
        os.close(ui)
        os.close(src)

if __name__ == "__main__":
    main()
