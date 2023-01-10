from contextlib import contextmanager
from typing import List, Optional, Tuple, Type, TypeVar, Any, Callable, Iterator
import platform
# Nitrokey 3
from pynitrokey.cli.exceptions import CliException
from pynitrokey.helpers import Retries, local_print
from pynitrokey.nk3.base import Nitrokey3Base
from pynitrokey.nk3.exceptions import TimeoutException
from pynitrokey.nk3.device import BootMode, Nitrokey3Device
from pynitrokey.nk3 import list as list_nk3
from pynitrokey.nk3 import open as open_nk3
from pynitrokey.nk3.updates import Updater, UpdateUi, REPOSITORY, get_firmware_update
from pynitrokey.nk3.utils import Version
from pynitrokey.updates import OverwriteError
from pynitrokey.nk3.bootloader import Variant
from pynitrokey.nk3.bootloader import (
    Nitrokey3Bootloader,
    Variant,
    detect_variant,
    parse_firmware_image,
)
# for fido2 (change pin)
import pynitrokey.fido2 as nkfido2
import pynitrokey.fido2.operations
from fido2.cbor import dump_dict
from fido2.client import ClientError as Fido2ClientError
from fido2.ctap import CtapError
from fido2.ctap1 import ApduError
from fido2.ctap2 import Ctap2
from fido2.ctap2.pin import ClientPin

from spsdk.mboot.exceptions import McuBootConnectionError
# tray icon
from nitropyapp.tray_notification import TrayNotification

T = TypeVar("T", bound=Nitrokey3Base)

class Nk3Context:
    def __init__(self, nk3_context: Nitrokey3Base) -> None:
        self.path = nk3_context
        print(self.path)


    def list(self) -> List[Nitrokey3Base]:
        if self.path:
            #device = list_nk3()[0]
            device = open_nk3(self.path)
            if device:
                print("funzt")
                print(type(device))
                return [device]

            else:
                print("funzt nicht")
                return []

        else:
            print("list_nk3")
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
        print(devices)
        return self._select_unique("Nitrokey 3", devices)

    def _await(self, name, ty: Type[T]) -> T:
        for t in Retries(10):
            #logger.debug(f"Searching {name} device ({t})")
            print(f"Searching {name} device ({t})")
            devices = [device for device in list_nk3() if isinstance(device, ty)] # changed self.list() to list_nk3()
            if len(devices) == 0:
                #logger.debug(f"No {name} device found, continuing")
                print(f"No {name} device found, continuing")
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
    print(":: 'Nitrokey 3' keys")
    #device = Nitrokey3Device.list
    for device in list_nk3():
            uuid = device.uuid()
            if uuid:
                print(f"{device.path}: {device.name} {device.uuid():X}")
            else:
                print(f"{device.path}: {device.name}")

def version(ctx: Nk3Context) -> None:
    """Query the firmware version of the device."""
    with ctx.connect_device() as device:
        version = device.version()
        local_print(version)

def wink(ctx: Nk3Context) -> None:
    """Send wink command to the device (blinks LED a few times)."""
    with ctx.connect_device() as device:
        device.wink()

def change_pin(ctx: Nk3Context, old_pin, new_pin, confirm_pin):
    """Change pin of current device"""
    with ctx.connect_device() as device:

        if new_pin != confirm_pin:
            print(
                "new pin does not match confirm-pin",
                "please try again!"
            )
        try:
            # @fixme: move this (function) into own fido2-client-class
            #dev = nkfido2.find_all()[0]
            dev = nkfido2.find(device.device.serial_number)
            print(dev)
            client = dev.client
            client_pin = ClientPin(dev.ctap2)
            client_pin.change_pin(old_pin, new_pin)
            local_print("done - please use new pin to verify key")
            TrayNotification("Nitrokey 3", f"Successfully changed the PIN.","Nitrokey 3 Change PIN")
        except Exception as e:
            print(
                "failed changing to new pin!", "did you set one already? or is it wrong?", e
            )



def nk3_update_helper(ctx: Nk3Context, progressBarUpdate, image, variant):
    try:
        nk3_update(ctx, progressBarUpdate, image, variant)
    except Exception as e:
        print("Failed to update Nitrokey 3", e)

def nk3_update(
    ctx: Nk3Context, progressBarUpdate, image, variant) -> None:

    from nitropyapp.update import update

    update_version = update(ctx, progressBarUpdate ,image, variant)

    local_print("")
    with ctx.await_device() as device:
        version = device.version()
        progressBarUpdate.show()
        if version == update_version:
            local_print(f"Successfully updated the firmware to version {version}.")
            TrayNotification("Nitrokey 3", f"Successfully updated the firmware to version {version}.","Nitrokey 3 Firmware Update")
            progressBarUpdate.hide()
            progressBarUpdate.setValue(0)
        else:
            raise CliException(
                f"The firmware update to {update_version} was successful, but the firmware "
                f"is still reporting version {version}."
            )
