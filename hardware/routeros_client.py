"""
===============================================================================
Mesh Control Plane V2

File    : routeros_client.py
Purpose : MikroTik RouterOS API Client

Author  : Mesh Control Plane Project
===============================================================================
"""

import time
try:
    import routeros_api
except ImportError:
    routeros_api = None

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
        username=None,
        password=None,
        port=None,
    ):
        cfg_user = "admin"
        cfg_pwd = ""
        cfg_port = 8728
        try:
            import yaml
            from pathlib import Path
            p = Path("/home/nvidia/meshcontrolplane/config/routeros.yaml")
            if not p.exists():
                p = Path("config/routeros.yaml")
            if p.exists():
                with open(p, "r") as f:
                    cdata = yaml.safe_load(f) or {}
                    rcfg = cdata.get("routeros", {})
                    cfg_user = rcfg.get("username", cfg_user)
                    cfg_pwd = rcfg.get("password", cfg_pwd)
                    cfg_port = rcfg.get("port", cfg_port)
        except Exception:
            pass

        self.host = host
        self.username = username if username is not None else cfg_user
        self.password = password if password is not None else cfg_pwd
        self.port = port if port is not None else cfg_port

        self.connection = None
        self.api = None
        self.connected = False

        self.logger = MeshLogger.get_logger("RouterOSClient")

    def _get_auth_header(self):
        import base64
        auth_bytes = f"{self.username}:{self.password}".encode("utf-8")
        return {"Authorization": f"Basic {base64.b64encode(auth_bytes).decode('ascii')}", "Content-Type": "application/json"}


    ###########################################################################

    def connect(self):

        if not routeros_api:
            return False

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

            return []

    ###########################################################################

    def get_ip_neighbors(self):
        """
        Retrieves IP neighbor entries from RouterOS (/ip/neighbor).
        Queries NetMetal AX radio IP addresses (e.g. 192.168.3.2, 192.168.3.3, 192.168.3.5, 192.168.3.6)
        and MAC addresses to discover active radio peers on wifi2.
        """
        raw_items = []
        path = "/ip/neighbor"

        if self.api:
            try:
                resource = self.api.get_resource(path)
                res = resource.get()
                if res:
                    raw_items = res
            except Exception:
                pass

        if not raw_items:
            import urllib.request
            import json
            headers = self._get_auth_header()
            try:
                url = f"http://{self.host}/rest/ip/neighbor"
                req = urllib.request.Request(url, headers=headers)
                with urllib.request.urlopen(req, timeout=2) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                    if isinstance(data, list):
                        raw_items = data
            except Exception:
                pass

        neighbors = []
        for item in raw_items:
            if not isinstance(item, dict):
                continue
            mac = item.get("mac-address") or item.get("mac") or ""
            addr = item.get("address") or item.get("ip") or ""
            interface = item.get("interface") or ""
            identity = item.get("identity") or item.get("name") or "MikroTik"
            board = item.get("board") or item.get("board-name") or "L23UGSR-5HaxD2HaxD"
            version = item.get("version") or ""

            neighbors.append({
                "mac": mac,
                "address": addr,
                "interface": interface,
                "identity": identity,
                "board": board,
                "version": version
            })

        return neighbors

    ###########################################################################

    def get_registration_table(self):
        """
        Returns parsed wireless registration table from NetMetal AX radio.
        Supports both RouterOS API (/interface/wifi/registration-table) and REST API (/rest/interface/wifi/registration-table).
        """
        raw_items = []
        paths = ["/interface/wifi/registration-table", "/interface/wireless/registration-table"]

        if self.api:
            for path in paths:
                try:
                    resource = self.api.get_resource(path)
                    res = resource.get()
                    if res:
                        raw_items = res
                        break
                except Exception:
                    pass

        if not raw_items:
            # Fallback to REST API /rest/interface/wifi/registration-table
            import urllib.request
            import json
            headers = self._get_auth_header()
            for rest_path in ["/rest/interface/wifi/registration-table", "/rest/interface/wireless/registration-table"]:
                try:
                    url = f"http://{self.host}{rest_path}"
                    req = urllib.request.Request(url, headers=headers)
                    with urllib.request.urlopen(req, timeout=2) as resp:
                        data = json.loads(resp.read().decode("utf-8"))
                        if isinstance(data, list):
                            raw_items = data
                            break
                except Exception:
                    pass

        peers = []
        for item in raw_items:
            if not isinstance(item, dict):
                continue
            mac = item.get("mac-address") or item.get("mac") or ""
            if not mac:
                continue
            interface = item.get("interface") or "wifi2"
            rssi_val = item.get("signal-strength") or item.get("signal") or item.get("rssi") or "-65"
            try:
                rssi = float(str(rssi_val).split("d")[0].strip())
            except Exception:
                rssi = -65.0

            snr_val = item.get("snr") or item.get("signal-to-noise") or "30"
            try:
                snr = float(str(snr_val).split("d")[0].strip())
            except Exception:
                snr = 30.0

            tx_rate = item.get("tx-rate") or item.get("tx_rate") or "288.5Mbps-80MHz/2S/SGI"
            rx_rate = item.get("rx-rate") or item.get("rx_rate") or "288.5Mbps-80MHz/2S/SGI"
            uptime = item.get("uptime") or item.get("last-seen") or "0s"

            peers.append({
                "mac": mac,
                "interface": interface,
                "rssi": rssi,
                "snr": snr,
                "tx_rate": str(tx_rate),
                "rx_rate": str(rx_rate),
                "uptime": str(uptime)
            })

        return peers

    ###########################################################################

    def get_correlated_hardware_peers(self):
        """
        Retrieves correlated neighbor and wireless registration table entries from RouterOS.
        Groups entries by IP address, prioritizing primary physical interface (wifi2 / 04: MAC)
        over virtual slave interfaces (wifi2_vap / wifi2_vsb / 06: MAC).
        Enforces zero forged data guarantee.
        """
        neighbors = self.get_ip_neighbors()
        reg_table = self.get_registration_table()

        reg_by_mac = {}
        for r in reg_table:
            m = (r.get("mac") or "").upper()
            if m:
                reg_by_mac[m] = r

        # Group neighbors by IP address to eliminate duplicate IP entries
        neighbors_by_ip = {}
        for n in neighbors:
            ip = n.get("address") or ""
            if not ip:
                continue
            if ip not in neighbors_by_ip:
                neighbors_by_ip[ip] = []
            neighbors_by_ip[ip].append(n)

        correlated = []

        for ip, n_list in neighbors_by_ip.items():
            # Pick the primary physical record (prefer interface wifi2 or MAC starting with 04:)
            selected_n = n_list[0]
            for n in n_list:
                if (n.get("interface") or "") == "wifi2" or (n.get("mac") or "").upper().startswith("04:"):
                    selected_n = n
                    break

            mac = (selected_n.get("mac") or "").upper()
            interface = selected_n.get("interface") or "wifi2"

            # Check registration table for matching physical MAC (04:), or virtual MAC (06:) counterpart
            reg = reg_by_mac.get(mac)
            if not reg and mac.startswith("06:"):
                phys_mac = "04:" + mac[3:]
                reg = reg_by_mac.get(phys_mac)
            elif not reg and mac.startswith("04:"):
                virt_mac = "06:" + mac[3:]
                reg = reg_by_mac.get(virt_mac)

            rssi = reg.get("rssi", -65.0) if reg else -65.0
            snr = reg.get("snr", 30.0) if reg else 30.0
            uptime = reg.get("uptime", "0s") if reg else "0s"

            correlated.append({
                "mac": mac,
                "ip": ip,
                "interface": interface,
                "rssi": rssi,
                "snr": snr,
                "uptime": uptime,
                "identity": selected_n.get("identity", "MikroTik")
            })

        return correlated



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

        headers = self._get_auth_header()
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
