"""
===============================================================================
Mesh Control Plane V2

File    : routeros_client.py
Purpose : MikroTik RouterOS API Client

Author  : Mesh Control Plane Project
===============================================================================
"""

import time
import routeros_api

from utils.logger import MeshLogger


class RouterOSClient:
    """
    RouterOS API Client

    Handles all communication between the AGX Orin and the
    locally connected MikroTik NetMetal AX.
    """

    def __init__(
        self,
        host="192.168.3.3",
        username="mesh",
        password="mesh123",
        port=8728,
    ):

        self.host = host
        self.username = username
        self.password = password
        self.port = port

        self.connection = None
        self.api = None
        self.connected = False

        self.logger = MeshLogger.get_logger("RouterOSClient")

    ###########################################################################

    def connect(self):

        try:

            pool = routeros_api.RouterOsApiPool(
                self.host,
                username=self.username,
                password=self.password,
                port=self.port,
                plaintext_login=True,
            )

            self.connection = pool
            self.api = pool.get_api()

            self.connected = True

            self.logger.info(
                f"Connected to RouterOS ({self.host})"
            )

            return True

        except Exception as e:

            self.connected = False

            self.logger.error(f"Connection failed : {e}")

            return False

    ###########################################################################

    def disconnect(self):

        try:

            if self.connection is not None:

                self.connection.disconnect()

        except Exception:

            pass

        self.connected = False

        self.logger.info("Disconnected from RouterOS")

    ###########################################################################

    def is_connected(self):

        return self.connected

    ###########################################################################

    def reconnect(self):

        self.disconnect()

        time.sleep(2)

        return self.connect()

    ###########################################################################

    def get_identity(self):

        try:

            resource = self.api.get_resource("/system/identity")

            return resource.get()

        except Exception as e:

            self.logger.error(e)

            return []

    ###########################################################################

    def get_system_resource(self):

        try:

            resource = self.api.get_resource("/system/resource")

            return resource.get()

        except Exception as e:

            self.logger.error(e)

            return []

    ###########################################################################

    def get_interfaces(self):

        try:

            resource = self.api.get_resource("/interface")

            return resource.get()

        except Exception as e:

            self.logger.error(e)

            return []

    ###########################################################################

    def get_ip_addresses(self):

        try:

            resource = self.api.get_resource("/ip/address")

            return resource.get()

        except Exception as e:

            self.logger.error(e)

            return []

    ###########################################################################

    def get_registration_table(self):

        """
        Returns wireless registration table.

        RouterOS v7 WiFi package
        """

        paths = [

            "/interface/wifi/registration-table",

            "/interface/wireless/registration-table",

        ]

        for path in paths:

            try:

                resource = self.api.get_resource(path)

                result = resource.get()

                if result is not None:

                    return result

            except Exception:

                continue

        return []

    ###########################################################################

    def ping(self, address, count=4):

        try:

            resource = self.api.get_binary_resource("/ping")

            return resource.call(

                "ping",

                {

                    "address": address,

                    "count": count,

                },

            )

        except Exception as e:

            self.logger.error(e)

            return None
