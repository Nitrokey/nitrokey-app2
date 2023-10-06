from typing import Optional

from PyQt5.QtCore import pyqtSlot
from PyQt5.QtWidgets import QWidget

from nitrokeyapp import __version__
from nitrokeyapp.logger import save_log

# from pynitrokey.nk3.utils import Version
from nitrokeyapp.qt_utils_mix_in import QtUtilsMixIn
from nitrokeyapp.ui.welcome_tab import Ui_WelcomeTab

# from urllib.request import urlopen


class WelcomeTab(QtUtilsMixIn, QWidget):
    def __init__(self, parent: Optional[QWidget], log_file: str) -> None:
        QWidget.__init__(self, parent)
        QtUtilsMixIn.__init__(self)

        self.log_file = log_file

        self.ui = Ui_WelcomeTab()
        self.ui.setupUi(self)
        self.ui.buttonSaveLog.pressed.connect(self.save_log)
        self.ui.VersionNr.setText(__version__)

    #   self.ui.CheckUpdate.pressed.connect(self.check_nversion)

    # def check_nversion(self) -> None:
    #     self.nversion = urlopen('https://raw.githubusercontent.com/Nitrokey/nitrokey-app2/main/nitrokeyapp/VERSION').read()
    #     self.nversion = str(self.nversion, encoding='utf-8')
    #     self.nversion = (self.nversion[:-1])
    #     self.check_update(self)
    #     print (self.nversion)
    #     print (type(self.nversion))

    # def check_update(self) -> None:

    @pyqtSlot()
    def save_log(self) -> None:
        save_log(self.log_file, self)
