# Copyright 2026 Nitrokey Developers
#
# Licensed under the Apache License, Version 2.0, <LICENSE-APACHE or
# http://apache.org/licenses/LICENSE-2.0> or the MIT license <LICENSE-MIT or
# http://opensource.org/licenses/MIT>, at your option. This file may not be
# copied, modified, or distributed except according to those terms.

from dataclasses import dataclass
from typing import Callable, Optional

from PySide6.QtCore import QMetaObject, QObject, Signal, Slot
from PySide6.QtWidgets import QInputDialog, QLineEdit, QWidget


class PivPinUi(QObject):
    """Prompt for PIV PIN via a modal dialog (runs in the UI thread)."""

    query = Signal(int)   # emitted from worker thread; delivered to UI thread
    queried = Signal(str)
    cancelled = Signal()

    def __init__(self, app_widget: QWidget, title: str = "PIV PIN", label: str = "Enter PIV PIN:") -> None:
        super().__init__(app_widget)
        self.app_widget = app_widget
        self.title = title
        self.label = label
        self.query.connect(self._show_dialog)

    @Slot(int)
    def _show_dialog(self, retries: int) -> None:
        label = f"{self.label} (remaining retries: {retries})" if retries >= 0 else self.label
        pin, ok = QInputDialog.getText(
            self.app_widget,
            self.title,
            label,
            QLineEdit.EchoMode.Password,
        )
        if ok and pin:
            self.queried.emit(pin)
        else:
            self.cancelled.emit()

    def connect_actions(
        self,
        queried: Optional[Callable[[str], None]],
        cancelled: Optional[Callable[[], None]],
    ) -> "PivPinUiConnection":
        conn = PivPinUiConnection(self)
        if queried:
            conn.queried = self.queried.connect(queried)
        if cancelled:
            conn.cancelled = self.cancelled.connect(cancelled)
        return conn


@dataclass
class PivPinUiConnection:
    pin_ui: PivPinUi
    queried: Optional[QMetaObject.Connection] = None
    cancelled: Optional[QMetaObject.Connection] = None

    def disconnect(self) -> None:
        if self.queried:
            self.pin_ui.queried.disconnect(self.queried)
            self.queried = None
        if self.cancelled:
            self.pin_ui.cancelled.disconnect(self.cancelled)
            self.cancelled = None
