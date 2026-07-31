#!/usr/bin/env python3

"""
===============================================================================

Mesh Control Plane

Topic Receiver

Subscribes to all deployment topics through their Zenoh transport keys.

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
        print("Starting Topic Receiver")
        print("======================================================")

        for topic in self.registry.all_topics().values():

            #
            # Convert ROS topic to Zenoh transport key
            #

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
