import webbrowser
from typing import Optional

from pynitrokey.nk3.utils import Version
from pynitrokey.updates import Release, Repository
from PySide6.QtCore import Slot
from PySide6.QtWidgets import QWidget

from nitrokeyapp import __version__
from nitrokeyapp.logger import save_log
from nitrokeyapp.qt_utils_mix_in import QtUtilsMixIn

REPOSITORY_OWNER = "Nitrokey"
REPOSITORY_NAME = "nitrokey-app2"
REPOSITORY = Repository(owner=REPOSITORY_OWNER, name=REPOSITORY_NAME)


class WelcomeTab(QtUtilsMixIn, QWidget):
    def __init__(self, log_file: str, parent: Optional[QWidget] = None) -> None:
        QWidget.__init__(self, parent)
        QtUtilsMixIn.__init__(self)

        self.log_file = log_file

        # self.ui === self -> this tricks mypy due to monkey-patching self
        self.ui = self.load_ui("welcome_tab.ui", self)
        self.ui.buttonSaveLog.pressed.connect(self.save_log)
        self.ui.VersionNr.setText(__version__)
        self.ui.CheckUpdate.pressed.connect(self.check_update)

    def check_update(self) -> None:
        self.c_version = __version__
        try:
            self.get_release = REPOSITORY.get_latest_release()
        except Exception:
            self.ui.CheckUpdate.setText("No connection")
            return

        self.release = Release
        self.last_release = self.release.__str__(self.get_release)

        self.n_version = self.last_release
        self.n_version = self.n_version[1:]

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

    @Slot()
    def save_log(self) -> None:
        save_log(self.log_file, self)
