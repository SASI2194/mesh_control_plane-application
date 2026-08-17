#!/usr/bin/env python3

"""
===============================================================================

Mesh Control Plane

Forwarding Engine

Only this module is allowed to publish data to the mesh network.

Responsibility:
1. Receive scheduler decisions
2. Forward admitted topics with sequence tracking metadata
3. Drop rejected topics
4. Maintain forwarding statistics

===============================================================================
"""

from core.network_models import MeshSample


class ForwardingEngine:

    #####################################################################

    def __init__(self, session, my_ip: str = "127.0.0.1"):

        #
        # Zenoh publishing session
        #

        self.session = session
        self.my_ip = my_ip

        #
        # Statistics
        #

        self.forwarded_packets = 0
        self.dropped_packets = 0

        self.forwarded_bytes = 0
        self.dropped_bytes = 0

    #####################################################################

    def forward(self, sample: MeshSample):

        """
        Forwards admitted ROS 2 topic payload onto Zenoh Control Plane transport (filtered/<topic>).
        """

        if not sample.allowed:

            self.dropped_packets += 1
            self.dropped_bytes += len(sample.payload)
            return

        #################################################################
        # Format Zenoh Key
        #################################################################

        topic_name = sample.key.lstrip("/")

        #################################################################
        # Mesh output key
        #################################################################

        output_key = f"filtered/{topic_name}"

        #################################################################
        # Pack payload with sequence metadata header & origin IP
        #################################################################

        origin = sample.origin_ip if sample.origin_ip and sample.origin_ip != "127.0.0.1" else self.my_ip
        packed_payload = MeshSample.pack_payload(
            sample.sequence_number,
            sample.timestamp,
            sample.payload,
            origin_ip=origin
        )

        # Real-time Wireless Mesh Link Audit (2.0s Heartbeat Freshness Window)
        remote_active = False
        try:
            from dashboard.server import DATA_PROVIDER
            if DATA_PROVIDER:
                import time
                now = time.time()
                with DATA_PROVIDER.lock:
                    for n in DATA_PROVIDER.nodes:
                        if not n.get("is_local") and (now - DATA_PROVIDER.node_activity.get(n["ip"], 0.0)) <= 2.0:
                            remote_active = True
                            break
        except Exception:
            remote_active = True

        if not remote_active:
            self.dropped_packets += 1
            self.dropped_bytes += len(sample.payload)
            print(f"[HOLD (LINK DOWN)] {output_key} (Seq #{sample.sequence_number})")
            return

        #################################################################
        # Publish
        #################################################################

        try:

            self.session.publish(

                output_key,

                packed_payload

            )

            self.forwarded_packets += 1

            self.forwarded_bytes += len(sample.payload)

            print(f"[FORWARD] {output_key} (Seq #{sample.sequence_number})")

        except Exception as ex:

            #
            # Publishing failed
            #

            self.dropped_packets += 1

            self.dropped_bytes += len(sample.payload)

            print()

            print("==========================================")
            print("Forwarding Error")
            print("==========================================")

            print(output_key)

            print(ex)

            print()

    #####################################################################

    def statistics(self):

        print()

        print("===================================================")
        print("Forwarding Statistics")
        print("===================================================")

        print(f"Forwarded Packets : {self.forwarded_packets}")
        print(f"Dropped Packets   : {self.dropped_packets}")

        print()

        print(f"Forwarded Data    : {self.forwarded_bytes/1e6:.2f} MB")
        print(f"Dropped Data      : {self.dropped_bytes/1e6:.2f} MB")

        total = self.forwarded_packets + self.dropped_packets

        if total > 0:

            success = 100.0 * self.forwarded_packets / total

            print()

            print(f"Forward Success   : {success:.2f} %")

        print()

    #####################################################################

    def reset_statistics(self):

        self.forwarded_packets = 0
        self.dropped_packets = 0

        self.forwarded_bytes = 0
        self.dropped_bytes = 0
