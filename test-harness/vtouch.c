// Virtual touchscreen (MT protocol B) for testing touch scroll behaviour.
// usage: vtouch x1 y1 x2 y2 [steps] [step_ms] [hold_ms_before_release]
#define _GNU_SOURCE
#include <fcntl.h>
#include <linux/uinput.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <unistd.h>

#define W 1920
#define H 1200

static int fd;

static void emit(int type, int code, int val) {
    struct input_event ev = {0};
    ev.type = type;
    ev.code = code;
    ev.value = val;
    if (write(fd, &ev, sizeof ev) != sizeof ev) perror("write");
}

static void msleep(long ms) {
    struct timespec ts = {ms / 1000, (ms % 1000) * 1000000L};
    nanosleep(&ts, NULL);
}

static void abs_setup(int code, int min, int max) {
    struct uinput_abs_setup s = {0};
    s.code = code;
    s.absinfo.minimum = min;
    s.absinfo.maximum = max;
    if (ioctl(fd, UI_ABS_SETUP, &s) < 0) perror("UI_ABS_SETUP");
}

int main(int argc, char **argv) {
    if (argc < 5) { fprintf(stderr, "usage: %s x1 y1 x2 y2 [steps] [step_ms] [hold_ms]\n", argv[0]); return 2; }
    int x1 = atoi(argv[1]), y1 = atoi(argv[2]), x2 = atoi(argv[3]), y2 = atoi(argv[4]);
    int steps = argc > 5 ? atoi(argv[5]) : 20;
    int step_ms = argc > 6 ? atoi(argv[6]) : 10;
    int hold_ms = argc > 7 ? atoi(argv[7]) : 0;

    fd = open("/dev/uinput", O_WRONLY | O_NONBLOCK);
    if (fd < 0) { perror("open /dev/uinput"); return 1; }

    ioctl(fd, UI_SET_EVBIT, EV_SYN);
    ioctl(fd, UI_SET_EVBIT, EV_KEY);
    ioctl(fd, UI_SET_EVBIT, EV_ABS);
    ioctl(fd, UI_SET_KEYBIT, BTN_TOUCH);
    ioctl(fd, UI_SET_PROPBIT, INPUT_PROP_DIRECT);

    abs_setup(ABS_X, 0, W - 1);
    abs_setup(ABS_Y, 0, H - 1);
    abs_setup(ABS_MT_SLOT, 0, 9);
    abs_setup(ABS_MT_TRACKING_ID, 0, 65535);
    abs_setup(ABS_MT_POSITION_X, 0, W - 1);
    abs_setup(ABS_MT_POSITION_Y, 0, H - 1);

    struct uinput_setup us = {0};
    us.id.bustype = BUS_VIRTUAL;
    us.id.vendor = 0x1234;
    us.id.product = 0x5678;
    strcpy(us.name, "vtouch test touchscreen");
    if (ioctl(fd, UI_DEV_SETUP, &us) < 0) { perror("UI_DEV_SETUP"); return 1; }
    if (ioctl(fd, UI_DEV_CREATE) < 0) { perror("UI_DEV_CREATE"); return 1; }

    int repeats = argc > 8 ? atoi(argv[8]) : 1;

    msleep(3500);  // let libinput/mutter pick the device up

  for (int r = 0; r < repeats; r++) {
    fprintf(stderr, "[vtouch] swipe %d\n", r + 1);
    emit(EV_ABS, ABS_MT_SLOT, 0);
    emit(EV_ABS, ABS_MT_TRACKING_ID, 1);
    emit(EV_ABS, ABS_MT_POSITION_X, x1);
    emit(EV_ABS, ABS_MT_POSITION_Y, y1);
    emit(EV_KEY, BTN_TOUCH, 1);
    emit(EV_ABS, ABS_X, x1);
    emit(EV_ABS, ABS_Y, y1);
    emit(EV_SYN, SYN_REPORT, 0);
    msleep(step_ms);

    for (int i = 1; i <= steps; i++) {
        int x = x1 + (x2 - x1) * i / steps;
        int y = y1 + (y2 - y1) * i / steps;
        emit(EV_ABS, ABS_MT_SLOT, 0);
        emit(EV_ABS, ABS_MT_POSITION_X, x);
        emit(EV_ABS, ABS_MT_POSITION_Y, y);
        emit(EV_ABS, ABS_X, x);
        emit(EV_ABS, ABS_Y, y);
        emit(EV_SYN, SYN_REPORT, 0);
        msleep(step_ms);
    }

    if (hold_ms) msleep(hold_ms);

    emit(EV_ABS, ABS_MT_SLOT, 0);
    emit(EV_ABS, ABS_MT_TRACKING_ID, -1);
    emit(EV_KEY, BTN_TOUCH, 0);
    emit(EV_SYN, SYN_REPORT, 0);
    msleep(1500);
  }

    msleep(400);
    ioctl(fd, UI_DEV_DESTROY);
    close(fd);
    return 0;
}
