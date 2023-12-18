from traceback import format_exception
from types import TracebackType
from typing import Optional, Type

from PySide6.QtCore import Slot
from PySide6.QtWidgets import QDialog, QDialogButtonBox, QPushButton, QWidget

from nitrokeyapp.logger import save_log
from nitrokeyapp.qt_utils_mix_in import QtUtilsMixIn


class ErrorDialog(QtUtilsMixIn, QDialog):
    def __init__(self, log_file: str, parent: Optional[QWidget] = None) -> None:
        QDialog.__init__(self, parent)
        QtUtilsMixIn.__init__(self)

        self.log_file = log_file

        # self.ui === self -> this tricks mypy due to monkey-patching self
        self.ui = self.load_ui("error_dialog.ui", self)

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
        self.show()

    @Slot()
    def save_log(self) -> None:
        save_log(self.log_file, self)
