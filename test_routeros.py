from utils.logger import MeshLogger
from hardware.routeros_client import RouterOSClient

MeshLogger.initialize("AGV01")

radio = RouterOSClient()

if radio.connect():

    print("\nCONNECTED\n")

    print("Identity")

    print(radio.get_identity())

    print()

    print("System Resource")

    print(radio.get_system_resource())

    print()

    print("Interfaces")

    print(radio.get_interfaces())

    print()

    print("Registration Table")

    print(radio.get_registration_table())

    radio.disconnect()

else:

    print("Connection Failed")
