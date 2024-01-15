import logging
from contextlib import contextmanager
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Iterator,
    List,
    Optional,
    Type,
    TypeVar,
)

# Nitrokey 3
from pynitrokey.cli.exceptions import CliException
from pynitrokey.helpers import Retries
from pynitrokey.nk3 import list as list_nk3
from pynitrokey.nk3 import open as open_nk3
from pynitrokey.nk3.base import Nitrokey3Base
from pynitrokey.nk3.bootloader import Nitrokey3Bootloader, Variant
from pynitrokey.nk3.device import Nitrokey3Device
from pynitrokey.nk3.updates import Updater, UpdateUi
from pynitrokey.nk3.utils import Version
from PySide6 import QtWidgets
from PySide6.QtCore import QCoreApplication

from nitrokeyapp.information_box import InfoBox

# TODO: This fixes a circular dependency, but should be avoided if possible
if TYPE_CHECKING:
    from nitrokeyapp.overview_tab import OverviewTab

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=Nitrokey3Base)

x = 0


class UpdateGUI(UpdateUi):
    def __init__(
        self,
        overview_tab: "OverviewTab",
        info_frame: InfoBox,
    ) -> None:
        self._version_printed = False
        self.overview_tab = overview_tab
        self.bar_update = overview_tab.ui.progressBar_Update
        self.bar_download = overview_tab.ui.progressBar_Download
        self.bar_finalization = overview_tab.ui.progressBar_Finalization
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
        confirm_download_msgBox = QtWidgets.QMessageBox(self.overview_tab)
        confirm_download_msgBox.setIcon(QtWidgets.QMessageBox.Icon.Information)
        confirm_download_msgBox.setText(
            f"Do you want to download the firmware version {new}?"
        )
        confirm_download_msgBox.setWindowTitle("Nitrokey 3 Firmware Update")
        confirm_download_msgBox.setStandardButtons(
            QtWidgets.QMessageBox.StandardButton.Ok
            | QtWidgets.QMessageBox.StandardButton.Cancel
        )
        returnValue = confirm_download_msgBox.exec()
        if returnValue == QtWidgets.QMessageBox.StandardButton.Cancel:
            logger.info("Cancel clicked (confirm download)")
            logger.info(
                "Firmware Download cancelled by user in the (confirm download) dialog"
            )
            raise self.abort(
                "Update cancelled by user in the (confirm download) dialog"
            )
        elif returnValue == QtWidgets.QMessageBox.StandardButton.Ok:
            logger.info("OK clicked (confirm download)")

    def confirm_update(self, current: Optional[Version], new: Version) -> None:
        confirm_update_msgBox = QtWidgets.QMessageBox(self.overview_tab)
        confirm_update_msgBox.setIcon(QtWidgets.QMessageBox.Icon.Information)
        confirm_update_msgBox.setText(
            "Please do not remove the Nitrokey 3 or insert any other Nitrokey 3 devices during the update. Doing so may damage the Nitrokey 3. Do you want to perform the firmware update now?"
        )
        confirm_update_msgBox.setWindowTitle("Nitrokey 3 Firmware Update")
        confirm_update_msgBox.setStandardButtons(
            QtWidgets.QMessageBox.StandardButton.Ok
            | QtWidgets.QMessageBox.StandardButton.Cancel
        )
        returnValue = confirm_update_msgBox.exec()
        if returnValue == QtWidgets.QMessageBox.StandardButton.Cancel:
            logger.info("Cancel clicked (confirm update)")
            logger.info("Update cancelled by user in the (confirm update) dialog")
            raise self.abort("Update cancelled by user in the (confirm update) dialog")
        elif returnValue == QtWidgets.QMessageBox.StandardButton.Ok:
            logger.info("OK clicked (confirm update)")
            self.info_frame.set_status(
                "Please touch the Nitrokey 3 until it stops flashing/glowing and then wait a few seconds.."
            )
            QCoreApplication.processEvents()

    def confirm_update_same_version(self, version: Version) -> None:
        confirm_update_same_version_msgBox = QtWidgets.QMessageBox(self.overview_tab)
        confirm_update_same_version_msgBox.setIcon(
            QtWidgets.QMessageBox.Icon.Information
        )
        confirm_update_same_version_msgBox.setText(
            "The version of the firmware image is the same as on the device. Do you want to continue anyway?"
        )
        confirm_update_same_version_msgBox.setWindowTitle("Nitrokey 3 Firmware Update")
        confirm_update_same_version_msgBox.setStandardButtons(
            QtWidgets.QMessageBox.StandardButton.Ok
            | QtWidgets.QMessageBox.StandardButton.Cancel
        )
        returnValue = confirm_update_same_version_msgBox.exec()
        if returnValue == QtWidgets.QMessageBox.StandardButton.Cancel:
            logger.info("Cancel clicked (confirm same version)")
            logger.info("Update cancelled by user in the (confirm same version) dialog")
            # raise Abort()
            raise self.abort(
                "Update cancelled by user in the (confirm same version) dialog"
            )
        elif returnValue == QtWidgets.QMessageBox.StandardButton.Ok:
            logger.info("OK clicked (confirm same version)")

    def confirm_extra_information(self, txt: List[str]) -> None:
        # if txt:
        # logger.info("\n".join(txt))
        # confirm_extra_information_msgBox QMessageBox(= QtWidgets.QMessageBox()
        # confirm_extra_information_msgBox.setIcon(QtWidgets.QMessageBox.Icon.Information)
        # confirm_extra_information_msgBox.setText(
        #     "Have you read these information? Do you want to continue?"
        # )
        # confirm_extra_information_msgBox.setWindowTitle("Nitrokey 3 Firmware Update")
        # confirm_extra_information_msgBox.setStandardButtons(
        #     QtWidgets.QMessageBox.StandardButton.Ok | QtWidgets.QMessageBox.StandardButton.Cancel
        # )
        # returnValue = confirm_extra_information_msgBox.exec()
        # if returnValue == QtWidgets.QMessageBox.StandardButton.Cancel:
        #     logger.info("Cancel clicked (confirm extra information)")
        #     logger.info("Update cancelled by user in the (confirm extra information) dialog")
        #     # raise Abort()
        #     raise self.abort("Update cancelled by user in the (confirm extra information) dialog")
        # elif returnValue == QtWidgets.QMessageBox.StandardButton.Ok:
        #     logger.info("OK clicked (confirm extra information)")
        # TODO: implement
        pass

    def abort_pynitrokey_version(
        self, current: Version, required: Version
    ) -> Exception:
        return self.abort(
            f"This update required pynitrokey {required} but you are using {current}"
        )

    def confirm_pynitrokey_version(self, current: Version, required: Version) -> None:
        # TODO: implement
        raise self.abort(
            f"This update required pynitrokey {required} but you are using {current}"
        )

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
        raise NotImplementedError()

    @contextmanager
    def update_progress_bar(self) -> Iterator[Callable[[int, int], None]]:
        self.bar_update.show()
        yield self.update_qbar

    @contextmanager
    def download_progress_bar(self, desc: str) -> Iterator[Callable[[int, int], None]]:
        self.bar_download.show()
        yield self.download_qbar

    @contextmanager
    def finalization_progress_bar(self) -> Iterator[Callable[[int, int], None]]:
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


class Nk3Context:
    def __init__(self, path: str) -> None:
        self.path = path
        logger.info(f"path: {path}")
        self.updating = False

    def connect(self) -> Nitrokey3Base:
        device = open_nk3(self.path)
        # TODO: improve error handling
        if not device:
            raise RuntimeError(f"Failed to open Nitrokey 3 device at {self.path}")
        return device

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

    def update(
        self,
        overview_tab: "OverviewTab",
        info_frame: InfoBox,
        image: Optional[str] = None,
        version: Optional[str] = None,
        ignore_pynitrokey_version: bool = False,
    ) -> None:
        with self.connect() as device:
            updater = Updater(
                UpdateGUI(overview_tab, info_frame),
                self.await_bootloader,
                self.await_device,
            )
            updater.update(device, image, version, ignore_pynitrokey_version)
