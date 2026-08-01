#!/usr/bin/env python3

"""
===============================================================================

Mesh Control Plane

Verification Framework

End-to-End Verification Tool

Validates:
    • Real-time Dynamic Topic Bandwidth
    • Packet Loss Tolerance Limit Verification
    • Low-Priority Topic Shedding Evaluation
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
        # Configuration
        #

        from utils.config_manager import ConfigManager

        self.config_mgr = ConfigManager()
        self.config_mgr.load()
        mesh_cfg = self.config_mgr.get("mesh")
        sched_cfg = mesh_cfg.get("scheduler", {})

        self.max_bw = float(sched_cfg.get("maximum_bandwidth_mbps", 600.0))
        self.loss_tolerance = float(sched_cfg.get("packet_loss_tolerance_percent", 5.0))

        #
        # Scheduler
        #

        self.scheduler = BandwidthScheduler(self.registry)
        self.scheduler.available_bandwidth = self.max_bw
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
        print("   MESH CONTROL PLANE LOSS-TOLERANCE VERIFICATION")
        print("==========================================================")

        print()

        print(f"Expected Bandwidth       : {self.scheduler.used_bandwidth:.1f} Mbps")

        print(f"Available Bandwidth      : {self.scheduler.available_bandwidth:.1f} Mbps")

        print(f"Packet Loss Limit        : {self.loss_tolerance:.1f} %")

        print()

    ###########################################################################

    def print_topics(self):

        stats = self.monitor.database()

        print()

        print("==========================================================================================================")
        print("Topic                 Packets       Rx Mbps     Loss %   Sequence Status")
        print("==========================================================================================================")

        total_packets = 0
        within_tolerance = True
        congested_topics = []

        for topic in stats.topics():

            s = stats.statistics(topic)

            total_packets += s["packets"]
            loss_pct = s["loss"]

            if s["packets"] == 0:
                status_str = "[NO DATA]"
                within_tolerance = False
            elif loss_pct <= self.loss_tolerance:
                status_str = f"[PASS: Loss <= {self.loss_tolerance:.1f}%]"
            else:
                status_str = f"[EXCEEDS TOLERANCE ({loss_pct:.1f}% > {self.loss_tolerance:.1f}%) -> SHED LOW PRIORITY]"
                within_tolerance = False
                congested_topics.append(topic)

            print(

                f"{topic:22}"

                f"{s['packets']:8}"

                f"{s['mbps']:12.2f}"

                f"{loss_pct:9.1f}%"

                f"   {status_str}"

            )

        print("----------------------------------------------------------------------------------------------------------")

        print(f"Total Packets Received : {total_packets}")

        if total_packets > 0 and within_tolerance:
            print(f"Loss Tolerance Verification     : PASS (All topics loss <= {self.loss_tolerance:.1f}%)")
        elif congested_topics:
            print(f"Loss Tolerance Verification     : CONGESTION DETECTED on {len(congested_topics)} topic(s) (Triggers Low-Priority Shedding)")

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
