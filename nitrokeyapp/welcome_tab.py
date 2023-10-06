import webbrowser
from typing import Optional
from urllib.request import urlopen

from pynitrokey.nk3.utils import Version
from PyQt5.QtCore import pyqtSlot
from PyQt5.QtWidgets import QWidget

from nitrokeyapp import __version__
from nitrokeyapp.logger import save_log
from nitrokeyapp.qt_utils_mix_in import QtUtilsMixIn
from nitrokeyapp.ui.welcome_tab import Ui_WelcomeTab


class WelcomeTab(QtUtilsMixIn, QWidget):
    def __init__(self, parent: Optional[QWidget], log_file: str) -> None:
        QWidget.__init__(self, parent)
        QtUtilsMixIn.__init__(self)

        self.log_file = log_file

        self.ui = Ui_WelcomeTab()
        self.ui.setupUi(self)
        self.ui.buttonSaveLog.pressed.connect(self.save_log)
        self.ui.VersionNr.setText(__version__)
        self.ui.CheckUpdate.pressed.connect(self.check_update)

    def check_update(self) -> None:
        self.c_version = __version__
        self.n_version = urlopen(
            "https://raw.githubusercontent.com/Nitrokey/nitrokey-app2/main/nitrokeyapp/VERSION"
        ).read()
        self.n_version = str(self.n_version, encoding="utf-8")
        self.n_version = self.n_version[:-1]

        self.c_version_v = Version.from_str(self.c_version)
        self.n_version_v = Version.from_str(self.n_version)

        if Version.__lt__(self.c_version_v, self.n_version_v):
            self.ui.CheckUpdate.setText("update available")
            self.ui.CheckUpdate.pressed.connect(
                lambda: webbrowser.open(
                    "https://github.com/Nitrokey/nitrokey-app2/releases"
                )
            )
        else:
            self.ui.CheckUpdate.setText("App is up to date")

    @pyqtSlot()
    def save_log(self) -> None:
        save_log(self.log_file, self)
