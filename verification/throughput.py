#!/usr/bin/env python3

"""
===============================================================================

Mesh Control Plane

Verification Framework

Throughput Calculator

Purpose

    • Compare expected bandwidth with measured bandwidth
    • Compute scheduler accuracy
    • Compute overall utilization
    • Produce verification summaries

===============================================================================
"""


class ThroughputCalculator:

    ###########################################################################

    def __init__(self):

        #
        # Scheduler bandwidth
        #

        self.expected_bandwidth = 0.0

        #
        # Actual measured bandwidth
        #

        self.measured_bandwidth = 0.0

    ###########################################################################

    def set_expected(self, bandwidth):

        self.expected_bandwidth = float(bandwidth)

    ###########################################################################

    def update(self, statistics_db):

        self.measured_bandwidth = statistics_db.total_bandwidth()

    ###########################################################################

    def difference(self):

        return abs(

            self.expected_bandwidth -

            self.measured_bandwidth

        )

    ###########################################################################

    def utilization(self):

        if self.expected_bandwidth <= 0:

            return 0.0

        return (

            self.measured_bandwidth *

            100.0 /

            self.expected_bandwidth

        )

    ###########################################################################

    def scheduler_accuracy(self):

        if self.expected_bandwidth <= 0:

            return 0.0

        error = self.difference()

        accuracy = (

            100.0 -

            (error * 100.0 /

             self.expected_bandwidth)

        )

        if accuracy < 0:

            accuracy = 0.0

        return accuracy

    ###########################################################################

    def pass_fail(self, tolerance=5.0):

        """
        Pass if measured bandwidth
        is within tolerance (Mbps)
        """

        if self.difference() <= tolerance:

            return "PASS"

        return "FAIL"

    ###########################################################################

    def report(self):

        return {

            "expected": self.expected_bandwidth,

            "measured": self.measured_bandwidth,

            "difference": self.difference(),

            "utilization": self.utilization(),

            "accuracy": self.scheduler_accuracy(),

            "result": self.pass_fail()

        }

    ###########################################################################

    def print_report(self):

        report = self.report()

        print()

        print("=========================================================")
        print("Bandwidth Verification")
        print("=========================================================")

        print(f"Expected Bandwidth : {report['expected']:.2f} Mbps")

        print(f"Measured Bandwidth : {report['measured']:.2f} Mbps")

        print(f"Difference         : {report['difference']:.2f} Mbps")

        print()

        print(f"Utilization        : {report['utilization']:.2f} %")

        print(f"Scheduler Accuracy : {report['accuracy']:.2f} %")

        print()

        print(f"Verification       : {report['result']}")

        print()

###############################################################################


if __name__ == "__main__":

    from verification.statistics import StatisticsDatabase

    db = StatisticsDatabase()

    #
    # Example statistics
    #

    for _ in range(150):

        db.update(

            "filtered/topic_01",

            bytes(200040)

        )

    for _ in range(150):

        db.update(

            "filtered/topic_02",

            bytes(300040)

        )

    calc = ThroughputCalculator()

    calc.set_expected(100.0)

    calc.update(db)

    calc.print_report()
