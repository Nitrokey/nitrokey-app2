import importlib.util
import logging
import os
import sys
from typing import TYPE_CHECKING, Optional

from nitrokey.trussed import should_default_ccid

if TYPE_CHECKING:
    from PySide6.QtWidgets import QWidget

NITROKEY_FORCE_CCID = "NITROKEY_FORCE_CCID"
NITROKEY_FORCE_CTAPHID = "NITROKEY_FORCE_CTAPHID"

logger = logging.getLogger(__name__)


def should_use_ccid() -> bool:
    if os.environ.get(NITROKEY_FORCE_CTAPHID):
        if os.environ.get(NITROKEY_FORCE_CCID):
            logger.warning(
                f"Both {NITROKEY_FORCE_CTAPHID} and {NITROKEY_FORCE_CCID} are set; "
                f"{NITROKEY_FORCE_CTAPHID} takes priority"
            )
        return False
    if os.environ.get(NITROKEY_FORCE_CCID):
        return True
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
