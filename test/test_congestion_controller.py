#!/usr/bin/env python3

"""
===============================================================================
Mesh Control Plane

Test Script: Congestion Controller & Low-Priority Topic Shedding
===============================================================================
"""

import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from ros.topic_database import TopicRegistry
from scheduler.bandwidth_scheduler import BandwidthScheduler
from scheduler.congestion_controller import CongestionController


def main():
    print("==========================================================")
    print("Testing Congestion Controller & Topic Shedding")
    print("==========================================================")

    registry = TopicRegistry()
    scheduler = BandwidthScheduler(registry)
    scheduler.available_bandwidth = 600.0
    scheduler.schedule()

    print(f"Initial Allowed Topics ({len(scheduler.allowed_topics)}): {sorted(scheduler.allowed_topics)}")

    controller = CongestionController(tolerance_percent=5.0, hysteresis_percent=2.0, dwell_seconds=0.0, recovery_dwell_seconds=0.0)

    # 1. Normal link condition: Loss 3.0% (<= 5.0%) -> No Shedding
    res1 = controller.update_feedback(current_loss_percent=3.0, scheduler=scheduler, registry=registry)
    print(f"\n[Test 1: Loss 3.0% <= Limit 5.0%]")
    print(f"Shedding Level: {res1['shedding_level']} (Shed Topics: {res1['shed_topics']})")
    assert res1["shedding_level"] == 0

    # 2. Congested link condition: Loss 12.6% (> 5.0%) -> Trigger Shedding Level 1
    res2 = controller.update_feedback(current_loss_percent=12.6, scheduler=scheduler, registry=registry)
    print(f"\n[Test 2: Congestion Loss 12.6% > Limit 5.0%]")
    print(f"Shedding Level: {res2['shedding_level']} (Shed Topics: {res2['shed_topics']})")
    assert res2["shedding_level"] == 1
    assert len(res2["shed_topics"]) > 0

    # 3. Severe congestion condition: Loss 20.0% -> Increase Shedding Level 2
    res3 = controller.update_feedback(current_loss_percent=20.0, scheduler=scheduler, registry=registry)
    print(f"\n[Test 3: Severe Loss 20.0% > Limit 5.0%]")
    print(f"Shedding Level: {res3['shedding_level']} (Shed Topics: {res3['shed_topics']})")
    assert res3["shedding_level"] == 2
    assert len(res3["shed_topics"]) > len(res2["shed_topics"])

    # 4. Link recovers: Loss 1.5% (< 3.0%) -> Decrease Shedding Level
    res4 = controller.update_feedback(current_loss_percent=1.5, scheduler=scheduler, registry=registry)
    print(f"\n[Test 4: Link Recovery Loss 1.5% < 3.0%]")
    print(f"Shedding Level: {res4['shedding_level']}")
    assert res4["shedding_level"] == 1

    print("\n[SUCCESS] Congestion Controller & Topic Shedding Tests PASSED!")


if __name__ == "__main__":
    main()
