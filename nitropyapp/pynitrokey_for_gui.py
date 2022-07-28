from typing import List, Optional, Tuple, Type, TypeVar
import platform
# Nitrokey 3
from pynitrokey.cli.exceptions import CliException
from pynitrokey.helpers import Retries, local_print
from pynitrokey.nk3.base import Nitrokey3Base
from pynitrokey.nk3.exceptions import TimeoutException
from pynitrokey.nk3.device import BootMode, Nitrokey3Device
from pynitrokey.nk3 import list as list_nk3
from pynitrokey.nk3 import open as open_nk3
from pynitrokey.nk3.updates import get_repo
from pynitrokey.nk3.utils import Version
from pynitrokey.updates import OverwriteError
from pynitrokey.nk3.bootloader import (
    RKHT,
    FirmwareMetadata,
    Nitrokey3Bootloader,
    check_firmware_image,
)
from spsdk.mboot.exceptions import McuBootConnectionError
# tray icon
from tray_notification import TrayNotification

T = TypeVar("T", bound=Nitrokey3Base)

######## nk3 stuff
sum = 0   

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

# def nk3(ctx: click.Context, path=None):
#     """Interact with Nitrokey 3, see subcommands."""
#     ctx.obj = Context(path)

# alles nach pynitrokey???
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

def test(ctx, pin: Optional[str]):
    """Run some tests on all connected Nitrokey 3 dtevices."""
    from pynitrokey.cli.nk3.test import TestContext, log_devices, log_system, run_tests

    log_system()
    devices = ctx.list()

    if len(devices) == 0:
        log_devices()
        raise CliException("No connected Nitrokey 3 devices found")

    print(f"Found {len(devices)} Nitrokey 3 device(s):")
    for device in devices:
        print(f"- {device.name} at {device.path}")

    results = []
    test_ctx = TestContext(pin=pin)
    for device in devices:
        results.append(run_tests(test_ctx, device))

    n = len(devices)
    success = sum(results)
    failure = n - success
    print("")
    print(
        f"Summary: {n} device(s) tested, {success} successful, {failure} failed"
    )

    if failure > 0:
        print("")
        raise CliException(f"Test failed for {failure} device(s)")
def version(ctx: Nk3Context) -> None:
    """Query the firmware version of the device."""
    with ctx.connect_device() as device:
        version = device.version()
        local_print(version)

def wink(ctx: Nk3Context) -> None:
    """Send wink command to the device (blinks LED a few times)."""
    with ctx.connect_device() as device:
        device.wink()
def _download_latest_update(device: Nitrokey3Base):
    try:
        update = get_repo().get_latest_update()
        #logger.info(f"Latest firmware version: {update.tag}")
        print(f"Latest firmware version: {update.tag}")
    except Exception as e:
        raise CliException("Failed to find latest firmware update", e)

    try:
        release_version = Version.from_v_str(update.tag)

        if isinstance(device, Nitrokey3Device):
            current_version = device.version()
            #_print_download_warning(release_version, current_version)
        else:
            #_print_download_warning(release_version)
            print("relaseversion")
    except ValueError as e:
        #logger.warning("Failed to parse version from release tag", e)
        print(("Failed to parse version from release tag", e))

    try:
        #logger.info(f"Trying to download firmware update from URL: {update.url}")
        print((f"Trying to download firmware update from URL: {update.url}"))

        #bar = self.DownloadProgressBar(desc=update.tag)
        # qbar not shown (for now) maybe add it in the future?
        data = update.read(callback=update_qbar)
        #bar.close()

        return (release_version, data)
    except Exception as e:
        raise CliException(f"Failed to download latest firmware update {update.tag}", e)

