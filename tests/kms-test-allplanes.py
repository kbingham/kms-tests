#!/usr/bin/python3

import kmstest
import pykms

class AllPlanesTest(kmstest.KMSTest):
    """Test composition with all planes enabled on all CRTCs."""

    def handle_page_flip(self, frame, time):
        self.logger.log("Page flip complete")

    def main(self):
        # Create the connectors to CRTCs map
        connectors = {}
        for connector in self.card.connectors:
            # Skip disconnected connectors
            if not connector.connected():
                continue

            # Add the connector to the map
            for crtc in connector.get_possible_crtcs():
                if crtc not in connectors:
                    connectors[crtc] = connector

        for crtc in self.card.crtcs:
            self.start("composition on CRTC %u" % crtc.id)

            # Get the connector and default mode
            try:
                connector = connectors[crtc];
                mode = connector.get_default_mode()
            except KeyError:
                self.skip("no connector or mode available")
                continue

            # List planes available for the CRTC
            planes = []
            for plane in self.card.planes:
                if plane.supports_crtc(crtc) and plane != crtc.primary_plane:
                    planes.append(plane)

            if len(planes) == 0:
                self.skip("no plane available for CRTC")
                continue

            self.logger.log("Testing connector %s, CRTC %u, mode %s with %u planes" % \
                  (connector.fullname, crtc.id, mode.name, len(planes)))

            # Create a frame buffer
            fb = pykms.DumbFramebuffer(self.card, mode.hdisplay, mode.vdisplay, "XR24")
            pykms.draw_test_pattern(fb)

            # Set the mode with a primary plane
            ret = self.atomic_crtc_mode_set(crtc, connector, mode, fb)
            if ret < 0:
                self.fail("atomic mode set failed with %d" % ret)
                continue

            self.run(3)

            # Add all other planes one by one
            offset = 100
            for plane in planes:
                source = kmstest.Rect(0, 0, fb.width, fb.height)
                destination = kmstest.Rect(offset, offset, fb.width, fb.height)
                ret = self.atomic_plane_set(plane, crtc, source, destination, fb)
                if ret < 0:
                    self.fail("atomic plane set failed with %d" % ret)
                    break

                self.logger.log("Adding plane %u" % plane.id)
                self.run(1)

                if self.flips == 0:
                    self.fail("No page flip registered")
                    break

                offset += 50

            else:
                self.success()

AllPlanesTest().execute()
