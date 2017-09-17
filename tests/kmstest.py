#!/usr/bin/python3

import errno
import fcntl
import os
import pykms
import selectors
import sys
import time


class Timer(object):
    def __init__(self, timeout, callback):
        self.timeout = time.clock_gettime(time.CLOCK_MONOTONIC) + timeout
        self.callback = callback


class EventLoop(selectors.DefaultSelector):
    def __init__(self):
        super().__init__()
        self.__timers = []

    def add_timer(self, timeout, callback):
        self.__timers.append(Timer(timeout, callback))
        self.__timers.sort(key=lambda timer: timer.timeout)

    def fire_timers(self):
        clk = time.clock_gettime(time.CLOCK_MONOTONIC)
        while len(self.__timers) > 0:
            timer = self.__timers[0]
            if timer.timeout > clk:
                break

            del self.__timers[0]
            timer.callback()

    def next_timeout(self):
        clk = time.clock_gettime(time.CLOCK_MONOTONIC)
        if len(self.__timers) == 0 or self.__timers[0].timeout < clk:
            return None

        return self.__timers[0].timeout - clk

    def run(self, duration=0):
        if duration:
            self.add_timer(duration, self.stop)

        timeout = self.next_timeout()

        self._stop = False
        while not self._stop:
            for key, events in self.select(timeout):
                key.data(key.fileobj, events)
            self.fire_timers()

        self.__timers = []

    def stop(self):
        self._stop = True


class KernelLogMessage(object):
    def __init__(self, msg):
        pos = msg.find(";")
        header = msg[:pos]
        msg = msg[pos+1:]

        facility, sequence, timestamp, *other = header.split(",")
        self.facility = int(facility)
        self.sequence = int(sequence)
        self.timestamp = int(timestamp) / 1000000.

        msg = msg.split("\n")
        self.msg = msg[0]
        self.tags = {}

        try:
            tags = msg[1:-1]
            for tag in tags:
                tag = tag.strip().split("=")
                self.tags[tag[0]] = tag[1]
        except:
            pass


class KernelLogReader(object):
    def __init__(self):
        self.kmsg = os.open("/dev/kmsg", 0)
        flags = fcntl.fcntl(self.kmsg, fcntl.F_GETFL)
        fcntl.fcntl(self.kmsg, fcntl.F_SETFL, flags | os.O_NONBLOCK)
        os.lseek(self.kmsg, 0, os.SEEK_END)

    def __del__(self):
        os.close(self.kmsg)

    def read(self):
        msgs = []
        while True:
            try:
                msg = os.read(self.kmsg, 8191)
                msg = msg.decode("utf-8")
            except OSError as e:
                if e.errno == errno.EAGAIN:
                    break
                else:
                    raise e
            msgs.append(KernelLogMessage(msg))

        return msgs


def KernelLogValidator(test_function):
    kernel_fault_strings = ("Kernel panic", "Oops", "WARNING:")

    def kernel_log_validator(self):
        klog = KernelLogReader()
        fault = False

        test_function(self)

        kmsgs = klog.read()
        for msg in kmsgs:
            if any(s in msg.msg for s in kernel_fault_strings):
                fault = True

        if fault:
            self.fail("Post Test Kernel Fault Found")

    return kernel_log_validator


class Logger(object):
    def __init__(self, name):
        self.logfile = open("%s.log" % name, "w")
        self._kmsg = KernelLogReader()

    def __del__(self):
        self.close()

    def close(self):
        if self.logfile:
            self.logfile.close()
            self.logfile = None

    def event(self):
        kmsgs = self._kmsg.read()
        for msg in kmsgs:
            self.logfile.write("K [%6f] %s\n" % (msg.timestamp, msg.msg))
        self.logfile.flush()

    @property
    def fd(self):
        return self._kmsg.kmsg

    def flush(self):
        self.logfile.flush()
        os.fsync(self.logfile)

    def log(self, msg):
        # Start by processing the kernel log as there might not be any event
        # loop running.
        self.event()

        now = time.clock_gettime(time.CLOCK_MONOTONIC)
        self.logfile.write("U [%6f] %s\n" % (now, msg))
        self.logfile.flush()


class Rect(object):
    def __init__(self, left, top, width, height):
        self.left = left
        self.top = top
        self.width = width
        self.height = height


