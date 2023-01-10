from typing import List, Optional, Tuple, Type, TypeVar, Any, Iterator, Callable
import platform
import logging
from contextlib import contextmanager

# Nitrokey 3
from pynitrokey.cli.exceptions import CliException
from pynitrokey.helpers import Retries, local_print, confirm
from pynitrokey.nk3.base import Nitrokey3Base
from pynitrokey.nk3.exceptions import TimeoutException
from pynitrokey.nk3.device import BootMode, Nitrokey3Device
from pynitrokey.nk3 import list as list_nk3
from pynitrokey.nk3 import open as open_nk3
from pynitrokey.nk3.updates import Updater, UpdateUi
from pynitrokey.nk3.utils import Version
from pynitrokey.updates import OverwriteError
from pynitrokey.nk3.bootloader import Variant
from pynitrokey.nk3.updates import Updater, UpdateUi

from PyQt5.Qt import QMessageBox

from nitropyapp.pynitrokey_for_gui import Nk3Context
# tray icon
from nitropyapp.tray_notification import TrayNotification

logger = logging.getLogger(__name__)

class UpdateGUI(UpdateUi):
    def __init__(self, progressBarUpdate):
        self._version_printed = False
        self.bar = progressBarUpdate

    def error(self, *msgs: Any) -> Exception:
        return CliException(*msgs)

    def abort(self, *msgs: Any) -> Exception:
        return CliException(*msgs, support_hint=False)

    def update_qbar(self, n: int, total: int) -> None:
        value = self.bar.value()
        if (n*100//total) > value:
            print((n*100//total))
            self.bar.setValue(((n)*100//total))

    def abort_downgrade(self, current: Version, image: Version) -> Exception:
        self._print_firmware_versions(current, image)
        return self.abort(
            "The firmware image is older than the firmware on the device."
        )

    def confirm_download(self, current: Optional[Version], new: Version) -> None:
        confirm_download_msgBox = QMessageBox()
        confirm_download_msgBox.setIcon(QMessageBox.Information)
        confirm_download_msgBox.setText(f"Do you want to download the firmware version {new}?")
        confirm_download_msgBox.setWindowTitle("Nitrokey 3 Firmware Update")
        confirm_download_msgBox.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
        returnValue = confirm_download_msgBox.exec()
        if returnValue == QMessageBox.Cancel:
            print('Cancel clicked')
            logger.info("Firmware Download cancelled by user in the second dialog")
            raise self.abort("Update cancelled by user in the second dialog")
        elif returnValue == QMessageBox.Ok:
            print('OK clicked')

    def confirm_update(self, current: Optional[Version], new: Version) -> None:
        confirm_update_msgBox = QMessageBox()
        confirm_update_msgBox.setIcon(QMessageBox.Information)
        confirm_update_msgBox.setText("Please do not remove the Nitrokey 3 or insert any other Nitrokey 3 devices during the update. Doing so may damage the Nitrokey 3. Do you want to perform the firmware update now?")
        confirm_update_msgBox.setWindowTitle("Nitrokey 3 Firmware Update")
        confirm_update_msgBox.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
        returnValue = confirm_update_msgBox.exec()
        if returnValue == QMessageBox.Cancel:
            print('Cancel clicked')
            logger.info("Update cancelled by user in the third dialog")
            raise self.abort("Update cancelled by user in the third dialog")
        elif returnValue == QMessageBox.Ok:
            print('OK clicked')
            TrayNotification("Nitrokey 3", "Nitrokey 3 Firmware Update", "Please touch your Nitrokey 3 Device")

    def confirm_update_same_version(self, version: Version) -> None:
        confirm_update_same_version_msgBox = QMessageBox()
        confirm_update_same_version_msgBox.setIcon(QMessageBox.Information)
        confirm_update_same_version_msgBox.setText("The version of the firmware image is the same as on the device. Do you want to continue anyway?")
        confirm_update_same_version_msgBox.setWindowTitle("Nitrokey 3 Firmware Update")
        confirm_update_same_version_msgBox.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
        returnValue = confirm_update_same_version_msgBox.exec()
        if returnValue == QMessageBox.Cancel:
            print('Cancel clicked')
            logger.info("Update cancelled by user in the first dialog")
            #raise Abort()
            raise self.abort("Update cancelled by user in the first dialog")
        elif returnValue == QMessageBox.Ok:
            print('OK clicked')

    def request_repeated_update(self) -> Exception:
        local_print(
            "Bootloader mode enabled. Please repeat this command to apply the update."
        )
        return Abort()

    def request_bootloader_confirmation(self) -> None:
        local_print("")
        local_print(
            "Please press the touch button to reboot the device into bootloader mode ..."
        )
        local_print("")

    def prompt_variant(self) -> Variant:
        return Variant.from_str(prompt("Firmware image variant", type=VARIANT_CHOICE))

    @contextmanager
    def update_progress_bar(self) -> Iterator[Callable[[int, int], None]]:
        yield self.update_qbar

    @contextmanager
    def download_progress_bar(self, desc: str):
        yield self.bar.show() and self.update_qbar

    def _print_firmware_versions(
        self, current: Optional[Version], new: Optional[Version]
    ) -> None:
        if not self._version_printed:
            current_str = str(current) if current else "[unknown]"
            local_print(f"Current firmware version:  {current_str}")
            local_print(f"Updated firmware version:  {new}")
            self._version_printed = True


def update(ctx: Nk3Context, progressBarUpdate, image: Optional[str], variant: Optional[Variant]) -> Version:
    with ctx.connect() as device:
        updater = Updater(UpdateGUI(progressBarUpdate), ctx.await_bootloader)
        return updater.update(device, image, variant)
