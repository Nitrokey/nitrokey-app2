"""Experimental Nitrokey GUI Application - based on pynitrokey"""

import importlib.metadata
import pathlib
import sys

__version__ = importlib.metadata.version(__name__)


def get_theme_path() -> str:
    theme_path = pathlib.Path("ui/nitrokey_theme.xml")
    if hasattr(sys, "_MEIPASS"):
        theme_path = sys._MEIPASS / pathlib.Path("nitrokeyapp") / theme_path
    else:
        theme_path = pathlib.Path(__file__).parent / theme_path
    return str(theme_path)
