import logging
from dataclasses import dataclass
from typing import Callable, Optional

from PySide6.QtCore import QMetaObject, QObject, Signal, Slot
from PySide6.QtWidgets import QInputDialog, QLineEdit, QMessageBox, QWidget

logger = logging.getLogger(__name__)


class PinUi(QObject):
    queried = Signal(str)
    chosen = Signal(str)
    cancelled = Signal()

    def __init__(self, app_widget: QWidget) -> None:
        super().__init__(app_widget)

        self.app_widget = app_widget

    @Slot(int)
    def query(self, attempts: int) -> None:
        logger.info(f"Querying secrets PIN (remaining attempts: {attempts})")

        if attempts <= 2:
            title = f"Enter Passwords PIN — {attempts} attempt(s) remaining"
            message = (
                f"Enter the Passwords PIN.\n\n"
                f"WARNING: Only {attempts} attempt(s) remaining before the device locks permanently."
            )
        else:
            title = "Enter Passwords PIN"
            message = f"Enter the Passwords PIN ({attempts} attempts remaining):"

        pin, ok = QInputDialog.getText(self.app_widget, title, message, QLineEdit.EchoMode.Password)
        if ok and pin:
            logger.debug("PIN entered by user")
            self.queried.emit(pin)
        else:
            logger.info("PIN query cancelled by user")
            self.cancelled.emit()

    @Slot()
    def choose(self) -> None:
        logger.info("Prompting user to set secrets PIN")
        pin, ok = QInputDialog.getText(
            self.app_widget,
            "Set Passwords PIN",
            "Please enter the new PIN for Passwords:",
            QLineEdit.EchoMode.Password,
        )
        if not (ok and pin):
            logger.info("PIN choice cancelled by user")
            self.cancelled.emit()
            return

        confirm_pin, ok = QInputDialog.getText(
            self.app_widget,
            "Confirm Passwords PIN",
            "Please confirm the new PIN for Passwords:",
            QLineEdit.EchoMode.Password,
        )
        if not (ok and confirm_pin):
            logger.info("PIN confirmation cancelled by user")
            self.cancelled.emit()
            return

        if pin != confirm_pin:
            logger.warning("PIN confirmation mismatch — not setting PIN")
            QMessageBox.warning(
                self.app_widget,
                "PIN Mismatch",
                "The PINs you entered do not match. The PIN has not been changed.",
            )
            self.cancelled.emit()
            return

        logger.debug("New PIN entered and confirmed by user")
        self.chosen.emit(pin)

    def connect_actions(
        self,
        queried: Optional[Callable[[str], None]],
        chosen: Optional[Callable[[str], None]],
        cancelled: Optional[Callable[[], None]],
    ) -> "PinUiConnection":
        connection = PinUiConnection(self)
        if queried:
            connection.queried = self.queried.connect(queried)
        if chosen:
            connection.chosen = self.chosen.connect(chosen)
        if cancelled:
            connection.cancelled = self.cancelled.connect(cancelled)
        return connection


@dataclass
class PinUiConnection:
    pin_ui: PinUi
    queried: Optional[QMetaObject.Connection] = None
    chosen: Optional[QMetaObject.Connection] = None
    cancelled: Optional[QMetaObject.Connection] = None

    def disconnect(self) -> None:
        if self.queried:
            self.pin_ui.queried.disconnect(self.queried)
            self.queried = None
        if self.chosen:
            self.pin_ui.chosen.disconnect(self.chosen)
            self.chosen = None
        if self.cancelled:
            self.pin_ui.cancelled.disconnect(self.cancelled)
            self.cancelled = None