class KMSTest(object):
    def __init__(self, use_default_key_handler=False):
        if not getattr(self, 'main', None):
            raise RuntimeError('Test class must implement main method')

        self.card = pykms.Card()
        if not self.card.has_atomic:
            raise RuntimeError("Device doesn't support the atomic API")

        logname = self.__class__.__name__
        self.logger = Logger(logname)

        self.loop = EventLoop()
        self.loop.register(self.logger.fd, selectors.EVENT_READ, self.__read_logger)
        self.loop.register(self.card.fd, selectors.EVENT_READ, self.__read_event)
        if use_default_key_handler:
            self.loop.register(sys.stdin, selectors.EVENT_READ, self.__read_key)

    def __del__(self):
        self.logger.close()

    def __format_props(self, props):
        return {k: v & ((1 << 64) - 1) for k, v in props.items()}

    def atomic_crtc_disable(self, crtc, sync=True):
        req = pykms.AtomicReq(self.card)
        req.add(crtc, 'ACTIVE', False)
        if sync:
            return req.commit_sync(True)
        else:
            return req.commit(self, True)

    def atomic_crtc_mode_set(self, crtc, connector, mode, fb=None, sync=False):
        """Perform a mode set on the given connector and CRTC. The framebuffer,
        if present, will be output on the primary plane. Otherwise no plane is
        configured for the CRTC."""

        # Mode blobs are reference-counted, make sure the blob stays valid until
        # the commit completes.
        mode_blob = mode.to_blob(self.card)

        req = pykms.AtomicReq(self.card)
        req.add(connector, 'CRTC_ID', crtc.id)
        req.add(crtc, {'ACTIVE': 1, 'MODE_ID': mode_blob.id})
        if fb:
            req.add(crtc.primary_plane, {
                        'FB_ID': fb.id,
                        'CRTC_ID': crtc.id,
                        'SRC_X': 0,
                        'SRC_Y': 0,
                        'SRC_W': int(fb.width * 65536),
                        'SRC_H': int(fb.height * 65536),
                        'CRTC_X': 0,
                        'CRTC_Y': 0,
                        'CRTC_W': fb.width,
                        'CRTC_H': fb.height,
            })
        if sync:
            return req.commit_sync(True)
        else:
            return req.commit(self, True)

    def atomic_plane_set(self, plane, crtc, source, destination, fb, sync=False):
        req = pykms.AtomicReq(self.card)
        req.add(plane, self.__format_props({
                    'FB_ID': fb.id,
                    'CRTC_ID': crtc.id,
                    'SRC_X': int(source.left * 65536),
                    'SRC_Y': int(source.top * 65536),
                    'SRC_W': int(source.width * 65536),
                    'SRC_H': int(source.height * 65536),
                    'CRTC_X': destination.left,
                    'CRTC_Y': destination.top,
                    'CRTC_W': destination.width,
                    'CRTC_H': destination.height,
        }))
        if sync:
            return req.commit_sync()
        else:
            return req.commit(self)

    def atomic_planes_disable(self, sync=True):
        req = pykms.AtomicReq(self.card)
        for plane in self.card.planes:
            req.add(plane, {"FB_ID": 0, 'CRTC_ID': 0})

        if sync:
            return req.commit_sync()
        else:
            return req.commit(self)

    def __handle_page_flip(self, frame, time):
        self.flips += 1
        try:
            # The handle_page_flip() method is optional, ignore attribute errors
            self.handle_page_flip(frame, time)
        except AttributeError:
            pass

    def __read_event(self, fileobj, events):
        for event in self.card.read_events():
            if event.type == pykms.DrmEventType.FLIP_COMPLETE:
                self.__handle_page_flip(event.seq, event.time)

    def __read_logger(self, fileobj, events):
        self.logger.event()

    def __read_key(self, fileobj, events):
        sys.stdin.readline()
        self.loop.stop()

    @KernelLogValidator
    def execute(self):
        """Execute the test by running the main function."""
        self.main()

    def flush_events(self):
        """Discard all pending DRM events."""

        # Temporarily switch to non-blocking I/O to read events, as there might
        # be no event pending.
        flags = fcntl.fcntl(self.card.fd, fcntl.F_GETFL)
        fcntl.fcntl(self.card.fd, fcntl.F_SETFL, flags | os.O_NONBLOCK)

        # read_events() is a generator so we have to go through all events
        # explicitly. Ignore -EAGAIN errors, they're expected in non-blocking
        # I/O mode.
        try:
            for event in self.card.read_events():
                pass
        except OSError as e:
            if e.errno != errno.EAGAIN:
                raise e

        fcntl.fcntl(self.card.fd, fcntl.F_SETFL, flags)

    def run(self, duration):
        """Run the event loop for the given duration (in seconds)."""
        self.flips = 0
        self.loop.run(duration)

    def start(self, name):
        """Start a test."""
        self.test_name = name
        self.logger.log("Testing %s" % name)
        sys.stdout.write("Testing %s: " % name)
        sys.stdout.flush()

    def progress(self, current, maximum):
        sys.stdout.write("\rTesting %s: %u/%u" % (self.test_name, current, maximum))
        sys.stdout.flush()

    def fail(self, reason):
        """Complete a test with failure."""
        self.logger.log("Test failed. Reason: %s" % reason)
        self.logger.flush()
        sys.stdout.write("\rTesting %s: FAIL\n" % self.test_name)
        sys.stdout.flush()
        return self.fail

    def skip(self, reason):
        """Complete a test with skip."""
        self.logger.log("Test skipped. Reason: %s" % reason)
        self.logger.flush()
        sys.stdout.write("SKIP\n")
        sys.stdout.flush()
        return self.skip

    def success(self):
        """Complete a test with success."""
        self.logger.log("Test completed successfully")
        self.logger.flush()
        sys.stdout.write("\rTesting %s: SUCCESS\n" % self.test_name)
        sys.stdout.flush()
        return self.success
