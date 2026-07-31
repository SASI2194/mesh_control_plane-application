"""
===============================================================================

Mesh Control Plane

Network Database

Stores the latest network state for all nodes.

===============================================================================
"""

from typing import Dict

from core.network_models import LinkMetrics


class NetworkDatabase:

    def __init__(self):

        #
        # node_id -> LinkMetrics
        #

        self._links: Dict[str, LinkMetrics] = {}

    #####################################################################

    def update_link(self, metrics: LinkMetrics):

        self._links[metrics.node_id] = metrics

    #####################################################################

    def get_link(self, node_id):

        return self._links.get(node_id)

    #####################################################################

    def all_links(self):

        return self._links

    #####################################################################

    def print_database(self):

        print()

        print("=============== Network Database ===============")

        if len(self._links) == 0:

            print("No link information")

            print()

            return

        for node_id, link in self._links.items():

            print(
                f"{node_id:10} "
                f"RSSI={link.rssi:6.1f} dBm   "
                f"TX={link.tx_rate:7.1f} Mbps   "
                f"RX={link.rx_rate:7.1f} Mbps"
            )

        print()
