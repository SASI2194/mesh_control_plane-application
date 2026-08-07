#!/usr/bin/env python3

"""
===============================================================================

Mesh Control Plane

Bandwidth Scheduler

Priority-Based Topic Scheduler

Policy

1. Process priorities from highest to lowest.
2. Admit as many topics as possible within the current priority.
3. If the priority is only partially admitted, stop.
4. Never continue to a lower priority.

===============================================================================
"""


class BandwidthScheduler:

    #####################################################################

    def __init__(self, registry):

        self.registry = registry

        #
        # Input
        #

        self.available_bandwidth = 250.0

        #
        # Scheduler Result
        #

        self.allowed_topics = set()

        self.used_bandwidth = 0.0

        self.remaining_bandwidth = 0.0

    #####################################################################

    def schedule(self):

        self.allowed_topics.clear()

        self.used_bandwidth = 0.0

        remaining = self.available_bandwidth

        #
        # Priority 1 → Priority 5
        #

        for priority in range(1, 6):
            topics = []
            for topic in self.registry.all_topics().values():
                if topic["priority"] == priority:
                    st = str(topic.get("status", "ALLOW")).upper()
                    # Exclude topics marked as DENY from entering admission/bandwidth list
                    if st == "DENY":
                        continue
                    topics.append(topic)

            for topic in topics:
                self.allowed_topics.add(topic["name"])

        return self.allowed_topics

    #####################################################################

    def allowed(self, topic):

        return topic in self.allowed_topics

    #####################################################################

    def print_schedule(self):

        print()

        print("==================================================")
        print("Bandwidth Scheduler (Real-Time Dynamic Rate)")
        print("==================================================")

        print(f"Available Bandwidth : {self.available_bandwidth:.1f} Mbps")

        print()

        print("================ Allowed Topics ================")

        for topic in sorted(self.allowed_topics):
            info = self.registry.get(topic)
            prio = info.get("priority", 5) if info else 5
            mbps = info.get("measured_bandwidth", info.get("tx_mbps", info.get("rx_mbps", 0.0))) if info else 0.0
            st = info.get("status", "ALLOW").upper() if info else "ALLOW"
            print(f"{topic:15} P{prio}   Status: {st} ({mbps:.1f} Measured Mbps)")

        print()

        print(f"Used Bandwidth      : {self.used_bandwidth:.1f} Mbps")

        print(f"Remaining Bandwidth : {self.remaining_bandwidth:.1f} Mbps")

        print()

    #####################################################################

    def scheduler_state(self):

        """
        Returns the current scheduler state.
        """

        return {

            "available_bandwidth": self.available_bandwidth,

            "used_bandwidth": self.used_bandwidth,

            "remaining_bandwidth": self.remaining_bandwidth,

            "allowed_topics": sorted(self.allowed_topics)

        }
