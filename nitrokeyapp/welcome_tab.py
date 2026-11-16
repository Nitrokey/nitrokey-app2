import logging
import webbrowser

from nitrokey.trussed import Version
from PySide6.QtCore import Slot
from PySide6.QtWidgets import QWidget

from nitrokeyapp import __version__, release_check
from nitrokeyapp.logger import save_log
from nitrokeyapp.qt_utils_mix_in import QtUtilsMixIn

logger = logging.getLogger(__name__)

REPOSITORY_OWNER = "Nitrokey"
REPOSITORY_NAME = "nitrokey-app2"
RELEASES_URL = release_check.releases_url(REPOSITORY_OWNER, REPOSITORY_NAME)


class WelcomeTab(QtUtilsMixIn, QWidget):
    def __init__(self, log_file: str, parent: QWidget | None = None) -> None:
        QWidget.__init__(self, parent)
        QtUtilsMixIn.__init__(self)

        self.log_file = log_file
        self.update_available = False

        # self.ui === self -> this tricks mypy due to monkey-patching self
        self.ui = self.load_ui("welcome_tab.ui", self)
        self.refresh_icons()
        self.ui.buttonSaveLog.pressed.connect(self.save_log)
        self.ui.VersionNr.setText(__version__)
        self.ui.CheckUpdate.pressed.connect(self.check_update)

    def refresh_icons(self) -> None:
        """re-resolve all themed icons, e.g. after a light/dark mode switch"""
        self.ui.AppIcon.setPixmap(self.get_pixmap("app_logo.svg"))

    def check_update(self) -> None:
        if self.update_available:
            # the button now leads to the download page, no need to ask GitHub again
            webbrowser.open(RELEASES_URL)
            return

        try:
            tag = release_check.get_latest_tag(REPOSITORY_OWNER, REPOSITORY_NAME)
            latest = Version.from_v_str(tag)
            current = Version.from_str(__version__)
        except release_check.RateLimited as e:
            logger.warning(f"update check was rate limited: {e}")
            self.ui.CheckUpdate.setText("Try again later")
            return
        except release_check.Unreachable as e:
            logger.warning(f"update check failed, GitHub is not reachable: {e}")
            self.ui.CheckUpdate.setText("No connection")
            return
        except (release_check.ReleaseCheckError, ValueError) as e:
            logger.warning(f"update check failed: {e}")
            self.ui.CheckUpdate.setText("Check failed")
            return

        if current < latest:
            self.update_available = True
            self.ui.CheckUpdate.setText("update available")
        else:
            self.ui.CheckUpdate.setText("App is up to date")

    @Slot()
    def save_log(self) -> None:
        save_log(self.log_file, self)
