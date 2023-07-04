"""Experimental Nitrokey GUI Application - based on pynitrokey"""

import pathlib
import sys

__version_path__ = pathlib.Path(__file__).parent.resolve().absolute() / "VERSION"
__version__ = open(__version_path__).read().strip()


def get_theme_path() -> str:
    theme_path = pathlib.Path("ui/nitrokey_theme.xml")
    if hasattr(sys, "_MEIPASS"):
        theme_path = sys._MEIPASS / pathlib.Path("nitrokeyapp") / theme_path
    else:
        theme_path = pathlib.Path(__file__).parent / theme_path
    return str(theme_path)
