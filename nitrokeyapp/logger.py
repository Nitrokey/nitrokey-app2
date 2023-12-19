import logging
import os
import platform
import shutil
import sys
from contextlib import contextmanager
from datetime import datetime
from importlib.metadata import version as package_version
from tempfile import NamedTemporaryFile
from typing import Generator

from PySide6.QtWidgets import QFileDialog, QWidget

logger = logging.getLogger(__name__)

log_to_console = "NKAPP_LOG" in os.environ


@contextmanager
def init_logging() -> Generator[str, None, None]:
    log_file = NamedTemporaryFile(prefix="nitrokey-app2.", suffix=".log", delete=False)
    log_format = "%(relativeCreated)-8d %(levelname)6s %(name)10s %(message)s"

    try:
        handler = logging.FileHandler(
            filename=log_file.name, delay=True, encoding="utf-8"
        )
        console_handler = logging.StreamHandler(sys.stdout)

        handlers = [handler]
        if log_to_console:
            handlers.append(console_handler)  # type: ignore

        logging.basicConfig(format=log_format, level=logging.DEBUG, handlers=handlers)

        yield log_file.name
    finally:
        logging.shutdown()


def log_environment() -> None:
    logger.info(f"Timestamp: {datetime.now()}")
    logger.info(f"OS: {platform.uname()}")
    logger.info(f"Python version: {platform.python_version()}")
    pymodules = [
        "nitrokeyapp",
        "pynitrokey",
        "cryptography",
        "ecdsa",
        "fido2",
        "pyusb",
        "spsdk",
    ]
    for x in pymodules:
        logger.info(f"{x} version: {package_version(x)}")


def save_log(log_file: str, parent: QWidget) -> None:
    path, _ = QFileDialog.getSaveFileName(parent, "Save Log File")
    if path:
        logger = logging.getLogger()
        for handler in logger.handlers:
            handler.flush()
        shutil.copyfile(log_file, path)
