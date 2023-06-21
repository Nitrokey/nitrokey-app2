from traceback import format_exception
from types import TracebackType
from typing import Optional, Type

from PyQt5.QtCore import pyqtSlot
from PyQt5.QtWidgets import QDialog, QDialogButtonBox, QPushButton, QWidget

from nitrokeyapp.logger import save_log
from nitrokeyapp.ui.error_dialog import Ui_ErrorDialog


class ErrorDialog(QDialog):
    def __init__(self, log_file: str, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)

        self.log_file = log_file

        self.ui = Ui_ErrorDialog()
        self.ui.setupUi(self)

        self.button_save_log = QPushButton("Save Log File", self)
        self.button_save_log.pressed.connect(self.save_log)

        self.ui.buttonBox.addButton(
            self.button_save_log, QDialogButtonBox.ButtonRole.ActionRole
        )

    def set_exception(
        self,
        ty: Type[BaseException],
        e: BaseException,
        tb: Optional[TracebackType],
    ) -> None:
        lines = format_exception(ty, e, tb)
        self.ui.textEditDetails.setPlainText("".join(lines))

    @pyqtSlot()
    def save_log(self) -> None:
        save_log(self.log_file, self)
