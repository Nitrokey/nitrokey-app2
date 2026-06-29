import logging
import os
import sys
from typing import TYPE_CHECKING, Optional

from nitrokey.trussed import HAS_CCID_SUPPORT, Transport, recommended_transport

if TYPE_CHECKING:
    from PySide6.QtWidgets import QWidget

logger = logging.getLogger(__name__)


def is_ctaphid_available() -> bool:
    if sys.platform == "win32" or sys.platform == "cygwin":
        try:
            return ctypes.windll.shell32.IsUserAnAdmin()
        except Exception:
            pass
    return True


def get_transport() -> Transport:
    force_ccid = os.environ.get("NITROKEY_FORCE_CCID")
    transport = os.environ.get("NITROKEY_TRANSPORT")
    if force_ccid:
        return Transport.CCID
    elif transport:
        return Transport.from_str(transport)
    else:
        return recommended_transport()


def check_ccid_config(parent: Optional["QWidget"] = None) -> None:
    transport = get_transport()
    if transport == Transport.CCID:
        if not HAS_CCID_SUPPORT:
            message = "CCID transport is selected but pyscard is not installed"
            logger.warning(message)
            sys.stderr.write(f"WARNING: {message}\n")

            from PySide6.QtWidgets import QMessageBox

            QMessageBox.warning(
                parent, "Missing Dependency", f"{message}.\nPlease install it to use CCID mode."
            )
