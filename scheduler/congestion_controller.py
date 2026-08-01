#!/usr/bin/env python3

"""
===============================================================================

Mesh Control Plane

Congestion Controller

Monitors real-time packet loss across the mesh network and dynamically
sheds (drops) low-priority topics when loss exceeds the configured tolerance limit.

===============================================================================
"""

from threading import Lock


class CongestionController:
    """
    Dynamic Packet Loss Tolerance & Congestion Feedback Shedder.
    """

    def __init__(self, tolerance_percent=5.0, hysteresis_percent=2.0):
        self.tolerance_percent = float(tolerance_percent)
        self.hysteresis_percent = float(hysteresis_percent)

        # Shedding level: 0 = No shedding, 1..4 = Levels of priority shedding
        self.shedding_level = 0
        self.max_shedding_level = 4  # Never shed Priority 1

        self.last_loss_percent = 0.0
        self.shed_topics = set()
        self.lock = Lock()

    def update_feedback(self, current_loss_percent, scheduler, registry):
        """
        Evaluates real-time packet loss against tolerance limit and adjusts allowed topics.
        """
        with self.lock:
            self.last_loss_percent = float(current_loss_percent)

            # Check if loss exceeds tolerance
            if self.last_loss_percent > self.tolerance_percent:
                if self.shedding_level < self.max_shedding_level:
                    self.shedding_level += 1
                    print(
                        f"[CONGESTION DETECTED] Packet Loss ({self.last_loss_percent:.1f}%) > "
                        f"Limit ({self.tolerance_percent:.1f}%). Increasing Shedding Level to {self.shedding_level}."
                    )
            # Recovery condition: Loss drops below (tolerance - hysteresis)
            elif self.last_loss_percent < (self.tolerance_percent - self.hysteresis_percent):
                if self.shedding_level > 0:
                    self.shedding_level -= 1
                    print(
                        f"[LINK RECOVERED] Packet Loss ({self.last_loss_percent:.1f}%) < "
                        f"Threshold ({self.tolerance_percent - self.hysteresis_percent:.1f}%). Decreasing Shedding Level to {self.shedding_level}."
                    )

            # Apply shedding rules to scheduler's allowed topics
            self._apply_shedding(scheduler, registry)

            return {
                "loss_percent": self.last_loss_percent,
                "tolerance_percent": self.tolerance_percent,
                "shedding_level": self.shedding_level,
                "shed_topics": sorted(self.shed_topics)
            }

    def _apply_shedding(self, scheduler, registry):
        self.shed_topics.clear()
        if self.shedding_level <= 0 or not scheduler.allowed_topics:
            return

        # Find the highest priority number (lowest importance) currently admitted
        admitted_priorities = [
            registry.get(t)["priority"] for t in scheduler.allowed_topics
            if registry.get(t) and registry.get(t)["priority"] > 1
        ]

        if not admitted_priorities:
            return

        # Determine cutoff priority based on shedding level
        max_pri = max(admitted_priorities)
        cutoff_priority = max(2, max_pri - self.shedding_level + 1)

        to_remove = set()
        for topic_name in list(scheduler.allowed_topics):
            info = registry.get(topic_name)
            if info and info["priority"] >= cutoff_priority and info["priority"] > 1:
                to_remove.add(topic_name)

        scheduler.allowed_topics -= to_remove
        self.shed_topics = to_remove

        if to_remove:
            print(f"[CONGESTION SHEDDING] Dropped Low-Priority Topics (Priority >= {cutoff_priority}): {sorted(to_remove)}")
