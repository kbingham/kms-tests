#!/usr/bin/python3

import kmstest
import pykms

class PageFlipTest(kmstest.KMSTest):
    """Test page flipping on all connectors in sequence with the default mode."""

    BAR_WIDTH = 20
    BAR_SPEED = 8

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

        fb = self.fbs[self.front_buf]
        self.front_buf = self.front_buf ^ 1

        old_xpos = (self.bar_xpos - self.BAR_SPEED) % (fb.width - self.BAR_WIDTH);
        new_xpos = (self.bar_xpos + self.BAR_SPEED) % (fb.width - self.BAR_WIDTH);
        self.bar_xpos = new_xpos

        pykms.draw_color_bar(fb, old_xpos, new_xpos, self.BAR_WIDTH)

        source = kmstest.Rect(0, 0, fb.width, fb.height)
        destination = kmstest.Rect(0, 0, fb.width, fb.height)
        self.atomic_plane_set(self.plane, self.crtc, source, destination, fb)

    def stop_page_flip(self):
        self.stop_requested = True

    def main(self):
        for connector in self.card.connectors:
            self.start("page flip on connector %s" % connector.fullname)

            # Skip disconnected connectors
            if not connector.connected():
                self.skip("unconnected connector")
                continue

            # Find a CRTC suitable for the connector
            crtc = connector.get_current_crtc()
            if not crtc:
                crtcs = connector.get_possible_crtcs()
                if len(crtcs) == 0:
                    pass

                crtc = crtcs[0]

            self.crtc = crtc

            # Find a plane suitable for the CRTC
            for plane in self.card.planes:
                if plane.supports_crtc(crtc):
                    self.plane = plane
                    break
            else:
                self.skip("no plane available for CRTC %u" % crtc.id)
                continue

            # Get the default mode for the connector
            try:
                mode = connector.get_default_mode()
            except ValueError:
                self.skip("no mode available")
                continue

            self.logger.log("Testing connector %s, CRTC %u, plane %u, mode %s" % \
                  (connector.fullname, crtc.id, self.plane.id, mode.name))

            # Create two frame buffers
            self.fbs = []
            for i in range(2):
                self.fbs.append(pykms.DumbFramebuffer(self.card, mode.hdisplay, mode.vdisplay, "XR24"))

            # Set the mode and perform the initial page flip
            ret = self.atomic_crtc_mode_set(crtc, connector, mode, self.fbs[0])
            if ret < 0:
                self.fail("atomic mode set failed with %d" % ret)
                continue

            # Flip pages for 10s
            self.bar_xpos = 0
            self.front_buf = 0
            self.frame_start = 0
            self.frame_end = 0
            self.time_start = 0
            self.time_end = 0
            self.stop_requested = False

            self.loop.add_timer(10, self.stop_page_flip)
            self.run(11)

            if not self.flips:
                self.fail("No page flip registered")
                continue

            if self.stop_requested:
                self.fail("Last page flip not registered")
                continue

            frames = self.frame_end - self.frame_start + 1
            interval = self.time_end - self.time_start
            self.logger.log("Frame rate: %f (%u/%u frames in %f s)" % \
                (frames / interval, self.flips, frames, interval))
            self.success()

PageFlipTest().execute()
