import rclpy

from utils.logger import MeshLogger

from ros_transport.ros_transport import RosTransport


MeshLogger.initialize("AGV01")

rclpy.init()

transport = RosTransport()


def callback(msg):

    print(msg.data)


transport.subscribe(
    "/mesh/test",
    callback
)

transport.publish(
    "/mesh/test",
    {
        "node": "AGV01",
        "hello": "world"
    }
)

rclpy.spin_once(
    transport,
    timeout_sec=1.0
)

transport.destroy_node()

rclpy.shutdown()
