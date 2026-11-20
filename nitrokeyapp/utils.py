import functools
import importlib.util
import logging
import os
import sys
from typing import TYPE_CHECKING, Optional

from nitrokey.trussed import Transport, TrussedDevice, recommended_transport
from nitrokey.trussed._connection.ctaphid import CtapHidConnection

if TYPE_CHECKING:
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import QWidget

    from nitrokeyapp.device_data import DeviceData

NITROKEY_FORCE_CCID = "NITROKEY_FORCE_CCID"
NITROKEY_FORCE_CTAPHID = "NITROKEY_FORCE_CTAPHID"
NKAPP_THEME = "NKAPP_THEME"

logger = logging.getLogger(__name__)


@functools.cache
def forced_color_scheme() -> Optional["Qt.ColorScheme"]:
    """Color scheme enforced via NKAPP_THEME=dark|light, or None for auto detection."""
    value = os.environ.get(NKAPP_THEME, "").strip().lower()
    if not value:
        return None

    from PySide6.QtCore import Qt

    if value == "dark":
        return Qt.ColorScheme.Dark
    if value == "light":
        return Qt.ColorScheme.Light
    logger.warning(f"{NKAPP_THEME} must be 'dark' or 'light', got {value!r}; using auto detection")
    return None


def resolved_color_scheme() -> "Qt.ColorScheme":
    """The color scheme to render with: NKAPP_THEME if set, else auto detection."""
    from PySide6.QtCore import Qt
    from PySide6.QtGui import QPalette
    from PySide6.QtWidgets import QApplication

    forced = forced_color_scheme()
    if forced is not None:
        return forced

    app = QApplication.instance()
    if not isinstance(app, QApplication):
        return Qt.ColorScheme.Light

    scheme = app.styleHints().colorScheme()
    if scheme != Qt.ColorScheme.Unknown:
        return scheme

    palette = app.palette()
    window = palette.color(QPalette.ColorRole.Window)
    text = palette.color(QPalette.ColorRole.WindowText)
    return Qt.ColorScheme.Dark if window.lightness() < text.lightness() else Qt.ColorScheme.Light


def get_transport() -> Transport:
    if os.environ.get(NITROKEY_FORCE_CTAPHID):
        if os.environ.get(NITROKEY_FORCE_CCID):
            logger.warning(
                f"Both {NITROKEY_FORCE_CTAPHID} and {NITROKEY_FORCE_CCID} are set; "
                f"{NITROKEY_FORCE_CTAPHID} takes priority"
            )
        return Transport.CTAPHID
    if os.environ.get(NITROKEY_FORCE_CCID):
        return Transport.CCID
    return recommended_transport()


def check_ccid_config(parent: Optional["QWidget"] = None) -> None:
    if os.environ.get(NITROKEY_FORCE_CCID):
        if importlib.util.find_spec("smartcard") is None:
            message = "NITROKEY_FORCE_CCID is set but pyscard is not installed"
            logger.warning(message)
            sys.stderr.write(f"WARNING: {message}\n")

            from PySide6.QtWidgets import QMessageBox

            QMessageBox.warning(
                parent, "Missing Dependency", f"{message}.\nPlease install it to use CCID mode."
            )


def instantiate_device_on_new_channel_hid(data: "DeviceData") -> "DeviceData":
    from nitrokeyapp.device_data import DeviceData

    assert isinstance(data._device, TrussedDevice)
    assert isinstance(data._device.connection, CtapHidConnection)
    data._device.connection.device._connection.close()
    devices = DeviceData.list()  # Internally calls INIT which creates new channel
    for d in devices:
        if data._uuid == d._device.uuid():
            return d
    return data  # Try with exisitng if device was not found in search. This should never hit, just keeping here to satisfy the return type.
