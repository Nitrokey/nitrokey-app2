import json
import logging
import tempfile
import urllib.error
import urllib.request
import webbrowser
from pathlib import Path
from typing import Any

from nitrokey.trussed import Version
from PySide6.QtCore import QStandardPaths, Slot
from PySide6.QtWidgets import QWidget

from nitrokeyapp import __version__
from nitrokeyapp.logger import save_log
from nitrokeyapp.qt_utils_mix_in import QtUtilsMixIn

logger = logging.getLogger(__name__)

REPOSITORY_OWNER = "Nitrokey"
REPOSITORY_NAME = "nitrokey-app2"

RELEASES_URL = f"https://github.com/{REPOSITORY_OWNER}/{REPOSITORY_NAME}/releases"
LATEST_RELEASE_API_URL = (
    f"https://api.github.com/repos/{REPOSITORY_OWNER}/{REPOSITORY_NAME}/releases/latest"
)


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
            latest_tag = self.fetch_latest_tag()
        except Exception:
            logger.warning("failed to check for app updates", exc_info=True)
            self.ui.CheckUpdate.setText("No connection")
            return

        current = Version.from_str(__version__)
        latest = Version.from_v_str(latest_tag)

        if current < latest:
            self.ui.CheckUpdate.setText("update available")
            self.ui.CheckUpdate.pressed.connect(lambda: webbrowser.open(RELEASES_URL))
        else:
            self.ui.CheckUpdate.setText("App is up to date")

    def fetch_latest_tag(self) -> str:
        cache = self.read_cache()

        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": REPOSITORY_NAME,
        }
        if cache and cache.get("etag"):
            headers["If-None-Match"] = cache["etag"]

        request = urllib.request.Request(LATEST_RELEASE_API_URL, headers=headers)
        try:
            with urllib.request.urlopen(request, timeout=10) as response:
                data = json.load(response)
                etag = response.headers.get("ETag")
        except urllib.error.HTTPError as e:
            # 304: release unchanged since last check; 403: rate limited by
            # GitHub -> in both cases fall back to the cached release
            if e.code in (304, 403) and cache:
                return cache["tag"]
            raise

        tag = data["tag_name"]
        self.write_cache(tag, etag)
        return tag

    def cache_file(self) -> Path:
        base = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.CacheLocation)
        directory = Path(base) if base else Path(tempfile.gettempdir())
        directory.mkdir(parents=True, exist_ok=True)
        return directory / "latest-release.json"

    def read_cache(self) -> dict[str, Any] | None:
        try:
            with open(self.cache_file(), encoding="utf-8") as f:
                data = json.load(f)
        except (OSError, ValueError):
            return None
        if isinstance(data, dict) and "tag" in data:
            return data
        return None

    def write_cache(self, tag: str, etag: str | None) -> None:
        try:
            with open(self.cache_file(), "w", encoding="utf-8") as f:
                json.dump({"tag": tag, "etag": etag}, f)
        except OSError:
            logger.warning("failed to write release cache", exc_info=True)

    @Slot()
    def save_log(self) -> None:
        save_log(self.log_file, self)
