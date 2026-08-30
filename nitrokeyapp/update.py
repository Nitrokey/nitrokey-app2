import logging
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from enum import Enum
from time import sleep
from typing import TYPE_CHECKING, Any, TypeVar

from nitrokey import trussed
from nitrokey.trussed import Model, TrussedBase, TrussedBootloader, TrussedDevice, Version
from nitrokey.trussed.admin_app import InitStatus
from nitrokey.trussed.updates import DeviceHandler, Updater, UpdateUi, Warning
from PySide6.QtCore import QCoreApplication

from nitrokeyapp.error_messages import warning_message

if TYPE_CHECKING:
    from nitrokeyapp.common_ui import CommonUi

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=TrussedBase)


class UpdateStatus(Enum):
    SUCCESS = "success"
    ERROR = "error"
    ABORTED = "aborted"


@dataclass
class UpdateResult:
    model: Model
    status: UpdateStatus
    message: str | None = None


@dataclass
class UpdateException(Exception):
    def __init__(self, status: UpdateStatus, *msgs: Any) -> None:
        super().__init__(*msgs)
        self.status = status


class UpdateGUI(UpdateUi):
    def __init__(self, common_ui: "CommonUi", model: Model, is_qubesos: bool) -> None:
        super().__init__()

        self.common_ui = common_ui
        self.model = model
        self.is_qubesos = is_qubesos

        # blocking wait, set by parent during confirm-prompt
        self.await_confirmation: bool | None = None

    def error(self, *msgs: Any) -> Exception:
        logger.error(f"Error during firmware update: {msgs}")
        return UpdateException(UpdateStatus.ERROR, *msgs)

    def abort(self, *msgs: Any) -> Exception:
        logger.warning(f"Firmware update aborted: {msgs}")
        return UpdateException(UpdateStatus.ABORTED, *msgs)

    def raise_warning(self, warning: Warning) -> Exception:
        return UpdateException(UpdateStatus.ERROR, warning_message(warning))

    def show_warning(self, warning: Warning) -> None:
        res = self.run_confirm_dialog(
            QCoreApplication.translate(
                "update", "DANGER - you can ignore this warning by pressing OK"
            ),
            warning_message(warning),
        )
        if not res:
            logger.info("Cancel clicked (during warning)")
            raise self.abort(
                QCoreApplication.translate("update", "The firmware update was cancelled.")
            )

        logger.info("OK clicked (warning dialog)")

    def abort_downgrade(self, current: Version, image: Version) -> Exception:
        logger.warning(f"downgrade from {current} to {image}")
        return self.abort(
            QCoreApplication.translate(
                "update", "The firmware image ({0}) is older than the firmware on the device ({1})."
            ).format(image, current)
        )

    def run_confirm_dialog(self, title: str, desc: str) -> bool:
        self.common_ui.prompt.confirm.emit(title, desc)
        while self.await_confirmation is None:
            sleep(0.1)
            QCoreApplication.processEvents()

        res = self.await_confirmation
        self.await_confirmation = None
        return res

    def confirm_download(self, current: Version | None, new: Version) -> None:
        res = self.run_confirm_dialog(
            self.update_title(),
            QCoreApplication.translate(
                "update", "Do you want to download firmware version {0}?"
            ).format(new),
        )
        if not res:
            logger.info("Cancel clicked (confirm download)")
            raise self.abort(
                QCoreApplication.translate("update", "The firmware update was cancelled.")
            )

        logger.info("OK clicked (confirm download)")

    def update_title(self) -> str:
        return QCoreApplication.translate("update", "{0} Firmware Update").format(self.model)

    def confirm_update(self, current: Version | None, new: Version) -> None:
        warning = QCoreApplication.translate(
            "update",
            "Please do not remove the {0} or insert any other {0} devices during the "
            "update. Doing so may damage the {0}.",
        ).format(self.model)

        if self.is_qubesos:
            question = QCoreApplication.translate(
                "update",
                "QubesOS is detected!\n\n"
                "After the touch prompt, the {0} will be loaded into the bootloader. "
                "The Nitrokey must then be reattached to the current Qube.\n\n"
                "Do you want to perform the firmware update now?",
            ).format(self.model)
        else:
            question = QCoreApplication.translate(
                "update", "Do you want to perform the firmware update now?"
            )

        res = self.run_confirm_dialog(self.update_title(), f"{warning}\n\n{question}")
        if not res:
            logger.info("Cancel clicked (confirm update)")
            raise self.abort(
                QCoreApplication.translate("update", "The firmware update was cancelled.")
            )

        logger.info("OK clicked (confirm update)")
        self.common_ui.touch.start.emit()

    def pre_bootloader_hint(self) -> None:
        self.common_ui.info.info.emit(
            QCoreApplication.translate("update", "Device is in bootloader mode")
        )

    def confirm_update_same_version(self, version: Version) -> None:
        res = self.run_confirm_dialog(
            self.update_title(),
            QCoreApplication.translate(
                "update",
                "The version of the firmware image is the same as the one on the device. "
                "Do you want to continue anyway?",
            ),
        )
        if not res:
            logger.info("Cancel clicked (confirm same version)")
            raise self.abort(
                QCoreApplication.translate("update", "The firmware update was cancelled.")
            )

        logger.info("OK clicked (confirm same version)")

    def confirm_extra_information(self, txt: list[str]) -> None:
        if len(txt) == 0:
            return

        res = self.run_confirm_dialog(
            QCoreApplication.translate("update", "Confirm extra information"), " ".join(txt)
        )
        if not res:
            logger.info("Cancel clicked (confirm extra info)")
            raise self.abort(
                QCoreApplication.translate("update", "The firmware update was cancelled.")
            )

        logger.info("OK clicked (confirm extra info)")

    def abort_pynitrokey_version(self, current: Version, required: Version) -> Exception:
        raise self.abort(self.pynitrokey_version_message(current, required))

    def confirm_pynitrokey_version(self, current: Version, required: Version) -> None:
        # TODO: implement
        raise self.abort(self.pynitrokey_version_message(current, required))

    def pynitrokey_version_message(self, current: Version, required: Version) -> str:
        logger.error(f"pynitrokey {current} too old, need: {required}")
        return QCoreApplication.translate(
            "update",
            "This version of the Nitrokey App is too old for the update. "
            "Please install version {0} or newer.",
        ).format(required)

    def request_repeated_update(self) -> Exception:
        logger.info("Bootloader mode enabled. Repeat to update")
        return self.abort(
            QCoreApplication.translate(
                "update",
                "The device was switched to bootloader mode. "
                "Please start the firmware update again.",
            )
        )

    def request_bootloader_confirmation(self) -> None:
        logger.info("requesting bootloader confirmation")
        self.common_ui.touch.start.emit()

    @contextmanager
    def update_progress_bar(self) -> Iterator[Callable[[int, int], None]]:
        self.common_ui.touch.stop.emit()
        self.common_ui.progress.start.emit(QCoreApplication.translate("update", "Update"))
        yield self.common_ui.progress.progress.emit

    @contextmanager
    def download_progress_bar(self, desc: str) -> Iterator[Callable[[int, int], None]]:
        self.common_ui.progress.start.emit(QCoreApplication.translate("update", "Download"))
        yield self.common_ui.progress.progress.emit

    @contextmanager
    def finalization_progress_bar(self) -> Iterator[Callable[[int, int], None]]:
        self.common_ui.progress.start.emit(QCoreApplication.translate("update", "Finalization"))
        yield self.common_ui.progress.progress.emit


