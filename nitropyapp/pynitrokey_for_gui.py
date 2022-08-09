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
from spsdk.mboot.exceptions import McuBootConnectionError
# tray icon
from tray_notification import TrayNotification

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

def nk3_update_helper(ctx: Nk3Context, progressBarUpdate, image, variant):
    try:
        nk3_update(ctx, progressBarUpdate, image, variant)
    except Exception as e:
        print("Failed to update Nitrokey 3", e)

def nk3_update(
    ctx: Nk3Context, progressBarUpdate, image, variant) -> None:
    """
    Update the firmware of the device using the given image.
    This command requires that exactly one Nitrokey 3 in bootloader or firmware mode is connected.
    The user is asked to confirm the operation before the update is started.  The Nitrokey 3 may
    not be removed during the update.  Also, additional Nitrokey 3 devices may not be connected
    during the update.
    If no firmware image is given, the latest firmware release is downloaded automatically.  If a
    firmware image is given and its name is changed so that the device variant can no longer be
    detected from the filename, it has to be set explictly with --variant.
    If the connected Nitrokey 3 device is in firmware mode, the user is prompted to touch the
    device’s button to confirm rebooting to bootloader mode.
    """

    from update import update

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