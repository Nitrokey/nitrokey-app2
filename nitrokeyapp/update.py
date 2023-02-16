import logging
from contextlib import contextmanager
from typing import Any, Callable, Iterator, Optional

# Nitrokey 3
from pynitrokey.cli.exceptions import CliException
from pynitrokey.nk3.bootloader import Variant
from pynitrokey.nk3.updates import Updater, UpdateUi
from pynitrokey.nk3.utils import Version
from PyQt5 import QtWidgets

from nitrokeyapp.pynitrokey_for_gui import Nk3Context

# tray icon
from nitrokeyapp.tray_notification import TrayNotification

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
        if (n * 100 // total) > value:
            self.bar.setValue(((n) * 100 // total))

    def abort_downgrade(self, current: Version, image: Version) -> Exception:
        self._print_firmware_versions(current, image)
        return self.abort(
            "The firmware image is older than the firmware on the device."
        )

    def confirm_download(self, current: Optional[Version], new: Version) -> None:
        confirm_download_msgBox = QtWidgets.QMessageBox()
        confirm_download_msgBox.setIcon(QtWidgets.QMessageBox.Information)
        confirm_download_msgBox.setText(
            f"Do you want to download the firmware version {new}?"
        )
        confirm_download_msgBox.setWindowTitle("Nitrokey 3 Firmware Update")
        confirm_download_msgBox.setStandardButtons(
            QtWidgets.QMessageBox.Ok | QtWidgets.QMessageBox.Cancel
        )
        returnValue = confirm_download_msgBox.exec()
        if returnValue == QtWidgets.QMessageBox.Cancel:
            logger.info("Cancel clicked 1")
            logger.info("Firmware Download cancelled by user in the second dialog")
            raise self.abort("Update cancelled by user in the second dialog")
        elif returnValue == QtWidgets.QMessageBox.Ok:
            logger.info("OK clicked 1")

    def confirm_update(self, current: Optional[Version], new: Version) -> None:
        confirm_update_msgBox = QtWidgets.QMessageBox()
        confirm_update_msgBox.setIcon(QtWidgets.QMessageBox.Information)
        confirm_update_msgBox.setText(
            "Please do not remove the Nitrokey 3 or insert any other Nitrokey 3 devices during the update. Doing so may damage the Nitrokey 3. Do you want to perform the firmware update now?"
        )
        confirm_update_msgBox.setWindowTitle("Nitrokey 3 Firmware Update")
        confirm_update_msgBox.setStandardButtons(
            QtWidgets.QMessageBox.Ok | QtWidgets.QMessageBox.Cancel
        )
        returnValue = confirm_update_msgBox.exec()
        if returnValue == QtWidgets.QMessageBox.Cancel:
            logger.info("Cancel clicked 2")
            logger.info("Update cancelled by user in the third dialog")
            raise self.abort("Update cancelled by user in the third dialog")
        elif returnValue == QtWidgets.QMessageBox.Ok:
            logger.info("OK clicked 2")
            TrayNotification(
                "Nitrokey 3",
                "Nitrokey 3 Firmware Update",
                "Please touch your Nitrokey 3 Device",
            )

    def confirm_update_same_version(self, version: Version) -> None:
        confirm_update_same_version_msgBox = QtWidgets.QMessageBox()
        confirm_update_same_version_msgBox.setIcon(QtWidgets.QMessageBox.Information)
        confirm_update_same_version_msgBox.setText(
            "The version of the firmware image is the same as on the device. Do you want to continue anyway?"
        )
        confirm_update_same_version_msgBox.setWindowTitle("Nitrokey 3 Firmware Update")
        confirm_update_same_version_msgBox.setStandardButtons(
            QtWidgets.QMessageBox.Ok | QtWidgets.QMessageBox.Cancel
        )
        returnValue = confirm_update_same_version_msgBox.exec()
        if returnValue == QtWidgets.QMessageBox.Cancel:
            logger.info("Cancel clicked 3")
            logger.info("Update cancelled by user in the first dialog")
            # raise Abort()
            raise self.abort("Update cancelled by user in the first dialog")
        elif returnValue == QtWidgets.QMessageBox.Ok:
            logger.info("OK clicked 3")

    def request_repeated_update(self) -> Exception:
        logger.info(
            "Bootloader mode enabled. Please repeat this command to apply the update."
        )
        return self.abort(
            "Bootloader mode enabled. Please repeat this command to apply the update."
        )

    def request_bootloader_confirmation(self) -> None:
        logger.info(
            "Please press the touch button to reboot the device into bootloader mode ..."
        )

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
            logger.info(f"Current firmware version:  {current_str}")
            logger.info(f"Updated firmware version:  {new}")
            self._version_printed = True


def update(
    ctx: Nk3Context, progressBarUpdate, image: Optional[str], variant: Optional[Variant]
) -> Version:
    with ctx.connect() as device:
        updater = Updater(UpdateGUI(progressBarUpdate), ctx.await_bootloader)
        return updater.update(device, image, variant)
