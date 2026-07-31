import time

from utils.logger import MeshLogger

from utils.config_manager import ConfigManager

from transport.zenoh_manager import ZenohManager


MeshLogger.initialize("AGV01")

cfg = ConfigManager()

cfg.load()

z = ZenohManager()

if not z.connect():

    print("Unable to connect")

    exit()


def callback(sample):

    print()

    print("Received")

    print(sample.key_expr)

    print(sample.payload.to_bytes().decode())

    print()


z.subscribe("/mesh/test", callback)

time.sleep(1)

z.publish(
    "/mesh/test",
    {
        "node": "AGV01",
        "message": "Hello Mesh"
    }
)

print("Published")

time.sleep(5)

z.close()
