#!/usr/bin/env python3

"""
===============================================================================

Mesh Control Plane

Topic Receiver

Subscribes to local deployment topics and inter-device control plane topics (filtered/**)
so running mesh_node.py automatically initiates inter-system mesh transmission.

===============================================================================
"""

from mesh_transport.key_mapper import KeyMapper


class TopicReceiver:

    #####################################################################

    def __init__(self, peer_session, registry, callback):

        self.peer = peer_session

        self.registry = registry

        self.callback = callback

        self.mapper = KeyMapper()

        self.subscribers = []

    #####################################################################

    def start(self):

        print()

        print("======================================================")
        print("Starting Topic Receiver (Local & Inter-Device Control Plane)")
        print("======================================================")

        # 1. Subscribe to inter-device Control Plane heartbeats & telemetry
        hb_sub = self.peer.subscribe(
            "filtered/_mesh_heartbeat/*",
            self.callback
        )
        self.subscribers.append(hb_sub)

        wifi_sub = self.peer.subscribe(
            "filtered/_mesh_wifi_telemetry/*",
            self.callback
        )
        self.subscribers.append(wifi_sub)
        print("[SUBSCRIBE] Control Plane Heartbeat & Telemetry Channels")

        # 2. Subscribe to local ROS deployment topics
        for topic in self.registry.all_topics().values():

            zenoh_key = self.mapper.ros_to_zenoh(

                topic["name"]

            )

            subscriber = self.peer.subscribe(

                zenoh_key,

                self.callback

            )

            self.subscribers.append(subscriber)

            print(f"[SUBSCRIBE] {zenoh_key}")

        print()

        print(f"Total Subscribers : {len(self.subscribers)}")

        print()

    #####################################################################

    def stop(self):

        for subscriber in self.subscribers:

            subscriber.undeclare()

        self.subscribers.clear()

        print()

        print("[INFO] Topic Receiver stopped.")

        print()
