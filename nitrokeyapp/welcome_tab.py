import logging
import webbrowser

from nitrokey.trussed import Version
from nitrokey.updates import Repository
from PySide6.QtCore import Qt, Slot
from PySide6.QtWidgets import QWidget

from nitrokeyapp import __version__, i18n
from nitrokeyapp.logger import save_log
from nitrokeyapp.qt_utils_mix_in import QtUtilsMixIn

logger = logging.getLogger(__name__)

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
        self.refresh_icons()
        self.ui.buttonSaveLog.pressed.connect(self.save_log)
        self.ui.VersionNr.setText(__version__)
        self.ui.CheckUpdate.pressed.connect(self.check_update)
        self.init_language_selection()

    def init_language_selection(self) -> None:
        """Fill the language selector and remember what the user picks.

        A change only takes effect on the next start, which the hint next to the
        selector says once something was actually changed.
        """
        combo = self.ui.SelectLanguage
        self.ui.LanguageHint.hide()

        forced = i18n.forced_language()
        # what the application is running in, to tell a real change from a no-op
        self.active_language = i18n.resolved_language()

        self.selected_language = forced or i18n.stored_language()
        languages = [i18n.SYSTEM_LANGUAGE, *i18n.available_languages()]
        if self.selected_language not in languages:
            if forced is not None:
                # NKAPP_LANG may name a language whose catalog holds nothing yet
                languages.append(self.selected_language)
            else:
                logger.warning(f"no catalog for the selected language {self.selected_language!r}")
                self.selected_language = i18n.SYSTEM_LANGUAGE

        if len(languages) < 3 and forced is None:
            logger.info("no translations installed, hiding the language selector")
            self.ui.frame_language.hide()
            return

        for language in languages:
            combo.addItem(i18n.language_name(language), language)
        combo.setCurrentIndex(combo.findData(self.selected_language))

        if forced is not None:
            combo.setEnabled(False)
            combo.setToolTip(
                self.tr("The language is set to {0} by {1}.").format(forced, i18n.NKAPP_LANG)
            )
            return

        combo.currentIndexChanged.connect(self.language_selected)

    @Slot(int)
    def language_selected(self, index: int) -> None:
        if index < 0:
            return
        language = self.ui.SelectLanguage.itemData(index, Qt.ItemDataRole.UserRole)
        i18n.set_configured_language(language)
        # "System language" and the language it resolves to are the same choice,
        # so compare what the next start would use
        self.ui.LanguageHint.setVisible(i18n.resolved_language() != self.active_language)

    def refresh_icons(self) -> None:
        """re-resolve all themed icons, e.g. after a light/dark mode switch"""
        self.ui.AppIcon.setPixmap(self.get_pixmap("app_logo.svg"))

    def check_update(self) -> None:
        try:
            release = REPOSITORY.get_latest_release()
        except Exception:
            self.ui.CheckUpdate.setText(self.tr("No connection"))
            return

        current = Version.from_str(__version__)
        latest = Version.from_v_str(release.tag)

        if current < latest:
            self.ui.CheckUpdate.setText(self.tr("Update available"))
            self.ui.CheckUpdate.pressed.connect(
                lambda: webbrowser.open("https://github.com/Nitrokey/nitrokey-app2/releases")
            )
        else:
            self.ui.CheckUpdate.setText(self.tr("App is up to date"))

    @Slot()
    def save_log(self) -> None:
        save_log(self.log_file, self)
