from typing import Optional

from PySide6 import QtWidgets
from PySide6.QtCore import QObject, Signal, Slot


class PromptUi(QObject):
    confirm = Signal(str, str)
    confirmed = Signal(bool)

    # def __init__(self, parent: QObject) -> None:
    # super().__init__(parent)
    # super().__init__()
    def __init__(self) -> None:
        super().__init__()

    # def connect_ui(self, prompt_box: "PromptBox") -> None:
    #     prompt_box.finished.connect(
    #         lambda res: self.done.emit(res == QtWidgets.QMessageBox.StandardButton.Ok)
    #     )
    #     self.start.connect(prompt_box.confirm)

    # def connect_actions(
    #     self,
    #     start: Optional[Callable[[str, str], None]],
    #     done: Optional[Callable[[bool], None]],
    # ) -> "PromptUiConnection":
    #     con = PromptUiConnection(self)
    #     if start:
    #         con.start = self.start.connect(start)
    #     if done:
    #         con.done = self.done.connect(done)
    #     return con


# @dataclass
# class PromptUiConnection:
#     prompt_ui: PromptUi
#     start: Optional[QMetaObject.Connection] = None
#     done: Optional[QMetaObject.Connection] = None

#     def disconnect_actions(self) -> None:
#         if self.start:
#             self.prompt_ui.start.disconnect()
#             self.start = None
#         if self.done:
#             self.prompt_ui.done.disconnect()
#             self.done = None


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
