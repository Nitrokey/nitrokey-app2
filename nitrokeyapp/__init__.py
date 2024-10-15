"""Experimental Nitrokey GUI Application - based on the Nitrokey Python SDK"""

import importlib.metadata
import pathlib
import sys

try:
    __version__ = importlib.metadata.version(__name__)
except Exception:
    __version__ = "dev-version"
