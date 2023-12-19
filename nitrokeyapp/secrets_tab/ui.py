from dataclasses import dataclass
from typing import Callable, Optional

from PySide6.QtCore import QMetaObject, QObject, Signal, Slot
from PySide6.QtWidgets import QInputDialog, QLineEdit, QWidget


class PinUi(QObject):
    queried = Signal(str)
    chosen = Signal(str)
    cancelled = Signal()

    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent)

        self.parent_widget = parent

    @Slot(int)
    def query(self, attempts: int) -> None:
        pin, ok = QInputDialog.getText(
            self.parent_widget,
            "Enter Passwords PIN",
            "Please enter the Passwords PIN (remaining retries: " f"{attempts}):",
            QLineEdit.EchoMode.Password,
        )
        if ok and pin:
            self.queried.emit(pin)
        else:
            self.cancelled.emit()

    @Slot()
    def choose(self) -> None:
        # TODO: confirm
        pin, ok = QInputDialog.getText(
            self.parent_widget,
            "Set Passwords PIN",
            "Please enter the new PIN for Passwords:",
            QLineEdit.EchoMode.Password,
        )
        if ok and pin:
            self.chosen.emit(pin)
        else:
            self.cancelled.emit()

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
