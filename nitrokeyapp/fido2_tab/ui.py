from dataclasses import dataclass
from typing import Callable, Optional

from PySide6.QtCore import QMetaObject, QObject, Signal, Slot
from PySide6.QtWidgets import QInputDialog, QLineEdit, QWidget


class Fido2PinUi(QObject):
    query = Signal(int)
    queried = Signal(str)
    cancelled = Signal()

    def __init__(self, app_widget: QWidget) -> None:
        super().__init__(app_widget)
        self.app_widget = app_widget
        self.query.connect(self._query)

    @Slot(int)
    def _query(self, attempts: int) -> None:
        pin, ok = QInputDialog.getText(
            self.app_widget,
            "Enter FIDO2 PIN",
            f"Please enter the FIDO2 PIN (remaining retries: {attempts}):",
            QLineEdit.EchoMode.Password,
        )
        if ok and pin:
            self.queried.emit(pin)
        else:
            self.cancelled.emit()

    def connect_actions(
        self, queried: Optional[Callable[[str], None]], cancelled: Optional[Callable[[], None]]
    ) -> "Fido2PinUiConnection":
        connection = Fido2PinUiConnection(self)
        if queried:
            connection.queried = self.queried.connect(queried)
        if cancelled:
            connection.cancelled = self.cancelled.connect(cancelled)
        return connection


@dataclass
class Fido2PinUiConnection:
    pin_ui: Fido2PinUi
    queried: Optional[QMetaObject.Connection] = None
    cancelled: Optional[QMetaObject.Connection] = None

    def disconnect(self) -> None:
        if self.queried:
            self.pin_ui.queried.disconnect(self.queried)
            self.queried = None
        if self.cancelled:
            self.pin_ui.cancelled.disconnect(self.cancelled)
            self.cancelled = None
