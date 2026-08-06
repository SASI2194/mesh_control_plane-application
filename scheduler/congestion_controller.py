#!/usr/bin/env python3

"""
===============================================================================

Mesh Control Plane

Congestion Controller

Monitors real-time packet loss across the mesh network and dynamically
sheds (drops) low-priority topics when loss exceeds the configured tolerance limit.

===============================================================================
"""

import time
from threading import Lock


class CongestionController:
    """
    Dynamic Packet Loss Tolerance & Congestion Feedback Shedder.
    """

    def __init__(self, tolerance_percent=5.0, hysteresis_percent=2.0, dwell_seconds=60.0):
        self.tolerance_percent = float(tolerance_percent)
        self.hysteresis_percent = float(hysteresis_percent)
        self.dwell_seconds = float(dwell_seconds)

        # Shedding level: 0 = No shedding, 1..4 = Levels of priority shedding
        self.shedding_level = 0
        self.max_shedding_level = 4  # Never shed Priority 1

        self.last_loss_percent = 0.0
        self.last_shed_change_time = 0.0
        self.shed_topics = set()
        self.lock = Lock()

    def update_feedback(self, current_loss_percent, scheduler, registry):
        """
        Evaluates real-time packet loss against tolerance limit and adjusts allowed topics.
        Enforces 60s wireless stabilization dwell time before each shedding step.
        """
        with self.lock:
            self.last_loss_percent = float(current_loss_percent)
            now = time.time()

            # Check if loss exceeds tolerance
            if self.last_loss_percent > self.tolerance_percent:
                if self.shedding_level < self.max_shedding_level:
                    # Enforce 60s wireless link stabilization dwell timer
                    if (now - self.last_shed_change_time) >= self.dwell_seconds:
                        self.shedding_level += 1
                        self.last_shed_change_time = now
                        print(
                            f"[CONGESTION DETECTED] Packet Loss ({self.last_loss_percent:.1f}%) > "
                            f"Limit ({self.tolerance_percent:.1f}%). Increasing Shedding Level to {self.shedding_level} (60s Dwell Active)."
                        )
            # Recovery condition: Loss drops below (tolerance - hysteresis)
            elif self.last_loss_percent < (self.tolerance_percent - self.hysteresis_percent):
                if self.shedding_level > 0:
                    # Enforce 60s link recovery verification dwell timer
                    if (now - self.last_shed_change_time) >= self.dwell_seconds:
                        self.shedding_level -= 1
                        self.last_shed_change_time = now
                        print(
                            f"[LINK RECOVERED] Packet Loss ({self.last_loss_percent:.1f}%) < "
                            f"Threshold ({self.tolerance_percent - self.hysteresis_percent:.1f}%). Decreasing Shedding Level to {self.shedding_level} (60s Dwell Active)."
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

        # Collect non-P1 admitted topics
        candidates = []
        for t in list(scheduler.allowed_topics):
            info = registry.get(t)
            if info and info.get("priority", 5) > 1:
                # Get measured Tx bandwidth if available, otherwise nominal bandwidth
                tx_mbps = info.get("tx_mbps", 0.0)
                nom_bw = float(info.get("bandwidth", 0.0))
                effective_bw = tx_mbps if tx_mbps > 0.0 else nom_bw
                candidates.append({
                    "name": t,
                    "priority": info.get("priority", 5),
                    "bandwidth": effective_bw
                })

        if not candidates:
            return

        # Sort candidates: Lowest priority tier first (P5 > P4 > P3 > P2),
        # then by highest measured bandwidth descending within that priority tier
        candidates.sort(key=lambda x: (-x["priority"], -x["bandwidth"]))

        # Select target candidates to shed based on shedding_level (drops exactly 1 topic per step)
        num_to_shed = min(len(candidates), self.shedding_level)
        to_remove = {c["name"] for c in candidates[:num_to_shed]}

        scheduler.allowed_topics -= to_remove
        self.shed_topics = to_remove

        if to_remove:
            details = [f"{c['name']} (P{c['priority']}, {c['bandwidth']:.1f} Mbps)" for c in candidates[:num_to_shed]]
            print(f"[CONGESTION SHEDDING] Target-dropped heavy topics: {details}")
