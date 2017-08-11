#!/usr/bin/python3

import kmstest
import pykms

class ModesTest(kmstest.KMSTest):
    """Test all available modes on all available connectors."""

    def handle_page_flip(self, frame, time):
        self.logger.log("Page flip complete")

    def test_mode(self, connector, crtc, mode):
        self.logger.log("Testing connector %s on CRTC %u with mode %s" % \
              (connector.fullname, crtc.id, mode.name))

        # Create a frame buffer
        fb = pykms.DumbFramebuffer(self.card, mode.hdisplay, mode.vdisplay, "XR24")
        pykms.draw_test_pattern(fb)

        # Perform the mode set
        ret = self.atomic_crtc_mode_set(crtc, connector, mode, fb)
        if ret < 0:
            raise RuntimeError("atomic mode set failed with %d" % ret)

        self.logger.log("Atomic mode set complete")
        self.run(4)

        if self.flips == 0:
            raise RuntimeError("Page flip not registered")

    def main(self):
        for connector in self.card.connectors:
            self.start("modes on connector %s" % connector.fullname)

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

            # Test all available modes
            modes = connector.get_modes()
            if len(modes) == 0:
                self.skip("no mode available")
                continue

            for i in range(len(modes)):
                try:
                    self.progress(i+1, len(modes))
                    self.test_mode(connector, crtc, modes[i])
                except RuntimeError as e:
                    self.fail(e.message)
                    break
            else:
                self.success()

ModesTest().execute()
