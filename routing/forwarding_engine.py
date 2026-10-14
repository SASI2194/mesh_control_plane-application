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

    def __init__(self, session, my_ip: str = "127.0.0.1", device_ns: str = None):

        #
        # Zenoh publishing session
        #

        self.session = session
        self.my_ip = my_ip
        self.device_ns = device_ns  # Local device namespace e.g. "ugv_01"

        #
        # Statistics
        #

        self.forwarded_packets = 0
        self.dropped_packets = 0

        self.forwarded_bytes = 0
        self.dropped_bytes = 0

    #####################################################################

    def _format_key(self, ros_topic: str) -> str:
        topic_name = ros_topic.lstrip("/")
        if topic_name.startswith("filtered/"):
            return topic_name
        if topic_name.startswith("55/"):
            return f"filtered/{topic_name}"
        return f"filtered/55/{topic_name}"

    def _format_ns_key(self, ros_topic: str) -> str:
        """Returns the device-namespaced Zenoh key (filtered/55/{dev_ns}/{clean_topic})."""
        if not self.device_ns:
            return self._format_key(ros_topic)
        topic_clean = ros_topic.lstrip("/")
        # Already namespaced — do not double-prefix
        if topic_clean.startswith(f"{self.device_ns}/"):
            return f"filtered/55/{topic_clean}"
        return f"filtered/55/{self.device_ns}/{topic_clean}"

    def _all_keys_for(self, ros_topic: str):
        """Returns the set of Zenoh keys to check/publish for this topic (namespaced + global)."""
        primary = self._format_key(ros_topic)
        keys = [primary]
        if self.device_ns:
            ns_key = self._format_ns_key(ros_topic)
            if ns_key != primary and ns_key not in keys:
                keys.append(ns_key)
        return keys

    def has_subscribers(self, ros_topic: str) -> bool:
        """Returns True if any remote subscriber exists on the namespaced OR global Zenoh key."""
        if hasattr(self.session, "has_matching_subscribers"):
            for key in self._all_keys_for(ros_topic):
                if self.session.has_matching_subscribers(key):
                    return True
            return False
        return True

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
        # Format Zenoh Key with Domain ID 55
        #################################################################

        output_key = self._format_key(sample.key)

        #################################################################
        # Demand-Driven Check: Skip egress if zero remote subscribers match
        # on EITHER the namespaced key OR the global (unnamespaced) key.
        # Exempt latched state topics and system transform infrastructure topics.
        #################################################################

        is_exempt = any(k in sample.key for k in ["robot_description", "tf_static", "tf", "map", "map_metadata", "clock", "rosout", "parameter_events"])

        # Collect all Zenoh keys to attempt publishing (namespaced + global)
        all_candidate_keys = self._all_keys_for(sample.key)
        # Also add tf-specific global mirrors as before
        for cand_key in list(all_candidate_keys):
            if "tf_static" in cand_key and "filtered/55/tf_static" not in all_candidate_keys:
                all_candidate_keys.append("filtered/55/tf_static")
            elif "/tf" in cand_key and not "tf_static" in cand_key and "filtered/55/tf" not in all_candidate_keys:
                all_candidate_keys.append("filtered/55/tf")

        if not is_exempt and hasattr(self.session, "has_matching_subscribers"):
            # Determine which candidate keys actually have remote subscribers
            keys_with_subs = [k for k in all_candidate_keys if self.session.has_matching_subscribers(k)]
            if not keys_with_subs:
                self.dropped_packets += 1
                self.dropped_bytes += len(sample.payload)
                return
            # Only publish to keys that have live subscribers
            keys_to_publish = keys_with_subs
        else:
            keys_to_publish = [output_key]

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

        #################################################################
        # Publish to all active subscriber keys
        #################################################################

        try:
            for pub_key in keys_to_publish:
                self.session.publish(
                    pub_key,
                    packed_payload
                )

            self.forwarded_packets += 1
            self.forwarded_bytes += len(sample.payload)
            print(f"[FORWARD] {output_key} -> {keys_to_publish} (Seq #{sample.sequence_number})")

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
