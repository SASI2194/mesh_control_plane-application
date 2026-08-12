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

        return []

    ###########################################################################

    def get_wifi_interfaces(self):
        """
        Retrieves detailed list of available and active WiFi interfaces
        from RouterOS v7 WiFi package (/interface/wifi).
        """
        paths = ["/interface/wifi", "/interface/wireless"]
        for path in paths:
            try:
                resource = self.api.get_resource(path)
                res = resource.get()
                if res:
                    interfaces = []
                    for item in res:
                        name = item.get("name") or item.get("default-name", "wifi")
                        master = item.get("master-interface", "")
                        mode = item.get("configuration.mode") or item.get("mode") or "AP"
                        ssid = item.get("configuration.ssid") or item.get("ssid") or ""
                        band = item.get("channel.band") or item.get("band") or "5GHz-ax"
                        freq = item.get("channel.frequency") or item.get("frequency") or "5180"
                        disabled = item.get("disabled") == "true" or "X" in item.get("flags", "")
                        running = item.get("running") == "true" or "R" in item.get("flags", "")

                        status_str = "ACTIVE & RUNNING" if running else ("DISABLED" if disabled else "INACTIVE")

                        interfaces.append({
                            "name": name,
                            "master_interface": master,
                            "mode": mode.upper(),
                            "ssid": ssid,
                            "band": band,
                            "freq": freq,
                            "disabled": disabled,
                            "running": running,
                            "status": status_str
                        })
                    return interfaces
            except Exception:
                continue
        return []

    def promote_to_master_ap(self, ssid="test_device"):
        """
        Reconfigures local NetMetal AX WiFi radio interfaces when this node is elected Master AP:
        - wifi2 (Physical 5GHz radio) -> Mode: AP, Disabled: false
        - wifi2_vap / wifi2_vsb (Virtual interface) -> Mode: STATION-BRIDGE, Disabled: false
        """
        paths = ["/interface/wifi", "/interface/wireless"]
        for path in paths:
            try:
                resource = self.api.get_resource(path)
                res = resource.get()
                if res:
                    for item in res:
                        item_id = item.get(".id")
                        name = item.get("name") or item.get("default-name", "")
                        if name == "wifi2":
                            try:
                                resource.set(id=item_id, disabled="false", mode="ap")
                            except Exception:
                                resource.set(id=item_id, disabled="false")
                            self.logger.info(f"Promoted wifi2 to AP mode on RouterOS ({self.host})")
                        elif name in ["wifi2_vap", "wifi2_vsb"]:
                            try:
                                resource.set(id=item_id, disabled="false", mode="station-bridge")
                            except Exception:
                                resource.set(id=item_id, disabled="false")
                            self.logger.info(f"Switched {name} to STATION-BRIDGE mode on RouterOS ({self.host})")
                    return True
            except Exception as e:
                self.logger.error(f"Failed to promote RouterOS interfaces to Master AP: {e}")
                continue
        return False

    def demote_to_station_bridge(self, ssid="test_device"):
        """
        Reconfigures local NetMetal AX WiFi radio interfaces when this node is a client/slave:
        - wifi2 (Physical 5GHz radio) -> Mode: STATION-BRIDGE, Disabled: false
        - wifi2_vap / wifi2_vsb (Virtual interface) -> Mode: AP, Disabled: false
        """
        paths = ["/interface/wifi", "/interface/wireless"]
        for path in paths:
            try:
                resource = self.api.get_resource(path)
                res = resource.get()
                if res:
                    for item in res:
                        item_id = item.get(".id")
                        name = item.get("name") or item.get("default-name", "")
                        if name == "wifi2":
                            try:
                                resource.set(id=item_id, disabled="false", mode="station-bridge")
                            except Exception:
                                resource.set(id=item_id, disabled="false")
                            self.logger.info(f"Set wifi2 to STATION-BRIDGE mode on RouterOS ({self.host})")
                        elif name in ["wifi2_vap", "wifi2_vsb"]:
                            try:
                                resource.set(id=item_id, disabled="false", mode="ap")
                            except Exception:
                                resource.set(id=item_id, disabled="false")
                            self.logger.info(f"Set {name} to AP mode on RouterOS ({self.host})")
                    return True
            except Exception as e:
                self.logger.error(f"Failed to set RouterOS interfaces to station-bridge mode: {e}")
                continue
        return False
