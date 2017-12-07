#!/usr/bin/python3

import kmstest
import pykms
import selectors

from rcar_vin import RCar_VIN_G3

class VINLoopbackTest(kmstest.KMSTest):
    """ Output a test image on a specific HDMI connector and capture using an HDMI
        cable looped back to the VIN HDMI input device. """

    def handle_page_flip(self, frame, time):
        if self.flips == 1:
            self.logger.log("first page flip frame %u time %f" % (frame, time))
            self.frame_start = frame
            self.time_start = time

        if self.stop_requested:
            self.logger.log("last page flip frame %u time %f" % (frame, time))
            self.frame_end = frame
            self.time_end = time
            self.loop.stop()
            self.stop_requested = False
            return

        # Flip between two constant (identical) pre-created buffers
        fb = self.fbs[self.front_buf]
        self.front_buf = self.front_buf ^ 1

        source = kmstest.Rect(0, 0, fb.width, fb.height)
        destination = kmstest.Rect(0, 0, fb.width, fb.height)
        self.atomic_plane_set(self.plane, self.crtc, source, destination, fb)

    def stop_page_flip(self):
        self.stop_requested = True
        self.cap.stream_off()

    def configure_vin(self, mode):
        vin = RCar_VIN_G3().vin_v4l2_device(0)
        self.logger.log("Using VIN : " + vin)

        # Capture frames using VIN
        self.vid = pykms.VideoDevice(vin)
        self.cap = self.vid.capture_streamer
        self.cap.set_port(0)
        self.cap.set_format(self.pixfmt, mode.hdisplay, mode.vdisplay)
        self.cap.set_queue_size(len(self.vin))
        self.captured = 0
        self.failures = 0

        for fb in self.vin:
            self.cap.queue(fb)

        self.cap.stream_on()

        self.loop.register(self.cap.fd, selectors.EVENT_READ, self.handle_frame_capture)


    def handle_frame_capture(self, fileobj, events):
        if self.stop_requested:
            return

        fb = self.cap.dequeue()
        diff = pykms.compare_framebuffers(fb, self.fbs[self.front_buf])

        self.logger.log("Frame Capture: " + str(self.captured) + " with difference " + str(diff))

        if diff:
            filename = "/tmp/captured{}.{}x{}.raw".format(str(self.captured), str(self.mode.hdisplay), str(self.mode.vdisplay))
            pykms.save_raw_frame(fb, filename)
            self.logger.log("Corrupt frame written to " + filename)
            self.failures += 1

        self.cap.queue(fb)
        self.captured += 1

        # Stop capturing after 10 frames
        if self.captured >= 10:
            self.stop_page_flip()


    def get_connector(self, name):
        for connector in self.card.connectors:
            # Skip unless we are HDMI-A-1
            if connector.fullname == "HDMI-A-1":
                return connector

    def main(self):
        connector_name = "HDMI-A-1"

        self.start("VIN Loopback on connector %s" % connector_name)

        connector = self.get_connector(connector_name)
        if connector is None:
            self.skip("HDMI output connector not found")
            return

        # Skip disconnected connectors
        if not connector.connected():
            self.skip("unconnected connector")
            return

        # Find a CRTC suitable for the connector
        crtc = connector.get_current_crtc()
        if not crtc:
            crtcs = connector.get_possible_crtcs()
            if len(crtcs) == 0:
                self.skip("No CRTC available")
                return

            crtc = crtcs[0]

        self.crtc = crtc

        # Find a plane suitable for the CRTC
        for plane in self.card.planes:
            if plane.supports_crtc(crtc):
                self.plane = plane
                break
        else:
            self.skip("no plane available for CRTC %u" % crtc.id)
            return

        # Get the default mode for the connector
        try:
            mode = connector.get_default_mode()
        except ValueError:
            self.skip("no mode available")
            return

        self.mode = mode

        self.logger.log("Testing connector %s, CRTC %u, plane %u, mode %s" % \
              (connector.fullname, crtc.id, self.plane.id, mode.name))

        # Create two frame buffers each for output and capture
        self.fbs = []
        self.vin = []
        self.pixfmt = pykms.PixelFormat.XRGB8888

        for i in range(2):
            self.fbs.append(pykms.DumbFramebuffer(self.card, mode.hdisplay, mode.vdisplay, self.pixfmt))
            self.vin.append(pykms.DumbFramebuffer(self.card, mode.hdisplay, mode.vdisplay, self.pixfmt))

        # Draw test patterns on the output frame buffers
        # We don't (yet) support comparing against changing patterns
        pykms.draw_test_pattern(self.fbs[0])
        pykms.draw_test_pattern(self.fbs[1])

        # Set the mode and perform the initial page flip
        ret = self.atomic_crtc_mode_set(crtc, connector, mode, self.fbs[0])
        if ret < 0:
            self.fail("atomic mode set failed with %d" % ret)
            return

        # Configure

        # Flip pages for 10s
        self.front_buf = 0
        self.frame_start = 0
        self.frame_end = 0
        self.time_start = 0
        self.time_end = 0
        self.stop_requested = False

        # Allow the output to settle before capturing
        # VIN currently does not support dynamic input change
        self.run(1)

        self.configure_vin(mode)

        # Set timeout at 5 seconds.
        # We stop after capturing 10 frames
        self.loop.add_timer(5, self.stop_page_flip)
        self.run(6)

        if not self.captured:
            self.fail("No frames captured")
            return

        if self.failures:
            self.fail("Frame comparisons failed")
            self.logger.log("Saving output image as /tmp/original.bin")
            pykms.save_raw_frame(self.fbs[0], "/tmp/original.bin")
            return

        if not self.flips:
            self.fail("No page flip registered")
            return

        if self.stop_requested:
            self.fail("Last page flip not registered")
            return

        self.success()

VINLoopbackTest().execute()
