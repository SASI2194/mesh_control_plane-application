"""
===============================================================================

Mesh Control Plane

Link Monitor

Reads wireless metrics from RouterOS and converts them into LinkMetrics.

===============================================================================
"""

from core.network_models import LinkMetrics


class LinkMonitor:

    def __init__(self, routeros_client, network_database, node_id):

        self.client = routeros_client
        self.database = network_database
        self.node_id = node_id

    #####################################################################

    def update(self):

        """
        Read RouterOS registration table and update NetworkDatabase.
        """

        registration = self.client.get_registration_table()

        if not registration:
            return

        #
        # First wireless client
        #

        station = registration[0]

        tx_rate = float(station.get("tx-rate", 0)) / 1e6
        rx_rate = float(station.get("rx-rate", 0)) / 1e6

        metrics = LinkMetrics(

            node_id=self.node_id,

            rssi=float(station.get("signal", 0)),

            tx_rate=tx_rate,

            rx_rate=rx_rate

        )

        self.database.update_link(metrics)

    #####################################################################

    def print_status(self):

        self.database.print_database()