class UpdateContext(DeviceHandler):
    def __init__(self, path: str, model: Model) -> None:
        self.path = path
        self.model = model
        logger.info(f"update for path: {path}, model: {model}")
        self.updating = False

    def connect(self) -> TrussedBase:
        device = trussed.open(path=self.path, model=self.model)
        if not device:
            logger.error(f"failed to open {self.model} device at {self.path}")
            raise RuntimeError(
                QCoreApplication.translate("update", "The device is no longer available.")
            )
        if device.model != self.model:
            logger.error(f"found {device.model} at {self.path}, expected {self.model}")
            raise RuntimeError(
                QCoreApplication.translate(
                    "update", "Found a {0} where a {1} was expected."
                ).format(device.model, self.model)
            )
        return device

    def _await(
        self,
        name: str,
        ty: type[T],
        retries: int,
        callback: Callable[[int, int], None] | None = None,
    ) -> T:
        for t in Retries(retries):
            logger.debug(f"Searching {name} device ({t})")
            try:
                devices = [
                    device for device in trussed.list(model=self.model) if isinstance(device, ty)
                ]
            except Exception:
                # have to catch this, to avoid early exception-raise-out
                devices = []
            if len(devices) == 0:
                if callback:
                    callback(int((t.i / retries) * 100), 100)
                logger.debug(f"No {name} device found, continuing")
                continue
            if len(devices) > 1:
                logger.error(f"multiple {name} devices found")
                raise Exception(
                    QCoreApplication.translate(
                        "update",
                        "More than one {0} is connected. Please connect only the device "
                        "that should be updated.",
                    ).format(name)
                )
            if callback:
                callback(100, 100)
            return devices[0]

        logger.error(f"no {name} device found")
        raise Exception(
            QCoreApplication.translate("update", "The {0} could not be found.").format(name)
        )

    def await_device(
        self,
        model: Model,
        retries: int | None = 90,
        callback: Callable[[int, int], None] | None = None,
    ) -> TrussedDevice:
        assert model == self.model
        assert retries is not None
        return self._await(str(model), TrussedDevice, retries, callback)  # type: ignore[type-abstract]

    def await_bootloader(self, model: Model) -> TrussedBootloader:
        assert model == self.model
        # mypy does not allow abstract types here, but this is still valid
        return self._await(f"{self.model} bootloader", TrussedBootloader, 90, None)  # type: ignore[type-abstract]

    def update(self, ui: UpdateGUI, image: str | None = None) -> UpdateResult:
        try:
            with self.connect() as device:
                updater = Updater(ui, self)
                _, status = updater.update(device=device, image=image, update_version=None)
        except UpdateException as e:
            return UpdateResult(model=self.model, status=e.status, message=str(e))
        except Exception as e:
            return UpdateResult(model=self.model, status=UpdateStatus.ERROR, message=str(e))

        if status.init_status is not None:
            if status.init_status & InitStatus.EXT_FLASH_NEED_REFORMAT:
                logger.error(f"Problematic init status after update: {status.init_status}")
                return UpdateResult(
                    model=self.model,
                    status=UpdateStatus.ERROR,
                    message=QCoreApplication.translate(
                        "update",
                        "The external filesystem of the device needs to be reformatted. "
                        "Please contact {0} for more information on how to solve this issue.",
                    ).format("support@nitrokey.com"),
                )

        return UpdateResult(model=self.model, status=UpdateStatus.SUCCESS)


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
