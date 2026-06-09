import importlib.util
import logging
import os
import sys
from typing import TYPE_CHECKING, Optional

from nitrokey.trussed import should_default_ccid

if TYPE_CHECKING:
    from PySide6.QtWidgets import QWidget

NITROKEY_FORCE_CCID = "NITROKEY_FORCE_CCID"

logger = logging.getLogger(__name__)


def should_use_ccid() -> bool:
    force_ccid = os.environ.get(NITROKEY_FORCE_CCID)
    if force_ccid:
        return True
    else:
        return should_default_ccid()


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
