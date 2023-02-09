"""Experimental Nitrokey GUI Application - based on pynitrokey"""

import pathlib

__version_path__ = pathlib.Path(__file__).parent.resolve().absolute() / "VERSION"
__version__ = open(__version_path__).read().strip()
