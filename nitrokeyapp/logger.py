import logging
import logging.handlers
import os
import platform
import shutil
import sys
import tempfile
from collections.abc import Generator
from contextlib import contextmanager
from datetime import datetime
from importlib.metadata import version as package_version
from pathlib import Path

from PySide6.QtWidgets import QFileDialog, QWidget

logger = logging.getLogger(__name__)

log_to_console = "NKAPP_LOG" in os.environ

LOG_FILE_NAME = "nitrokey-app2.log"
LOG_FILE_BACKUP_COUNT = 9


@contextmanager
def init_logging() -> Generator[str, None, None]:
    log_file = Path(tempfile.gettempdir()) / LOG_FILE_NAME
    log_format = "%(relativeCreated)-8d %(levelname)6s %(name)10s %(message)s"

    try:
        handler = logging.handlers.RotatingFileHandler(
            filename=log_file, backupCount=LOG_FILE_BACKUP_COUNT, delay=True, encoding="utf-8"
        )
        try:
            handler.doRollover()
        except OSError:
            pass

        try:
            os.close(os.open(log_file, os.O_CREAT | os.O_WRONLY, 0o600))
        except OSError:
            pass

        console_handler = logging.StreamHandler(sys.stdout)

        handlers = [handler]
        if log_to_console:
            handlers.append(console_handler)  # type: ignore

        logging.basicConfig(format=log_format, level=logging.DEBUG, handlers=handlers)

        yield str(log_file)
    finally:
        logging.shutdown()


def log_environment() -> None:
    logger.info(f"Timestamp: {datetime.now()}")
    logger.info(f"OS: {platform.uname()}")
    logger.info(f"Python version: {platform.python_version()}")
    pymodules = ["nitrokeyapp", "nitrokey", "cryptography", "ecdsa", "fido2"]
    for x in pymodules:
        try:
            logger.info(f"{x} version: {package_version(x)}")
        except Exception:
            logger.info(f"{x} version: n/a")


def save_log(log_file: str, parent: QWidget) -> None:
    path, _ = QFileDialog.getSaveFileName(parent, "Save Log File")
    if path:
        root_logger = logging.getLogger()
        for handler in root_logger.handlers:
            handler.flush()
        try:
            shutil.copyfile(log_file, path)
        except OSError as e:
            logger.error(f"failed to save the logfile: {e}")
