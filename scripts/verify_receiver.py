#!/usr/bin/env python3

"""
===============================================================================

Mesh Control Plane

Verification Receiver

Purpose
-------
Receives forwarded topics from another AGV and displays
real-time packet statistics.

===============================================================================
"""

import time
import threading

from mesh_transport.zenoh_session import ZenohSession


PEER_CONFIG = "config/zenoh/zenoh_peer_tcp.json5"


class VerificationReceiver:

    def __init__(self):

        self.session = ZenohSession(PEER_CONFIG)

        self.session.connect()

        #
        # Packet counters
        #

        self.counters = {}

        #
        # Subscribe to every forwarded topic
        #

        self.subscriber = self.session.subscribe(

            "filtered/**",

            self.callback

        )

    ##################################################################

    def callback(self, sample):

        topic = str(sample.key_expr)

        if topic not in self.counters:

            self.counters[topic] = 0

        self.counters[topic] += 1

    ##################################################################

    def display(self):

        while True:

            time.sleep(1)

            print("\033[2J\033[H", end="")

            print("==========================================================")
            print("      Mesh Control Plane Verification")
            print("==========================================================")
            print()

            print(f"{'Topic':25} {'Packets':>10}")

            print("-"*40)

            total = 0

            for topic in sorted(self.counters):

                packets = self.counters[topic]

                total += packets

                print(

                    f"{topic:25}"

                    f"{packets:10d}"

                )

            print()

            print(f"Total Packets : {total}")

    ##################################################################

    def run(self):

        threading.Thread(

            target=self.display,

            daemon=True

        ).start()

        while True:

            time.sleep(1)


########################################################################

if __name__ == "__main__":

    receiver = VerificationReceiver()

    receiver.run()
