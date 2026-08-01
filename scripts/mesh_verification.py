#!/usr/bin/env python3

"""
===============================================================================

Mesh Control Plane

Verification Framework

End-to-End Verification Tool

Validates:
    • Real-time Dynamic Topic Bandwidth
    • Lossless Full Data Transmission (0% Packet Loss)
    • Scheduler Decisions & Topic Forwarding
    • System Throughput & Scheduler Accuracy

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

        self.scheduler = BandwidthScheduler(self.registry)

        from utils.config_manager import ConfigManager

        self.config_mgr = ConfigManager()
        self.config_mgr.load()
        mesh_cfg = self.config_mgr.get("mesh")
        max_bw = float(mesh_cfg.get("scheduler", {}).get("maximum_bandwidth_mbps", 600.0))

        self.scheduler.available_bandwidth = max_bw

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
        print("   MESH CONTROL PLANE REAL-TIME LOSSLESS VERIFICATION")
        print("==========================================================")

        print()

        print(f"Expected Bandwidth : {self.scheduler.used_bandwidth:.1f} Mbps")

        print(f"Available Bandwidth: {self.scheduler.available_bandwidth:.1f} Mbps")

        print()

    ###########################################################################

    def print_topics(self):

        stats = self.monitor.database()

        print()

        print("========================================================================================")
        print("Topic                 Packets       Rx Mbps     Loss %   Sequence Status")
        print("========================================================================================")

        total_packets = 0
        all_lossless = True

        for topic in stats.topics():

            s = stats.statistics(topic)

            total_packets += s["packets"]
            loss_pct = s["loss"]

            if loss_pct == 0.0 and s["packets"] > 0:
                status_str = "[FULL DATA 100%]"
            elif s["packets"] == 0:
                status_str = "[NO DATA]"
                all_lossless = False
            else:
                status_str = f"[LOSS: {loss_pct:.1f}% ({s['seq_errors']} pkts)]"
                all_lossless = False

            print(

                f"{topic:22}"

                f"{s['packets']:8}"

                f"{s['mbps']:12.2f}"

                f"{loss_pct:9.1f}%"

                f"   {status_str}"

            )

        print("----------------------------------------------------------------------------------------")

        print(f"Total Packets Received : {total_packets}")
        if total_packets > 0 and all_lossless:
            print("Lossless Full Data Verification : PASS (100% Complete Transmission)")
        else:
            print("Lossless Full Data Verification : WAITING / MONITORING")

        print()

    ###########################################################################

    def run(self):

        self.monitor.start()

        self.print_header()

        try:

            while True:

                time.sleep(3)

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
