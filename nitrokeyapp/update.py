import logging
from contextlib import contextmanager
from typing import Any, List, Optional

# Nitrokey 3
from pynitrokey.cli.exceptions import CliException
from pynitrokey.nk3.bootloader import Variant
from pynitrokey.nk3.updates import Updater, UpdateUi
from pynitrokey.nk3.utils import Version
from PyQt5 import QtWidgets
from PyQt5.QtCore import QCoreApplication

from nitrokeyapp.pynitrokey_for_gui import Nk3Context

logger = logging.getLogger(__name__)

x = 0


class UpdateGUI(UpdateUi):
    def __init__(
        self,
        progressBarUpdate,
        progressBarDownload,
        progressBarFinalization,
        info_frame,
    ):
        self._version_printed = False
        self.bar_update = progressBarUpdate
        self.bar_download = progressBarDownload
        self.bar_finalization = progressBarFinalization
        self.info_frame = info_frame

    def error(self, *msgs: Any) -> Exception:
        return CliException(*msgs)

    def abort(self, *msgs: Any) -> Exception:
        return CliException(*msgs, support_hint=False)

    def update_qbar(self, n: int, total: int) -> None:
        value = self.bar_update.value()
        if n >= total:
            self.bar_update.setValue(0)
            self.bar_update.hide()
        elif (n * 100 // total) > value:
            self.bar_update.setValue(((n) * 100 // total))
            QCoreApplication.processEvents()

    def download_qbar(self, n: int, total: int) -> None:
        value = self.bar_download.value()
        global x
        x += n
        if x == total:
            self.bar_download.setValue(0)
            self.bar_download.hide()
            x = 0
        if (x * 100 // total) > value:
            self.bar_download.setValue(x * 100 // total)
            QCoreApplication.processEvents()

    def finalization_qbar(self, n: int, total: int) -> None:
        value = self.bar_finalization.value()
        if n >= total:
            self.bar_finalization.setValue(0)
            self.bar_finalization.hide()
        elif n > value:
            self.bar_finalization.setValue(n)
            QCoreApplication.processEvents()

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
            logger.info("Cancel clicked (confirm download)")
            logger.info(
                "Firmware Download cancelled by user in the (confirm download) dialog"
            )
            raise self.abort(
                "Update cancelled by user in the (confirm download) dialog"
            )
        elif returnValue == QtWidgets.QMessageBox.Ok:
            logger.info("OK clicked (confirm download)")

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
            logger.info("Cancel clicked (confirm update)")
            logger.info("Update cancelled by user in the (confirm update) dialog")
            raise self.abort("Update cancelled by user in the (confirm update) dialog")
        elif returnValue == QtWidgets.QMessageBox.Ok:
            logger.info("OK clicked (confirm update)")
            self.info_frame.set_text(
                "Please touch the Nitrokey 3 until it stops flashing/glowing and then wait a few seconds.."
            )
            QCoreApplication.processEvents()

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
            logger.info("Cancel clicked (confirm same version)")
            logger.info("Update cancelled by user in the (confirm same version) dialog")
            # raise Abort()
            raise self.abort(
                "Update cancelled by user in the (confirm same version) dialog"
            )
        elif returnValue == QtWidgets.QMessageBox.Ok:
            logger.info("OK clicked (confirm same version)")

    def confirm_extra_information(self, txt: List[str]) -> None:
        # if txt:
        # logger.info("\n".join(txt))
        # confirm_extra_information_msgBox = QtWidgets.QMessageBox()
        # confirm_extra_information_msgBox.setIcon(QtWidgets.QMessageBox.Information)
        # confirm_extra_information_msgBox.setText(
        #     "Have you read these information? Do you want to continue?"
        # )
        # confirm_extra_information_msgBox.setWindowTitle("Nitrokey 3 Firmware Update")
        # confirm_extra_information_msgBox.setStandardButtons(
        #     QtWidgets.QMessageBox.Ok | QtWidgets.QMessageBox.Cancel
        # )
        # returnValue = confirm_extra_information_msgBox.exec()
        # if returnValue == QtWidgets.QMessageBox.Cancel:
        #     logger.info("Cancel clicked (confirm extra information)")
        #     logger.info("Update cancelled by user in the (confirm extra information) dialog")
        #     # raise Abort()
        #     raise self.abort("Update cancelled by user in the (confirm extra information) dialog")
        # elif returnValue == QtWidgets.QMessageBox.Ok:
        #     logger.info("OK clicked (confirm extra information)")
        return True

    def abort_pynitrokey_version(
        self, current: Version, required: Version
    ) -> Exception:
        True

    def confirm_pynitrokey_version(self, current: Version, required: Version) -> None:
        True

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

    # atm we dont need this
    def prompt_variant(self) -> Variant:
        return 0

    @contextmanager
    def update_progress_bar(self):
        self.bar_update.show()
        yield self.update_qbar

    @contextmanager
    def download_progress_bar(self, desc: str):
        self.bar_download.show()
        yield self.download_qbar

    @contextmanager
    def finalization_progress_bar(self):
        self.bar_finalization.show()
        yield self.finalization_qbar

    def _print_firmware_versions(
        self, current: Optional[Version], new: Optional[Version]
    ) -> None:
        if not self._version_printed:
            current_str = str(current) if current else "[unknown]"
            logger.info(f"Current firmware version:  {current_str}")
            logger.info(f"Updated firmware version:  {new}")
            self._version_printed = True


def update(
    ctx: Nk3Context,
    progressBarUpdate,
    progressBarDownload,
    progressBarFinalization,
    image: Optional[str],
    version: Optional[str],
    ignore_pynitrokey_version: bool,
    info_frame,
) -> None:
    with ctx.connect() as device:

        updater = Updater(
            UpdateGUI(
                progressBarUpdate,
                progressBarDownload,
                progressBarFinalization,
                info_frame,
            ),
            ctx.await_bootloader,
            ctx.await_device,
        )
        return updater.update(device, image, version, ignore_pynitrokey_version)
