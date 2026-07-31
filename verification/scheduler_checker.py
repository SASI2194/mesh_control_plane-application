#!/usr/bin/env python3

"""
===============================================================================

Mesh Control Plane

Verification Framework

Scheduler Checker

Verifies that the topics received over the mesh exactly match the topics
selected by the scheduler.

===============================================================================
"""


class SchedulerChecker:

    ###########################################################################

    def __init__(self, registry, scheduler):

        self.registry = registry
        self.scheduler = scheduler

    ###########################################################################

    def expected_topics(self):

        """
        Scheduler allowed topics.
        """

        return set(

            self.scheduler.allowed_topics

        )

    ###########################################################################

    def received_topics(self, statistics):

        """
        Convert

            filtered/topic_01

        into

            /topic_01
        """

        topics = set()

        for topic in statistics.topics():

            if topic.startswith("filtered/"):

                ros_topic = "/" + topic.replace(

                    "filtered/", ""

                )

                topics.add(

                    ros_topic

                )

        return topics

    ###########################################################################

    def verify(self, statistics):

        expected = self.expected_topics()

        received = self.received_topics(

            statistics

        )

        missing = sorted(

            expected -

            received

        )

        unexpected = sorted(

            received -

            expected

        )

        return {

            "expected": sorted(expected),

            "received": sorted(received),

            "missing": missing,

            "unexpected": unexpected,

            "pass": len(missing) == 0 and len(unexpected) == 0

        }

    ###########################################################################

    def print_report(self, statistics):

        report = self.verify(

            statistics

        )

        print()

        print("==========================================================")
        print("Scheduler Verification")
        print("==========================================================")

        print()

        print("Expected Topics")

        print("-------------------------")

        for topic in report["expected"]:

            print("✓", topic)

        print()

        print("Received Topics")

        print("-------------------------")

        for topic in report["received"]:

            print("✓", topic)

        print()

        if report["missing"]:

            print("Missing Topics")

            print("-------------------------")

            for topic in report["missing"]:

                print("✗", topic)

            print()

        if report["unexpected"]:

            print("Unexpected Topics")

            print("-------------------------")

            for topic in report["unexpected"]:

                print("✗", topic)

            print()

        print("------------------------------------------")

        if report["pass"]:

            print("Scheduler Verification : PASS")

        else:

            print("Scheduler Verification : FAIL")

        print()
