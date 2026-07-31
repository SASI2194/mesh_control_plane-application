"""
===============================================================================
Mesh Control Plane V2

File    : logger.py
Purpose : Common logging utility
===============================================================================
"""

import logging
import os
from pathlib import Path

try:
    import colorlog
    COLOR_AVAILABLE = True
except ImportError:
    COLOR_AVAILABLE = False


class MeshLogger:

    _configured = False

    @staticmethod
    def initialize(node_id: str):

        if MeshLogger._configured:
            return

        log_directory = Path("logs")
        log_directory.mkdir(exist_ok=True)

        logfile = log_directory / f"{node_id}.log"

        root_logger = logging.getLogger()
        root_logger.setLevel(logging.INFO)

        root_logger.handlers.clear()

        formatter = logging.Formatter(
            "%(asctime)s | %(levelname)-8s | %(name)-20s | %(message)s"
        )

        file_handler = logging.FileHandler(logfile)

        file_handler.setFormatter(formatter)

        root_logger.addHandler(file_handler)

        console_handler = logging.StreamHandler()

        if COLOR_AVAILABLE:

            color_formatter = colorlog.ColoredFormatter(
                "%(log_color)s%(asctime)s | %(levelname)-8s | %(name)-20s | %(message)s",
                log_colors={
                    "DEBUG": "cyan",
                    "INFO": "green",
                    "WARNING": "yellow",
                    "ERROR": "red",
                    "CRITICAL": "bold_red",
                },
            )

            console_handler.setFormatter(color_formatter)

        else:

            console_handler.setFormatter(formatter)

        root_logger.addHandler(console_handler)

        MeshLogger._configured = True

    @staticmethod
    def get_logger(name: str):

        return logging.getLogger(name)
