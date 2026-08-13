"""
===============================================================================
Mesh Control Plane V2

File    : config_manager.py
Purpose : Loads and manages all Mesh configuration files.

Author  : Mesh Control Plane Project
===============================================================================
"""

from pathlib import Path
import yaml

from utils.logger import MeshLogger


class ConfigManager:
    """
    Singleton configuration manager.

    Loads all YAML configuration files only once.
    """

    _instance = None

    def __new__(cls):

        if cls._instance is None:

            cls._instance = super().__new__(cls)

            cls._instance.mesh = {}
            cls._instance.priorities = {}
            cls._instance.routing = {}
            cls._instance.failover = {}

            cls._instance.logger = MeshLogger.get_logger("ConfigManager")

        return cls._instance

    ###########################################################################

    def load(self):

        self.mesh = self._load_yaml("config/mesh.yaml")

        self.priorities = self._load_yaml("config/priorities.yaml")

        self.routing = self._load_yaml("config/routing.yaml")

        self.failover = self._load_yaml("config/failover.yaml")

        self.logger.info("Configuration loaded successfully.")

    ###########################################################################

    def _load_yaml(self, filename):

        file = Path(filename)

        if not file.exists():

            raise FileNotFoundError(f"Configuration file not found: {filename}")

        with open(file, "r") as stream:

            return yaml.safe_load(stream)

    ###########################################################################

    def get_mesh(self):

        return self.mesh

    ###########################################################################

    def get_priorities(self):

        return self.priorities

    ###########################################################################

    def get_routing(self):

        return self.routing

    ###########################################################################

    def get_failover(self):

        return self.failover

    ###########################################################################

    def get(self, section, key=None):

        tables = {

            "mesh": self.mesh,

            "priorities": self.priorities,

            "routing": self.routing,

            "failover": self.failover,

        }

        table = tables.get(section)

        if table is None:

            return None

        if key is None:

            return table

        return table.get(key)
