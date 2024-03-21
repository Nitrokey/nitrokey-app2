from typing import Optional

from PySide6 import QtWidgets
from PySide6.QtCore import QObject, Signal, Slot


class PromptUi(QObject):
    confirm = Signal(str, str)
    confirmed = Signal(bool)

    def __init__(self) -> None:
        super().__init__()


class PromptBox(QtWidgets.QMessageBox):
    confirmed = Signal(bool)

    def __init__(self, parent: Optional[QtWidgets.QWidget] = None):
        super().__init__(parent)

        self.finished.connect(self.send_confirmed)

    @Slot(int)
    def send_confirmed(self, result: int) -> None:
        self.confirmed.emit(result == QtWidgets.QMessageBox.StandardButton.Ok)

    @Slot(str, str)
    def confirm(self, title: str, desc: str) -> None:
        self.setText(desc)
        self.setWindowTitle(title)
        self.setStandardButtons(
            QtWidgets.QMessageBox.StandardButton.Ok
            | QtWidgets.QMessageBox.StandardButton.Cancel
        )
        self.setIcon(QtWidgets.QMessageBox.Icon.Information)

        self.show()
