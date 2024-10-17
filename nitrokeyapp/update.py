import logging
from contextlib import contextmanager
from time import sleep
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
from nitrokey.nk3 import NK3, NK3Bootloader
from nitrokey.nk3 import list as list_nk3
from nitrokey.nk3 import open as open_nk3
from nitrokey.nk3.updates import Updater, UpdateUi
from nitrokey.trussed import TrussedBase, Variant, Version
from PySide6.QtCore import QCoreApplication

if TYPE_CHECKING:
    from nitrokeyapp.common_ui import CommonUi

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=TrussedBase)


class UpdateGUI(UpdateUi):
    def __init__(self, common_ui: "CommonUi", is_qubesos: bool) -> None:
        super().__init__()

        self._version_printed = False
        self.common_ui = common_ui
        self.is_qubesos = is_qubesos

        # blocking wait, set by parent during confirm-prompt
        self.await_confirmation: Optional[bool] = None

    def error(self, *msgs: Any) -> Exception:
        return Exception(*msgs)

    def abort(self, *msgs: Any) -> Exception:
        return Exception(*msgs)

    def abort_downgrade(self, current: Version, image: Version) -> Exception:
        self._print_firmware_versions(current, image)
        return self.abort("Abort: firmware older as on device")

    def run_confirm_dialog(self, title: str, desc: str) -> bool:
        self.common_ui.prompt.confirm.emit(title, desc)
        while self.await_confirmation is None:
            sleep(0.1)
            QCoreApplication.processEvents()

        res = self.await_confirmation
        self.await_confirmation = None
        return res

    def confirm_download(self, current: Optional[Version], new: Version) -> None:
        res = self.run_confirm_dialog(
            "Nitrokey 3 Firmware Update",
            f"Do you want to download the firmware version {new}?",
        )
        if not res:
            logger.info("Cancel clicked (confirm download)")
            raise self.abort("Abort: canceled by user (confirm download)")

        logger.info("OK clicked (confirm download)")

    def confirm_update(self, current: Optional[Version], new: Version) -> None:
        if self.is_qubesos:
            res = self.run_confirm_dialog(
                "Nitrokey 3 Firmware Update",
                "Please do not remove the Nitrokey 3 or insert any other "
                + "Nitrokey 3 devices during the update. Doing so may "
                + "damage the Nitrokey 3.\n\n"
                + "QubesOS is detected!\n\n"
                + "After the touch prompt, the Nitrokey3 will be loaded into the bootloader. The Nitrokey must then be reattach to the current Qube.\n\n"
                + "Do you want to perform the firmware update now?",
            )

        else:
            res = self.run_confirm_dialog(
                "Nitrokey 3 Firmware Update",
                "Please do not remove the Nitrokey 3 or insert any other "
                + "Nitrokey 3 devices during the update. Doing so may "
                + "damage the Nitrokey 3. Do you want to perform the "
                + "firmware update now?",
            )
        if not res:
            logger.info("Cancel clicked (confirm update)")
            raise self.abort("Abort: canceled by user (confirm update)")

        logger.info("OK clicked (confirm update)")
        self.common_ui.touch.start.emit()

    def pre_bootloader_hint(self) -> None:
        self.common_ui.info.info.emit("Device is in bootloader mode")

    def confirm_update_same_version(self, version: Version) -> None:
        res = self.run_confirm_dialog(
            "Nitrokey 3 Firmware Update",
            "The version of the firmware image is the same as on the device."
            + "Do you want to continue anyway?",
        )
        if not res:
            logger.info("Cancel clicked (confirm same version)")
            raise self.abort("Abort: canceled by user (confirm same version)")

        logger.info("OK clicked (confirm same version)")

    def confirm_extra_information(self, txt: List[str]) -> None:
        res = self.run_confirm_dialog("Confirm extra information", " ".join(txt))
        if not res:
            logger.info("Cancel clicked (confirm extra info)")
            raise self.abort("Abort: canceled by user (confirm extra info)")

        logger.info("OK clicked (confirm same version)")

    def abort_pynitrokey_version(
        self, current: Version, required: Version
    ) -> Exception:
        raise self.abort(f"Abort: pynitrokey {required} too old, need: {current}")

    def confirm_pynitrokey_version(self, current: Version, required: Version) -> None:
        # TODO: implement
        raise self.abort(f"Abort: pynitrokey {required} too old, need: {current}")

    def request_repeated_update(self) -> Exception:
        logger.info("Bootloader mode enabled. Repeat to update")
        return self.abort("Abort: bootloader enabled")

    def request_bootloader_confirmation(self) -> None:
        logger.info("requesting bootloader confirmation")
        self.common_ui.touch.start.emit()

    # atm we dont need this
    def prompt_variant(self) -> Variant:
        raise NotImplementedError()

    @contextmanager
    def update_progress_bar(self) -> Iterator[Callable[[int, int], None]]:
        self.common_ui.touch.stop.emit()
        self.common_ui.progress.start.emit("Update")
        yield self.common_ui.progress.progress.emit

    @contextmanager
    def download_progress_bar(self, desc: str) -> Iterator[Callable[[int, int], None]]:
        self.common_ui.progress.start.emit("Download")
        yield self.common_ui.progress.progress.emit

    @contextmanager
    def finalization_progress_bar(
        self,
    ) -> Iterator[Callable[[int, int], None]]:
        self.common_ui.progress.start.emit("Finalization")
        yield self.common_ui.progress.progress.emit

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

    def connect(self) -> TrussedBase:
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
            try:
                devices = [device for device in list_nk3() if isinstance(device, ty)]
            except Exception:
                # have to catch this, to avoid early exception-raise-out
                devices = []
            if len(devices) == 0:
                if callback:
                    callback(int((t.i / retries) * 100), 100)
                logger.debug(f"No {name} device found, continuing")
                continue
            if len(devices) > 1:
                raise Exception(f"Multiple {name} devices found")
            if callback:
                callback(100, 100)
            return devices[0]

        raise Exception(f"No {name} device found")

    def await_device(
        self,
        retries: Optional[int] = 90,
        callback: Optional[Callable[[int, int], None]] = None,
    ) -> NK3:
        assert isinstance(retries, int)
        return self._await("Nitrokey 3", NK3, retries, callback)

    def await_bootloader(
        self,
        retries: Optional[int] = 90,
        callback: Optional[Callable[[int, int], None]] = None,
    ) -> NK3Bootloader:
        assert isinstance(retries, int)
        # mypy does not allow abstract types here, but this is still valid
        return self._await("Nitrokey 3 bootloader", NK3Bootloader, retries, callback)  # type: ignore

    def update(
        self,
        ui: UpdateGUI,
        image: Optional[str] = None,
        version: Optional[str] = None,
        ignore_pynitrokey_version: bool = False,
    ) -> None:

        with self.connect() as device:
            updater = Updater(
                ui,
                self.await_bootloader,
                self.await_device,
            )
            updater.update(device, image, version, ignore_pynitrokey_version)


class Try:
    """Utility class for an execution of a repeated action with Retries."""

    def __init__(self, i: int, retries: int) -> None:
        self.i = i
        self.retries = retries

    def __str__(self) -> str:
        return f"try {self.i + 1} of {self.retries}"

    def __repr__(self) -> str:
        return f"Try(i={self.i}, retries={self.retries})"


class Retries:
    """Utility class for repeating an action multiple times until it succeeds."""

    def __init__(self, retries: int, timeout: float = 0.5) -> None:
        self.retries = retries
        self.i = 0
        self.timeout = timeout

    def __iter__(self) -> "Retries":
        return self

    def __next__(self) -> Try:
        if self.i >= self.retries:
            raise StopIteration
        if self.i > 0:
            sleep(self.timeout)
        t = Try(self.i, self.retries)
        self.i += 1
        return t
