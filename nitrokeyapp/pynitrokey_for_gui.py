import logging
from typing import List, Type, TypeVar

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
        logger.info("path:", self.path)

    def list(self) -> List[Nitrokey3Base]:
        if self.path:
            # device = list_nk3()[0]
            device = open_nk3(self.path)
            if device:
                logger.info("device type:", type(device))
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
        logger.info("devices:", devices)
        return self._select_unique("Nitrokey 3", devices)

    def _await(self, name, ty: Type[T]) -> T:
        for t in Retries(10):
            # logger.debug(f"Searching {name} device ({t})")
            logger.info(f"Searching {name} device ({t})")
            devices = [
                device for device in list_nk3() if isinstance(device, ty)
            ]  # changed self.list() to list_nk3()
            if len(devices) == 0:
                # logger.debug(f"No {name} device found, continuing")
                logger.info(f"No {name} device found, continuing")
                continue
            if len(devices) > 1:
                raise CliException(f"Multiple {name} devices found")
            return devices[0]

        raise CliException(f"No {name} device found")

    def await_device(self) -> Nitrokey3Device:
        return self._await("Nitrokey 3", Nitrokey3Device)

    def await_bootloader(self) -> Nitrokey3Bootloader:
        return self._await("Nitrokey 3 bootloader", Nitrokey3Bootloader)


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
            logger.info("new pin does not match confirm-pin", "please try again!")
        try:
            # @fixme: move this (function) into own fido2-client-class
            # dev = nkfido2.find_all()[0]
            dev = nkfido2.find(device.device.serial_number)
            logger.info("fido2 device:", dev)
            # client = dev.client
            client_pin = ClientPin(dev.ctap2)
            client_pin.change_pin(old_pin, new_pin)
            logger.info("done - please use new pin to verify key")
            TrayNotification(
                "Nitrokey 3", "Successfully changed the PIN.", "Nitrokey 3 Change PIN"
            )
        except Exception as e:
            logger.info(
                "failed changing to new pin!",
                "did you set one already? or is it wrong?",
                e,
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
            logger.info("new pin does not match confirm-pin", "please try again!")
        try:
            # @fixme: move this (function) into own fido2-client-class
            # dev = nkfido2.find_all()[0]
            dev = nkfido2.find(device.device.serial_number)
            logger.info("fido2 device:", dev)
            # client = dev.client
            client_pin = ClientPin(dev.ctap2)
            client_pin.set_pin(new_pin)
            logger.info("done - please use new pin to verify key")
            TrayNotification(
                "Nitrokey 3", "Successfully set the PIN.", "Nitrokey 3 Set PIN"
            )
        except Exception as e:
            logger.info(
                "failed to set pin!", "did you set one already? or is it wrong?", e
            )
            TrayNotification(
                "Nitrokey 3",
                "Failed setting a pin! Did you set one already or is it wrong?",
                "Nitrokey 3 Change PIN",
            )


def nk3_update_helper(ctx: Nk3Context, progressBarUpdate, image, variant):
    try:
        nk3_update(ctx, progressBarUpdate, image, variant)
    except Exception as e:
        logger.info("Failed to update Nitrokey 3", e)
        TrayNotification(
            "Nitrokey 3", "Failed to update Nitrokey 3", "Nitrokey 3 Update"
        )


def nk3_update(ctx: Nk3Context, progressBarUpdate, image, variant) -> None:

    from nitrokeyapp.update import update

    update_version = update(ctx, progressBarUpdate, image, variant)
    
    with ctx.await_device() as device:
        version = device.version()
        progressBarUpdate.show()
        if version == update_version:
            logger.info(f"Successfully updated the firmware to version {version}.")
            TrayNotification(
                "Nitrokey 3",
                f"Successfully updated the firmware to version {version}.",
                "Nitrokey 3 Firmware Update",
            )
            progressBarUpdate.hide()
            progressBarUpdate.setValue(0)
        else:
            TrayNotification(
                "Nitrokey 3",
                f"The firmware update to {update_version} was successful, but the firmware is still reporting version {version}.",
                "Nitrokey 3 Firmware Update",
            )
            raise CliException(
                f"The firmware update to {update_version} was successful, but the firmware "
                f"is still reporting version {version}."
            )
