#!/usr/bin/python3

import kmstest
import pykms

class ConnectorsTest(kmstest.KMSTest):
    """Perform sanity checks on all connectors."""

    def main(self):
        for connector in self.card.connectors:
            self.start("connector %s" % connector.fullname)

            # Every connector should have at least one suitable CRTC
            crtcs = connector.get_possible_crtcs()
            if len(crtcs) == 0:
                self.fail("no possible CRTC")
                continue

            # Connected connectors should have at least one mode
            if connector.connected():
                modes = connector.get_modes()
                if len(modes) == 0:
                    self.fail("no mode available")
                    continue

            self.success()

ConnectorsTest().execute()
