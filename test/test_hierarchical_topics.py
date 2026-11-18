#!/usr/bin/env python3
"""
===============================================================================
Mesh Control Plane

Test Script: Hierarchical Topic Registry & Multi-Device Stream Matching Test
===============================================================================
"""

import os
import sys
import unittest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from ros.topic_database import TopicRegistry


class TestHierarchicalTopics(unittest.TestCase):

    def setUp(self):
        self.registry = TopicRegistry()

    def test_multi_device_stream_matching_and_aggregation(self):
        """
        Verify that namespaced topics from multiple robots (/ugv_01/..., /ugv_02/...)
        properly match their base canonical topic (/compressed/lidar_point_cloud),
        aggregate swarm bandwidth and rates, and retain per-stream breakdown.
        """
        measured = {
            "/ugv_01/compressed/lidar_point_cloud": {
                "mbps": 12.0, "hz": 10.0, "avg_bytes": 150000.0, "data_size_str": "150 KB",
                "tx_mbps": 0.0, "tx_hz": 0.0, "tx_data_size_str": "0 B",
                "rx_mbps": 12.0, "rx_hz": 10.0, "rx_data_size_str": "150 KB",
                "diff_mbps": -12.0, "delivery_pct": 100.0, "role": "SUBSCRIBER"
            },
            "/ugv_02/compressed/lidar_point_cloud": {
                "mbps": 14.5, "hz": 10.0, "avg_bytes": 181250.0, "data_size_str": "181 KB",
                "tx_mbps": 0.0, "tx_hz": 0.0, "tx_data_size_str": "0 B",
                "rx_mbps": 14.5, "rx_hz": 10.0, "rx_data_size_str": "181 KB",
                "diff_mbps": -14.5, "delivery_pct": 92.0, "role": "SUBSCRIBER"
            },
            "/ugv_03/compressed/front_cam": {
                "mbps": 8.0, "hz": 30.0, "avg_bytes": 33333.0, "data_size_str": "33 KB",
                "tx_mbps": 8.0, "tx_hz": 30.0, "tx_data_size_str": "33 KB",
                "rx_mbps": 0.0, "rx_hz": 0.0, "rx_data_size_str": "0 B",
                "diff_mbps": 8.0, "delivery_pct": 100.0, "role": "PUBLISHER"
            },
            "/tf": {
                "mbps": 0.2, "hz": 5.0, "avg_bytes": 5000.0, "data_size_str": "5 KB",
                "tx_mbps": 0.0, "tx_hz": 0.0, "tx_data_size_str": "0 B",
                "rx_mbps": 0.2, "rx_hz": 5.0, "rx_data_size_str": "5 KB",
                "diff_mbps": -0.2, "delivery_pct": 100.0, "role": "SUBSCRIBER"
            }
        }

        self.registry.update_measured_metrics(measured)

        # 1. Verify /compressed/lidar_point_cloud
        t_lidar = self.registry.get("/compressed/lidar_point_cloud")
        self.assertIsNotNone(t_lidar)
        self.assertEqual(t_lidar["role"], "SUBSCRIBER")
        self.assertEqual(t_lidar["rx_hz"], 20.0)
        self.assertEqual(t_lidar["rx_mbps"], 26.5)
        self.assertEqual(t_lidar["delivery_pct"], 92.0)
        self.assertEqual(t_lidar["verification"], "8.0% LOSS")
        self.assertEqual(t_lidar["active_streams_count"], 2)

        streams = {s["device_name"]: s for s in t_lidar["active_streams"]}
        self.assertIn("UGV-01", streams)
        self.assertIn("UGV-02", streams)

        s1 = streams["UGV-01"]
        self.assertEqual(s1["rx_hz"], 10.0)
        self.assertEqual(s1["rx_mbps"], 12.0)
        self.assertEqual(s1["verification"], "FULL DATA 100%")

        s2 = streams["UGV-02"]
        self.assertEqual(s2["rx_hz"], 10.0)
        self.assertEqual(s2["rx_mbps"], 14.5)
        self.assertEqual(s2["verification"], "8.0% LOSS DETECTED")

        # 2. Verify /compressed/front_cam Publisher Stream
        t_cam = self.registry.get("/compressed/front_cam")
        self.assertIsNotNone(t_cam)
        self.assertEqual(t_cam["role"], "PUBLISHER")
        self.assertEqual(t_cam["tx_hz"], 30.0)
        self.assertEqual(t_cam["tx_mbps"], 8.0)
        self.assertEqual(t_cam["verification"], "TX LIVE 100%")
        self.assertEqual(t_cam["active_streams_count"], 1)

        # 3. Verify unnamespaced /tf
        t_tf = self.registry.get("/tf")
        self.assertIsNotNone(t_tf)
        self.assertEqual(t_tf["rx_hz"], 5.0)
        self.assertEqual(t_tf["verification"], "FULL DATA 100%")
        self.assertEqual(t_tf["active_streams_count"], 1)

    def test_rtabmap_3d_cloud_topic_classification(self):
        from ros.topic_database import is_rtabmap_3d_cloud_topic, is_2d_occupancy_grid_topic

        # RTAB-Map 3D cloud topics (must be True)
        self.assertTrue(is_rtabmap_3d_cloud_topic("/rtabmap/cloud_obstacles"))
        self.assertTrue(is_rtabmap_3d_cloud_topic("/ugv_02/rtabmap/cloud_obstacles"))
        self.assertTrue(is_rtabmap_3d_cloud_topic("filtered/55/ugv_02/rtabmap/cloud_obstacles"))
        self.assertTrue(is_rtabmap_3d_cloud_topic("/rtabmap/cloud_map"))
        self.assertTrue(is_rtabmap_3d_cloud_topic("/ugv_02/rtabmap/cloud_map"))
        self.assertTrue(is_rtabmap_3d_cloud_topic("/ugv_02/rtabmap/cloud_ground"))
        self.assertTrue(is_rtabmap_3d_cloud_topic("/ugv_02/rtabmap/octomap_grid"))

        # Exclusions (must be False)
        self.assertFalse(is_rtabmap_3d_cloud_topic("/ugv_02/compressed/cloud_obstacles"))
        self.assertFalse(is_rtabmap_3d_cloud_topic("/ugv_02/rtabmap/map"))
        self.assertFalse(is_rtabmap_3d_cloud_topic("/map"))
        self.assertFalse(is_rtabmap_3d_cloud_topic("/ugv_02/scan_2d"))

        # 2D occupancy grid topics
        self.assertTrue(is_2d_occupancy_grid_topic("/map"))
        self.assertTrue(is_2d_occupancy_grid_topic("/ugv_02/map"))
        self.assertTrue(is_2d_occupancy_grid_topic("/rtabmap/map"))
        self.assertTrue(is_2d_occupancy_grid_topic("/ugv_02/rtabmap/map"))
        self.assertFalse(is_2d_occupancy_grid_topic("/ugv_02/rtabmap/cloud_obstacles"))

    def test_forwarding_engine_3d_cloud_deduplication(self):
        from routing.forwarding_engine import ForwardingEngine
        from core.network_models import MeshSample

        class DummySession:
            def __init__(self, subscribed_keys):
                self.subscribed_keys = set(subscribed_keys)
                self.published_keys = []
            def has_matching_subscribers(self, key):
                return key in self.subscribed_keys
            def publish(self, key, payload):
                self.published_keys.append(key)

        sample = MeshSample(
            key="/ugv_02/rtabmap/cloud_obstacles",
            payload=b"test_payload",
            allowed=True,
            priority=1,
            sequence_number=1,
            origin_ip="192.168.3.66"
        )

        # 1. When both namespaced and global keys have matching subscribers,
        # verify deduplication: publishes strictly to device-namespaced key.
        session = DummySession(["filtered/55/ugv_02/rtabmap/cloud_obstacles", "filtered/55/rtabmap/cloud_obstacles"])
        engine = ForwardingEngine(session, device_ns="ugv_02")
        engine.forward(sample)
        self.assertEqual(session.published_keys, ["filtered/55/ugv_02/rtabmap/cloud_obstacles"])

        # 2. When only the global key has subscribers, falls back to single global key.
        session2 = DummySession(["filtered/55/rtabmap/cloud_obstacles"])
        engine2 = ForwardingEngine(session2, device_ns="ugv_02")
        engine2.forward(sample)
        self.assertEqual(session2.published_keys, ["filtered/55/rtabmap/cloud_obstacles"])

        # 3. When 0 remote subscribers exist, skips egress completely (Rule 8 demand filtering).
        session3 = DummySession([])
        engine3 = ForwardingEngine(session3, device_ns="ugv_02")
        engine3.forward(sample)
        self.assertEqual(session3.published_keys, [])

    def test_latched_3d_cloud_sync_delivery(self):
        from core.network_models import MeshSample
        from mesh_node import MeshNode

        class DummyRawSession:
            def __init__(self):
                self.puts = []
            def put(self, key, payload):
                self.puts.append((key, payload))

        class DummyForwardSession:
            def __init__(self):
                self.session = DummyRawSession()

        node = object.__new__(MeshNode)
        node.my_dev_ns = "ugv_02"
        node.my_ip = "192.168.3.66"
        node.forward_session = DummyForwardSession()
        node.latched_payload_cache = {
            "/ugv_02/rtabmap/cloud_obstacles": (b"cloud_bytes", "192.168.3.66"),
            "/ugv_01/rtabmap/cloud_obstacles": (b"remote_bytes", "192.168.3.65"),
        }

        node._deliver_cached_3d_clouds("TEST SYNC")
        self.assertEqual(len(node.forward_session.session.puts), 1)
        out_key, packed = node.forward_session.session.puts[0]
        self.assertEqual(out_key, "filtered/55/ugv_02/rtabmap/cloud_obstacles")
        seq, ts, orig_ip, raw = MeshSample.unpack_payload(packed)
        self.assertEqual(orig_ip, "192.168.3.66")
        self.assertEqual(raw, b"cloud_bytes")


if __name__ == "__main__":
    unittest.main()
