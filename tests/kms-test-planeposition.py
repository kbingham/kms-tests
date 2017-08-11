#!/usr/bin/python3

import kmstest
import pykms
import time

class PlanePositionTest(kmstest.KMSTest):
    """Test boundaries of plane positioning."""

    def main(self):
        self.start("plane positioning boundaries")

        # Find a CRTC with a connected connector and at least two planes
        for connector in self.card.connectors:
            if not connector.connected():
                self.skip("unconnected connector")
                continue

            try:
                mode = connector.get_default_mode()
            except ValueError:
                continue

            crtcs = connector.get_possible_crtcs()
            for crtc in crtcs:
                planes = []
                for plane in self.card.planes:
                    if plane.supports_crtc(crtc):
                        planes.append(plane)

                if len(planes) > 1:
                    break
            else:
                crtc = None

            if crtc:
                break

        else:
            self.skip("no CRTC available with connector and at least two planes")
            return

        self.logger.log("Testing connector %s, CRTC %u, mode %s with %u planes" % \
              (connector.fullname, crtc.id, mode.name, len(planes)))

        # Create a frame buffer
        fb = pykms.DumbFramebuffer(self.card, mode.hdisplay, mode.vdisplay, "XR24")
        pykms.draw_test_pattern(fb)

        # Set the mode with no plane, wait 5s for the monitor to wake up
        ret = self.atomic_crtc_mode_set(crtc, connector, mode, sync=True)
        if ret < 0:
            self.fail("atomic mode set failed with %d" % ret)
            return

        self.logger.log("Initial atomic mode set completed")
        time.sleep(5)

        # Add the first plane to cover half of the CRTC
        source = kmstest.Rect(0, 0, fb.width // 2, fb.height)
        destination = kmstest.Rect(0, 0, fb.width // 2, fb.height)
        ret = self.atomic_plane_set(planes[0], crtc, source, destination, fb, sync=True)
        if ret < 0:
            self.fail("atomic plane set for first plane failed with %d" % ret)
            return

        self.logger.log("Root plane enabled")
        time.sleep(3)

        # Add the second plane and move it around to cross all CRTC boundaries
        offsets = ((50, 50), (150, 50), (50, 150), (-50, 50), (50, -50))
        for offset in offsets:
            width = fb.width - 100
            height = fb.height - 100
            source = kmstest.Rect(0, 0, width, height)
            destination = kmstest.Rect(offset[0], offset[1], width, height)

            ret = self.atomic_plane_set(planes[1], crtc, source, destination, fb, sync=True)
            if ret < 0:
                self.fail("atomic plane set with offset %d,%d" % offset)
                return

            self.logger.log("Moved overlay plane to %d,%d" % offset)
            time.sleep(3)

        # Try to move the plane completely off-screen. The device is expected to
        # reject this.
        offsets = ((mode.hdisplay, 50), (50, mode.vdisplay),
                   (-mode.hdisplay, 50), (50, -mode.vdisplay))
        for offset in offsets:
            width = fb.width - 100
            height = fb.height - 100
            source = kmstest.Rect(0, 0, width, height)
            destination = kmstest.Rect(offset[0], offset[1], width, height)

            ret = self.atomic_plane_set(planes[1], crtc, source, destination, fb, sync=True)
            if ret >= 0:
                self.fail("atomic plane set with invalid offset %d,%d accepted" % offset)
                return

            self.logger.log("Failed to Move overlay plane to %d,%d as expected" % offset)

        self.success()

PlanePositionTest().execute()
