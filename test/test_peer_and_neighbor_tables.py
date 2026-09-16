#!/usr/bin/env python3

"""
===============================================================================

Mesh Control Plane

Test Suite: Segregated Discovered Peer Table & Best 2 Neighbour Table Test

Verifies that:
1. TelemetryDataProvider generates Table 1 (NetMetal AX Discovered Peer Table)
   with MAC address, IP, interface, signal (RSSI), SNR, and PHY rates.
2. TelemetryDataProvider generates Table 2 (Best 2 Neighbour Selection Governance Table)
   with evaluated link quality scores and assigned roles (PRIMARY_ACTIVE / STANDBY_BACKUP).
3. Web REST API endpoints (/api/peers, /api/neighbors, /api/all) expose both tables cleanly.

===============================================================================
"""

import os
import sys
import unittest
import json
import urllib.request
import time

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from dashboard.server import DATA_PROVIDER, start_dashboard_background


class TestPeerAndNeighborTables(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        os.environ["no_proxy"] = "127.0.0.1,localhost"
        os.environ["HTTP_PROXY"] = ""
        os.environ["http_proxy"] = ""

        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        urllib.request.install_opener(opener)

        cls.server_thread = start_dashboard_background(host="127.0.0.1", port=8091)
        time.sleep(1.0)

    def setUp(self):
        DATA_PROVIDER.set_mesh_node_running(True)
        DATA_PROVIDER.record_node_activity("192.168.3.65")
        DATA_PROVIDER.record_node_activity("192.168.3.67")
        for n in DATA_PROVIDER.nodes:
            if n["id"] == "UGV-01":
                n["status"] = "ONLINE"
                n["is_local"] = True
                n["rssi"] = -62.0
                n["latency"] = 1.0
                n["loss"] = 0.0
                n["snr"] = 30.0
            elif n["id"] == "UGV-03":
                n["status"] = "ONLINE"
                n["is_local"] = False
                n["rssi"] = -56.0
                n["latency"] = 8.5
                n["loss"] = 0.0
                n["snr"] = 30.0
                n["link_score"] = 0.85
                n["neighbor_role"] = "PRIMARY_ACTIVE"

    def test_table1_discovered_peers(self):
        peers = DATA_PROVIDER.get_discovered_peers()
        self.assertGreaterEqual(len(peers), 1)
        peer = peers[0]
        self.assertIn("node_id", peer)
        self.assertIn("mac", peer)
        self.assertIn("ip", peer)
        self.assertIn("interface", peer)
        self.assertIn("rssi", peer)
        self.assertIn("snr", peer)
        self.assertIn("tx_rate", peer)
        self.assertIn("rx_rate", peer)

    def test_table2_neighbor_selection(self):
        neighbors = DATA_PROVIDER.get_neighbor_selection_table()
        self.assertGreaterEqual(len(neighbors), 1)
        neighbor = neighbors[0]
        self.assertIn("node_id", neighbor)
        self.assertIn("ip", neighbor)
        self.assertIn("eval_rssi", neighbor)
        self.assertIn("eval_latency", neighbor)
        self.assertIn("eval_loss", neighbor)
        self.assertIn("eval_snr", neighbor)
        self.assertIn("link_score", neighbor)
        self.assertIn("assigned_role", neighbor)

    def test_rest_api_peers_and_neighbors(self):
        # 1. Test GET /api/peers
        req1 = urllib.request.urlopen("http://127.0.0.1:8091/api/peers")
        self.assertEqual(req1.status, 200)
        peers_data = json.loads(req1.read().decode("utf-8"))
        self.assertIsInstance(peers_data, list)
        self.assertGreaterEqual(len(peers_data), 1)

        # 2. Test GET /api/neighbors
        self.setUp()
        req2 = urllib.request.urlopen("http://127.0.0.1:8091/api/neighbors")
        self.assertEqual(req2.status, 200)
        neighbors_data = json.loads(req2.read().decode("utf-8"))
        self.assertIsInstance(neighbors_data, list)
        self.assertGreaterEqual(len(neighbors_data), 1)

        # 3. Test GET /api/all
        req3 = urllib.request.urlopen("http://127.0.0.1:8091/api/all")
        self.assertEqual(req3.status, 200)
        all_data = json.loads(req3.read().decode("utf-8"))
        self.assertIn("peer_table", all_data)
        self.assertIn("neighbor_table", all_data)


if __name__ == "__main__":
    unittest.main()
