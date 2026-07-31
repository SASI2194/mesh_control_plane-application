#!/usr/bin/env python3

"""
===============================================================================

Mesh Control Plane

Verification Framework

End-to-End Verification Tool

Validates:

    • Scheduler Decisions
    • Forwarded Topics
    • Measured Bandwidth
    • Packet Statistics
    • Scheduler Accuracy

===============================================================================
"""

import os
import sys
import time

#
# Allow imports when executed from scripts/
#

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from verification.packet_monitor import PacketMonitor
from verification.throughput import ThroughputCalculator
from verification.scheduler_checker import SchedulerChecker

from ros.topic_database import TopicRegistry
from scheduler.bandwidth_scheduler import BandwidthScheduler


CONFIG = "/home/nvidia/ws_rmw_zenoh/src/rmw_zenoh-humble/rmw_zenoh_cpp/config/tcp/zenoh_peer_tcp.json5"


###############################################################################


class MeshVerification:

    ###########################################################################

    def __init__(self):

        #
        # Topic Database
        #

        self.registry = TopicRegistry()

        #
        # Scheduler
        #

        self.scheduler = BandwidthScheduler(

            self.registry

        )

        #
        # Same bandwidth used in mesh_node.py
        #

        self.scheduler.available_bandwidth = 250.0

        self.scheduler.schedule()

        #
        # Packet Monitor
        #

        self.monitor = PacketMonitor(CONFIG)

        #
        # Throughput
        #

        self.throughput = ThroughputCalculator()

        self.throughput.set_expected(

            self.scheduler.used_bandwidth

        )

        #
        # Scheduler Checker
        #

        self.checker = SchedulerChecker(

            self.registry,

            self.scheduler

        )

    ###########################################################################

    def print_header(self):

        print()

        print("==========================================================")
        print("      MESH CONTROL PLANE VERIFICATION")
        print("==========================================================")

        print()

        print(f"Expected Bandwidth : {self.scheduler.used_bandwidth:.1f} Mbps")

        print(f"Available Bandwidth: {self.scheduler.available_bandwidth:.1f} Mbps")

        print()

    ###########################################################################

    def print_topics(self):

        stats = self.monitor.database()

        print()

        print("==========================================================================")
        print("Topic                 Packets      Mbps        Avg Packet")
        print("==========================================================================")

        total_packets = 0

        for topic in stats.topics():

            s = stats.statistics(topic)

            total_packets += s["packets"]

            print(

                f"{topic:22}"

                f"{s['packets']:8}"

                f"{s['mbps']:12.2f}"

                f"{s['avg_packet']/1024:14.1f} KB"

            )

        print("--------------------------------------------------------------------------")

        print(f"Total Packets : {total_packets}")

        print()

    ###########################################################################

    def run(self):

        self.monitor.start()

        self.print_header()

        try:

            while True:

                time.sleep(5)

                stats = self.monitor.database()

                self.throughput.update(

                    stats

                )

                self.print_topics()

                self.throughput.print_report()

                self.checker.print_report(

                    stats

                )

        except KeyboardInterrupt:

            print()

            print("Stopping Verification")

            self.monitor.stop()


###############################################################################

if __name__ == "__main__":

    verifier = MeshVerification()

    verifier.run()