def nk3_update(ctx: Nk3Context, progressBarUpdate, image: Optional[str]):
    """
    Update the firmware of the device using the given image.
    This command requires that exactly one Nitrokey 3 in bootloader or firmware mode is connected.
    The user is asked to confirm the operation before the update is started.  The Nitrokey 3 may
    not be removed during the update.  Also, additional Nitrokey 3 devices may not be connected
    during the update.
    If no firmware image is given, the latest firmware release is downloaded automatically.
    If the connected Nitrokey 3 device is in firmware mode, the user is prompted to touch the
    device’s button to confirm rebooting to bootloader mode.
    """

    #if experimental:
    "The --experimental switch is not required to run this command anymore and can be safely removed."
    print ("HIEEEEEER!!!",ctx.path)
    with ctx.connect() as device:
        progressBarUpdate.show()
        release_version = None
        if image:
            with open(image, "rb") as f:
                data = f.read()
        else:
            release_version, data = _download_latest_update(device)

        metadata = check_firmware_image(data)
        if release_version and release_version != metadata.version:
            raise CliException(
                f"The firmware image for the release {release_version} has the unexpected product "
                f"version {metadata.version}."
            )

        if isinstance(device, Nitrokey3Device):
            if not release_version:
                current_version = device.version()
                #_print_version_warning(metadata, current_version)
            #_print_update_warning()

            local_print("")
            _reboot_to_bootloader(device)
            local_print("")

            if platform.system() == "Darwin":
                # Currently there is an issue with device enumeration after reboot on macOS, see
                # <https://github.com/Nitrokey/pynitrokey/issues/145>.  To avoid this issue, we
                # cancel the command now and ask the user to run it again.
                local_print(
                    "Bootloader mode enabled. Please repeat this command to apply the update."
                )
                print("Darwin")

            exc = None
            for t in Retries(3):
                #logger.debug(f"Trying to connect to bootloader ({t})")
                print(f"Trying to connect to bootloader ({t})")
                try:
                    #time.sleep(1)
                    with ctx.await_bootloader() as bootloader:
                        _perform_update(bootloader, data)
                        print("worked")
                        #### qprogressbar
                        progressBarUpdate.setValue(100)
                        tray_successful_update = TrayNotification("Nitrokey 3", "Successfully updated your Nitrokey 3.","Successfully updated your Nitrokey 3.")
                        #self.sendmessage("Successfully updated your Nitrokey 3.")
                        progressBarUpdate.hide()
                        progressBarUpdate.setValue(0)
                    break
                except McuBootConnectionError as e:
                    #logger.debug("Received connection error", exc_info=True)
                    print("Received connection error", exc_info=True)
                    exc = e
            else:
                msgs = ["Failed to connect to Nitrokey 3 bootloader"]
                if platform.system() == "Linux":
                    msgs += ["Are the Nitrokey udev rules installed and active?"]
                raise CliException(*msgs, exc)
                print((*msgs, exc))
        elif isinstance(device, Nitrokey3Bootloader):
            #_print_version_warning(metadata)
            #_print_update_warning()
            _perform_update(device, data)
        else:
            raise CliException(f"Unexpected Nitrokey 3 device: {device}")
            print(f"Unexpected Nitrokey 3 device: {device}")
        local_print("")
        with ctx.await_device() as device:
            version = device.version()
            if version == metadata.version:
                local_print(f"Successfully updated the firmware to version {version}.")
                print(f"Successfully updated the firmware to version {version}.")
            else:
                raise CliException(
                    f"The firmware update to {metadata.version} was successful, but the firmware "
                    f"is still reporting version {version}."
                )
                print(f"The firmware update to {metadata.version} was successful, but the firmware "
                    f"is still reporting version {version}.")

def reboot(ctx: Nk3Context, bootloader: bool) -> None:
    """
    Reboot the key.
    Per default, the key will reboot into regular firmware mode.  If the --bootloader option
    is set, a key can boot from firmware mode to bootloader mode.  Booting into
    bootloader mode has to be confirmed by pressing the touch button.
    """
    with ctx.connect() as device:
        if bootloader:
            if isinstance(device, Nitrokey3Device):
                _reboot_to_bootloader(device)
            else:
                raise CliException(
                    "A Nitrokey 3 device in bootloader mode can only reboot into firmware mode.",
                    support_hint=False,
                )
        else:
            device.reboot()


def _reboot_to_bootloader(device: Nitrokey3Device) -> None:
    local_print(
        "Please press the touch button to reboot the device into bootloader mode ..."
    )
    tray_please_touch = TrayNotification("Nitrokey 3","Please touch the Nitrokey 3 to start the firmware update.","Please touch the Nitrokey 3 to start the firmware update.")
    #self.sendmessage("Please touch the Nitrokey 3 to start the firmware update.")
    try:
        device.reboot(BootMode.BOOTROM)
    except TimeoutException:
        raise CliException(
            "The reboot was not confirmed with the touch button.",
            support_hint=False,
        )

def _perform_update(device: Nitrokey3Bootloader, image: bytes) -> None:
    #logger.debug("Starting firmware update")
    result = device.update(image, callback=update_qbar)#bar.update_sum)
        
    #logger.debug(f"Firmware update finished with status {device.status}")

    if result:
        #logger.debug("Firmware update finished successfully")
        device.reboot()
    else:
        (code, message) = device.status
        raise CliException(f"Firmware update failed with status code {code}: {message}")
def update_qbar(n: int, total: int) -> None:
    global sum
    if n > sum:
        print(((sum)*100//total))    
        #self.progressBarUpdate.setValue(((sum)*100//total))        
        sum += n
