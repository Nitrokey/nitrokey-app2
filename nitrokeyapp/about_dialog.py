from PyQt5 import QtWidgets
from PyQt5.QtCore import pyqtSlot

from nitrokeyapp import __version__
from nitrokeyapp.logger import save_log
from nitrokeyapp.qt_utils_mix_in import QtUtilsMixIn
from nitrokeyapp.ui.aboutdialog import Ui_AboutDialog


class AboutDialog(QtUtilsMixIn, QtWidgets.QDialog):
    def __init__(self, log_file: str, qt_app: QtWidgets.QApplication) -> None:
        QtWidgets.QDialog.__init__(self)
        QtUtilsMixIn.__init__(self)

        self.log_file = log_file

        self.app = qt_app
        self.ui = Ui_AboutDialog()
        self.ui.setupUi(self)
        self.ui.ButtonOK.clicked.connect(self.close)
        self.ui.buttonSaveLog.pressed.connect(self.save_log)
        self.ui.VersionLabel.setText(__version__)

    @pyqtSlot()
    def save_log(self) -> None:
        save_log(self.log_file, self)
