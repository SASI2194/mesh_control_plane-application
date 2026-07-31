"""
===============================================================================

Mesh Control Plane

Admission Controller

Final decision maker.

===============================================================================
"""


class AdmissionController:

    def __init__(self, scheduler):

        self.scheduler = scheduler

    #####################################################################

    def evaluate(self, topic):

        """
        Returns True if the topic is currently
        allowed onto the mesh.
        """

        return self.scheduler.allowed(topic)
