#!/usr/bin/python3

import kmstest
import pykms

class ModeSetTest(kmstest.KMSTest):
    """Test mode setting on all connectors in sequence with the default mode."""

    def handle_page_flip(self, frame, time):
        self.logger.log("Page flip complete")

    def main(self):
        for connector in self.card.connectors:
            self.start("atomic mode set on connector %s" % connector.fullname)

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

            # Get the default mode for the connector
            try:
                mode = connector.get_default_mode()
            except ValueError:
                self.skip("no mode available")
                continue

            self.logger.log("Testing connector %s on CRTC %u with mode %s" % \
                  (connector.fullname, crtc.id, mode.name))

            # Create a frame buffer
            fb = pykms.DumbFramebuffer(self.card, mode.hdisplay, mode.vdisplay, "XR24")
            pykms.draw_test_pattern(fb)

            # Perform a mode set
            ret = self.atomic_crtc_mode_set(crtc, connector, mode, fb)
            if ret < 0:
                self.fail("atomic mode set failed with %d" % ret)
                continue

            self.logger.log("Atomic mode set complete")
            self.run(5)

            if self.flips == 0:
                self.fail("Page flip not registered")
            else:
                self.success()

ModeSetTest().execute()
