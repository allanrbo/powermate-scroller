#!/usr/bin/env python3
import os, fcntl, struct, time, errno

SCROLL_MULTIPLIER = 2      # 1 = default speed, 2-4 feel natural, >6 can jump

SRC_DEV = "/dev/input/by-id/usb-Griffin_Technology__Inc._Griffin_PowerMate-event-if00"
UINPUT  = "/dev/uinput"

EV_SYN, EV_KEY, EV_REL, EV_MSC = 0x00, 0x01, 0x02, 0x04
SYN_REPORT, REL_DIAL, REL_WHEEL = 0, 0x07, 0x08
MSC_PULSELED = 0x01
BTN_0, BTN_LEFT = 0x100, 0x110
UI_SET_EVBIT, UI_SET_KEYBIT, UI_SET_RELBIT = 0x40045564, 0x40045565, 0x40045566
UI_DEV_CREATE, UI_DEV_DESTROY = 0x5501, 0x5502
EVENT_FMT = "llHHi"
EVENT_SIZE = struct.calcsize(EVENT_FMT)

def emit(fd, etype, code, value):
    t = time.time()
    sec, usec = int(t), int((t - int(t)) * 1000000)
    os.write(fd, struct.pack(EVENT_FMT, sec, usec, etype, code, value))

def set_led(fd, brightness):
    emit(fd, EV_MSC, MSC_PULSELED, brightness)
    emit(fd, EV_SYN, SYN_REPORT, 0)

def make_uinput():
    fd = os.open(UINPUT, os.O_WRONLY | os.O_NONBLOCK)
    fcntl.ioctl(fd, UI_SET_EVBIT, EV_REL)
    fcntl.ioctl(fd, UI_SET_RELBIT, REL_WHEEL)
    fcntl.ioctl(fd, UI_SET_EVBIT, EV_KEY)
    fcntl.ioctl(fd, UI_SET_KEYBIT, BTN_LEFT)
    header = struct.pack(
        "80sHHHHi", b"PowerMate-Scroller".ljust(80, b"\0"), 3, 0x077d, 0x0410, 1, 0
    )
    os.write(fd, header + bytes(4 * 64 * 4))
    fcntl.ioctl(fd, UI_DEV_CREATE)
    return fd

def run_loop(src_fd, ui_fd):
    while True:
        try:
            data = os.read(src_fd, EVENT_SIZE)
        except OSError as e:
            if e.errno in (errno.ENODEV, errno.EIO, errno.ENOENT):
                break   # device vanished – reopen in outer loop
            raise
        if len(data) != EVENT_SIZE:
            continue
        _, _, etype, code, val = struct.unpack(EVENT_FMT, data)
        if etype == EV_REL and code == REL_DIAL and val:
            emit(ui_fd, EV_REL, REL_WHEEL, -val * SCROLL_MULTIPLIER)
            emit(ui_fd, EV_SYN, SYN_REPORT, 0)
        elif etype == EV_KEY and code == BTN_0:
            emit(ui_fd, EV_KEY, BTN_LEFT, val)
            emit(ui_fd, EV_SYN, SYN_REPORT, 0)

def main():
    ui_fd = make_uinput()
    try:
        while True:
            try:
                src_fd = os.open(SRC_DEV, os.O_RDWR)
            except FileNotFoundError:
                time.sleep(3)
                continue
            try:
                set_led(src_fd, 0)
                run_loop(src_fd, ui_fd)
            finally:
                os.close(src_fd)
            time.sleep(3)  # brief pause before retrying after unplug
    finally:
        fcntl.ioctl(ui_fd, UI_DEV_DESTROY)
        os.close(ui_fd)

if __name__ == "__main__":
    main()
