import logging
import platform
import tempfile
from datetime import datetime
from importlib.metadata import version as package_version


def init_logging():

    logger = logging.getLogger(__name__)
    LOG_FN = tempfile.NamedTemporaryFile(prefix="nitrokey-app2.log.").name
    LOG_FORMAT = "%(relativeCreated)-8d %(levelname)6s %(name)10s %(message)s"
    handler = logging.FileHandler(filename=LOG_FN, delay=True, encoding="utf-8")
    logging.basicConfig(format=LOG_FORMAT, level=logging.DEBUG, handlers=[handler])

    logger.info(f"Timestamp: {datetime.now()}")
    logger.info(f"OS: {platform.uname()}")
    logger.info(f"Python version: {platform.python_version()}")
    pymodules = [
        "pynitrokey",
        "cryptography",
        "ecdsa",
        "fido2",
        "pyusb",
        "spsdk",
    ]
    for x in pymodules:
        logger.info(f"{x} version: {package_version(x)}")
