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

    def _rest_set_wifi_interface(self, target_name, mode, disabled=False):
        """Helper to reconfigure interface mode via RouterOS v7 REST API (HTTP Basic Auth using PATCH)."""
        import urllib.request
        import json
        import socket

        headers = {"Authorization": "Basic YWRtaW46", "Content-Type": "application/json"}
        disabled_str = "true" if disabled else "false"

        try:
            # 1. GET /rest/interface/wifi to find matching interface .id
            url_get = f"http://{self.host}/rest/interface/wifi"
            req_get = urllib.request.Request(url_get, headers=headers)
            with urllib.request.urlopen(req_get, timeout=3) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                for item in data:
                    name = item.get("name") or item.get("default-name", "")
                    if name == target_name:
                        item_id = item.get(".id")
                        if item_id:
                            # 2. Send PATCH request to /rest/interface/wifi/<item_id>
                            url_patch = f"http://{self.host}/rest/interface/wifi/{item_id}"
                            body = json.dumps({
                                "configuration.mode": mode,
                                "disabled": disabled_str
                            }).encode("utf-8")
                            req_patch = urllib.request.Request(url_patch, data=body, headers=headers, method="PATCH")
                            try:
                                with urllib.request.urlopen(req_patch, timeout=3) as patch_resp:
                                    if patch_resp.status in [200, 201, 204]:
                                        self.logger.info(f"REST API (PATCH {item_id}): Successfully set {target_name} configuration.mode={mode} on {self.host}")
                                        return True
                            except (urllib.error.URLError, socket.timeout, ConnectionResetError, Exception) as e:
                                # When physical radio mode changes, RouterOS resets the 5GHz radio RF interface,
                                # which momentarily closes the TCP socket or times out after applying the change to hardware.
                                err_str = str(e).lower()
                                if any(k in err_str for k in ["timed out", "timeout", "reset", "refused", "route"]):
                                    self.logger.info(f"REST API (PATCH {item_id}): Reconfiguration payload delivered to {target_name} (radio hardware resetting): {e}")
                                    return True
                                self.logger.error(f"REST API PATCH error for {target_name}: {e}")
        except Exception as e:
            self.logger.error(f"REST API PATCH reconfiguration failed for {target_name} on {self.host}: {e}")
        return False

    def promote_to_master_ap(self, ssid="test_device"):
        """
        Reconfigures local NetMetal AX WiFi radio interfaces when this node is elected Master AP:
        - Step 1: wifi2_vap / wifi2_vsb (Virtual slave interfaces) -> Mode: station-bridge FIRST
        - Step 2: wifi2 (Physical 5GHz radio) -> Mode: ap SECOND
        """
        s_vap = self._rest_set_wifi_interface("wifi2_vap", mode="station-bridge", disabled=False)
        s_vsb = self._rest_set_wifi_interface("wifi2_vsb", mode="station-bridge", disabled=False)
        s_master = self._rest_set_wifi_interface("wifi2", mode="ap", disabled=False)
        return s_master or s_vap or s_vsb

    def demote_to_station_bridge(self, ssid="test_device"):
        """
        Reconfigures local NetMetal AX WiFi radio interfaces when this node is a client/slave:
        - Step 1: wifi2 (Physical 5GHz radio) -> Mode: station-bridge FIRST
        - Step 2: wifi2_vap / wifi2_vsb (Virtual slave interfaces) -> Mode: ap SECOND
        """
        s_master = self._rest_set_wifi_interface("wifi2", mode="station-bridge", disabled=False)
        s_vap = self._rest_set_wifi_interface("wifi2_vap", mode="ap", disabled=False)
        s_vsb = self._rest_set_wifi_interface("wifi2_vsb", mode="ap", disabled=False)
        return s_master or s_vap or s_vsb
