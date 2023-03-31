import logging
from typing import Callable, List, Optional, Type, TypeVar

# for fido2 (change pin)
import pynitrokey.fido2 as nkfido2
from fido2.ctap2.pin import ClientPin

# Nitrokey 3
from pynitrokey.cli.exceptions import CliException
from pynitrokey.helpers import Retries
from pynitrokey.nk3 import list as list_nk3
from pynitrokey.nk3 import open as open_nk3
from pynitrokey.nk3.base import Nitrokey3Base
from pynitrokey.nk3.bootloader import Nitrokey3Bootloader
from pynitrokey.nk3.device import Nitrokey3Device

# tray icon
from nitrokeyapp.tray_notification import TrayNotification

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

T = TypeVar("T", bound=Nitrokey3Base)


class Nk3Context:
    def __init__(self, nk3_context: Nitrokey3Base) -> None:
        self.path = nk3_context
        logger.info(f"path: {self.path}")
        self.updating = False

    def list(self) -> List[Nitrokey3Base]:
        if self.path:
            # device = list_nk3()[0]
            device = open_nk3(self.path)
            if device:
                logger.info(f"device type: {type(device)}")
                return [device]

            else:
                return []

        else:
            return list_nk3()

    def _select_unique(self, name: str, devices: List[T]) -> T:
        if len(devices) == 0:
            msg = f"No {name} device found"
            if self.path:
                msg += f" at path {self.path}"
            raise CliException(msg)

        if len(devices) > 1:
            raise CliException(
                f"Multiple {name} devices found -- use the --path option to select one"
            )

        return devices[0]

    def connect(self) -> Nitrokey3Base:
        return self._select_unique("Nitrokey 3", self.list())

    def connect_device(self) -> Nitrokey3Device:
        devices = [
            device for device in self.list() if isinstance(device, Nitrokey3Device)
        ]
        logger.info(f"devices: {devices}")
        return self._select_unique("Nitrokey 3", devices)

    def _await(
        self,
        name: str,
        ty: Type[T],
        retries: int,
        callback: Optional[Callable[[int, int], None]] = None,
    ) -> T:
        for t in Retries(retries):
            logger.debug(f"Searching {name} device ({t})")
            devices = [device for device in list_nk3() if isinstance(device, ty)]
            if len(devices) == 0:
                if callback:
                    callback(int((t.i / retries) * 100), 100)
                logger.debug(f"No {name} device found, continuing")
                continue
            if len(devices) > 1:
                raise CliException(f"Multiple {name} devices found")
            if callback:
                callback(100, 100)
            return devices[0]

        raise CliException(f"No {name} device found")

    def await_device(
        self,
        retries: Optional[int] = 30,
        callback: Optional[Callable[[int, int], None]] = None,
    ) -> Nitrokey3Device:
        assert isinstance(retries, int)
        return self._await("Nitrokey 3", Nitrokey3Device, retries, callback)

    def await_bootloader(
        self,
        retries: Optional[int] = 30,
        callback: Optional[Callable[[int, int], None]] = None,
    ) -> Nitrokey3Bootloader:
        assert isinstance(retries, int)
        # mypy does not allow abstract types here, but this is still valid
        return self._await("Nitrokey 3 bootloader", Nitrokey3Bootloader, retries, callback)  # type: ignore


def list():
    """List all Nitrokey 3 devices."""
    logger.info(":: 'Nitrokey 3' keys")
    # device = Nitrokey3Device.list
    for device in list_nk3():
        uuid = device.uuid()
        if uuid:
            logger.info(f"{device.path}: {device.name} {device.uuid()}")
        else:
            logger.info(f"{device.path}: {device.name}")


def version(ctx: Nk3Context) -> None:
    """Query the firmware version of the device."""
    with ctx.connect_device() as device:
        version = device.version()
        logger.info(version)


def wink(ctx: Nk3Context) -> None:
    """Send wink command to the device (blinks LED a few times)."""
    with ctx.connect_device() as device:
        device.wink()


def change_pin(ctx: Nk3Context, old_pin, new_pin, confirm_pin):
    """Change pin of current device"""
    with ctx.connect_device() as device:
        if new_pin != confirm_pin:
            logger.info("new pin does not match confirm-pin. please try again!")
        try:
            # @fixme: move this (function) into own fido2-client-class
            # dev = nkfido2.find_all()[0]
            dev = nkfido2.find(device.device.serial_number)
            logger.info(f"fido2 device: {dev}")
            # client = dev.client
            client_pin = ClientPin(dev.ctap2)
            client_pin.change_pin(old_pin, new_pin)
            logger.info("done - please use new pin to verify key")
            TrayNotification(
                "Nitrokey 3", "Successfully changed the PIN.", "Nitrokey 3 Change PIN"
            )
        except Exception as e:
            logger.info(
                f"failed changing to new pin! did you set one already? or is it wrong? {e}"
            )
            TrayNotification(
                "Nitrokey 3",
                "Failed changing to new pin! Did you set one already or is it wrong?",
                "Nitrokey 3 Change PIN",
            )


def set_pin(ctx: Nk3Context, new_pin, confirm_pin):
    """Set pin of current device"""
    with ctx.connect_device() as device:

        if new_pin != confirm_pin:
            logger.info("new pin does not match confirm-pin please try again!")
            try:
                # @fixme: move this (function) into own fido2-client-class
                # dev = nkfido2.find_all()[0]
                dev = nkfido2.find(device.device.serial_number)
                logger.info(f"fido2 device:  {dev}")
                # client = dev.client
                client_pin = ClientPin(dev.ctap2)
                client_pin.set_pin(new_pin)
                logger.info("done - please use new pin to verify key")
                TrayNotification(
                    "Nitrokey 3", "Successfully set the PIN.", "Nitrokey 3 Set PIN"
                )
            except Exception as e:
                logger.info(
                    f"failed to set pin! did you set one already? or is it wrong? {e}"
                )
                TrayNotification(
                    "Nitrokey 3",
                    "Failed setting a pin! Did you set one already or is it wrong?",
                    "Nitrokey 3 Change PIN",
                )


def nk3_update_helper(
    ctx: Nk3Context,
    progressBarUpdate,
    progressBarDownload,
    progressBarFinalization,
    image,
    version,
    ignore_pynitrokey_version,
):
    try:
        nk3_update(
            ctx,
            progressBarUpdate,
            progressBarDownload,
            progressBarFinalization,
            image,
            version,
            ignore_pynitrokey_version,
        )
        logger.info("Successfully updated the Nitrokey 3")
        TrayNotification(
            "Nitrokey 3", "Successfully updated the Nitrokey 3", "Nitrokey 3 Update"
        )
    except Exception as e:
        logger.info(f"Failed to update Nitrokey 3 {e}")
        TrayNotification(
            "Nitrokey 3", "Failed to update Nitrokey 3", "Nitrokey 3 Update"
        )


def nk3_update(
    ctx: Nk3Context,
    progressBarUpdate,
    progressBarDownload,
    progressBarFinalization,
    image,
    version,
    ignore_pynitrokey_version,
) -> None:

    from nitrokeyapp.update import update

    ctx.updating = True
    update(
        ctx,
        progressBarUpdate,
        progressBarDownload,
        progressBarFinalization,
        image,
        version,
        ignore_pynitrokey_version,
    )
    ctx.updating = False
