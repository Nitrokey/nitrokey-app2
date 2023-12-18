from PySide6 import QtWidgets
from PySide6.QtCore import Slot

from nitrokeyapp import __version__
from nitrokeyapp.logger import save_log
from nitrokeyapp.qt_utils_mix_in import QtUtilsMixIn

## unused ?


class AboutDialog(QtUtilsMixIn, QtWidgets.QDialog):
    def __init__(self, log_file: str, qt_app: QtWidgets.QApplication) -> None:
        QtWidgets.QDialog.__init__(self, parent)
        QtUtilsMixIn.__init__(self)

        self.log_file = log_file

        self.app = qt_app
        self.ui = self.load_ui("aboutdialog.ui", parent)

        self.ui.ButtonOK.clicked.connect(self.close)
        self.ui.buttonSaveLog.pressed.connect(self.save_log)
        self.ui.VersionLabel.setText(__version__)

    @Slot()
    def save_log(self) -> None:
        save_log(self.log_file, self)
