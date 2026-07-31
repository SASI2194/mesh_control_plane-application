#!/usr/bin/env python3

"""
===============================================================================

Mesh Control Plane

Verification Statistics

Maintains runtime statistics for every forwarded topic.

===============================================================================
"""

import time


class TopicStatistics:

    ###########################################################################

    def __init__(self, topic):

        self.topic = topic

        #
        # Packet counters
        #

        self.packet_count = 0

        self.byte_count = 0

        #
        # Timing
        #

        self.first_packet = None

        self.last_packet = None

        #
        # Rates
        #

        self.mbps = 0.0

        self.mbps_megabytes = 0.0

        self.packet_rate = 0.0

        #
        # Packet size
        #

        self.average_packet_size = 0.0

        #
        # Jitter
        #

        self.last_arrival = None

        self.average_interval = 0.0

        self.jitter = 0.0

        self.interval_sum = 0.0

        self.interval_samples = 0

    ###########################################################################

    def update(self, payload_size):

        now = time.time()

        #
        # First packet
        #

        if self.first_packet is None:

            self.first_packet = now

            self.last_arrival = now

        #
        # Timing
        #

        self.last_packet = now

        #
        # Counters
        #

        self.packet_count += 1

        self.byte_count += payload_size

        #
        # Average packet size
        #

        self.average_packet_size = (

            self.byte_count / self.packet_count

        )

        #
        # Interval
        #

        interval = now - self.last_arrival

        self.last_arrival = now

        if self.packet_count > 1:

            self.interval_sum += interval

            self.interval_samples += 1

            self.average_interval = (

                self.interval_sum /

                self.interval_samples

            )

            self.jitter = abs(

                interval -

                self.average_interval

            )

        #
        # Throughput
        #

        duration = self.last_packet - self.first_packet

        if duration <= 0:

            return

        bytes_per_second = self.byte_count / duration

        self.mbps_megabytes = bytes_per_second / 1e6

        self.mbps = (

            bytes_per_second *

            8.0 /

            1e6

        )

        self.packet_rate = (

            self.packet_count /

            duration

        )

    ###########################################################################

    def loss_percentage(self, expected_rate=25.0):

        if self.first_packet is None:

            return 0.0

        duration = self.last_packet - self.first_packet

        expected_packets = duration * expected_rate

        if expected_packets <= 0:

            return 0.0

        loss = (

            expected_packets -

            self.packet_count

        )

        if loss < 0:

            loss = 0

        return 100.0 * loss / expected_packets

    ###########################################################################

    def summary(self):

        return {

            "topic": self.topic,

            "packets": self.packet_count,

            "bytes": self.byte_count,

            "mbps": self.mbps,

            "MBps": self.mbps_megabytes,

            "pps": self.packet_rate,

            "avg_packet": self.average_packet_size,

            "loss": self.loss_percentage(),

            "jitter": self.jitter

        }


###############################################################################


class StatisticsDatabase:

    ###########################################################################

    def __init__(self):

        self.database = {}

    ###########################################################################

    def update(self, topic, payload):

        if topic not in self.database:

            self.database[topic] = TopicStatistics(topic)

        self.database[topic].update(

            len(payload)

        )

    ###########################################################################

    def topics(self):

        return sorted(

            self.database.keys()

        )

    ###########################################################################

    def statistics(self, topic):

        return self.database[topic].summary()

    ###########################################################################

    def total_packets(self):

        total = 0

        for topic in self.database.values():

            total += topic.packet_count

        return total

    ###########################################################################

    def total_bytes(self):

        total = 0

        for topic in self.database.values():

            total += topic.byte_count

        return total

    ###########################################################################

    def total_bandwidth(self):

        total = 0

        for topic in self.database.values():

            total += topic.mbps

        return total

    ###########################################################################

    def reset(self):

        self.database.clear()
