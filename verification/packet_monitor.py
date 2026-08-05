#!/usr/bin/env python3

"""
===============================================================================

Mesh Control Plane

Verification Framework

Packet Monitor

Receives forwarded mesh packets and updates runtime statistics with sequence tracking.

===============================================================================
"""

from mesh_transport.zenoh_session import ZenohSession
from verification.statistics import StatisticsDatabase
from core.network_models import MeshSample


class PacketMonitor:

    ###########################################################################

    def __init__(self, config_file):

        #
        # Transport
        #

        self.session = ZenohSession(config_file)

        #
        # Statistics Database
        #

        self.statistics = StatisticsDatabase()

        #
        # Subscriber
        #

        self.subscriber = None

    ###########################################################################

    def start(self):

        self.session.connect()

        print()

        print("=========================================================")
        print("Packet Monitor (Lossless Sequence Verification)")
        print("=========================================================")

        self.subscriber = self.session.subscribe(

            "filtered/**",

            self.callback

        )

        print("Subscribed : filtered/**")

        print()

    ###########################################################################

    def callback(self, sample):

        topic = str(sample.key_expr)

        payload = sample.payload.to_bytes()

        # Unpack sequence number, timestamp, and origin IP
        seq_num, timestamp, origin_ip, raw_payload = MeshSample.unpack_payload(payload)

        self.statistics.update(

            topic,

            raw_payload,

            seq_num

        )

    ###########################################################################

    def database(self):

        return self.statistics

    ###########################################################################

    def stop(self):

        if self.subscriber is not None:

            self.subscriber.undeclare()

        self.session.close()

        print()

        print("[INFO] Packet Monitor stopped.")

        print()
