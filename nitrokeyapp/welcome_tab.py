import webbrowser

from nitrokey.trussed import Version
from nitrokey.updates import Repository
from PySide6.QtCore import Slot
from PySide6.QtWidgets import QWidget

from nitrokeyapp import __version__
from nitrokeyapp.logger import save_log
from nitrokeyapp.qt_utils_mix_in import QtUtilsMixIn

REPOSITORY_OWNER = "Nitrokey"
REPOSITORY_NAME = "nitrokey-app2"
REPOSITORY = Repository(owner=REPOSITORY_OWNER, name=REPOSITORY_NAME)


class WelcomeTab(QtUtilsMixIn, QWidget):
    def __init__(self, log_file: str, parent: QWidget | None = None) -> None:
        QWidget.__init__(self, parent)
        QtUtilsMixIn.__init__(self)

        self.log_file = log_file

        # self.ui === self -> this tricks mypy due to monkey-patching self
        self.ui = self.load_ui("welcome_tab.ui", self)
        self.ui.buttonSaveLog.pressed.connect(self.save_log)
        self.ui.VersionNr.setText(__version__)
        self.ui.CheckUpdate.pressed.connect(self.check_update)

    def check_update(self) -> None:
        try:
            release = REPOSITORY.get_latest_release()
        except Exception:
            self.ui.CheckUpdate.setText("No connection")
            return

        current = Version.from_str(__version__)
        latest = Version.from_v_str(release.tag)

        if current < latest:
            self.ui.CheckUpdate.setText("update available")
            self.ui.CheckUpdate.pressed.connect(
                lambda: webbrowser.open("https://github.com/Nitrokey/nitrokey-app2/releases")
            )
        else:
            self.ui.CheckUpdate.setText("App is up to date")

    @Slot()
    def save_log(self) -> None:
        save_log(self.log_file, self)
