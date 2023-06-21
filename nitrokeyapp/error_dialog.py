from traceback import format_exception
from types import TracebackType
from typing import Optional, Type

from PyQt5.QtWidgets import QDialog, QWidget

from nitrokeyapp.ui.error_dialog import Ui_ErrorDialog


class ErrorDialog(QDialog):
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)

        self.ui = Ui_ErrorDialog()
        self.ui.setupUi(self)

    def set_exception(
        self,
        ty: Type[BaseException],
        e: BaseException,
        tb: Optional[TracebackType],
    ) -> None:
        lines = format_exception(ty, e, tb)
        self.ui.textEditDetails.setPlainText("".join(lines))
