"""Picks the language and installs the translation catalogs.

Has to run before the first widget is built, see nitrokeyapp.__main__.run_gui.
The catalogs themselves are documented in docs/translations.md.
"""

import logging
import os
from pathlib import Path

from PySide6.QtCore import QCoreApplication, QLibraryInfo, QLocale, QSettings, QTranslator

logger = logging.getLogger(__name__)

ORGANIZATION = "Nitrokey"
APPLICATION = "nitrokey-app2"

NKAPP_LANG = "NKAPP_LANG"
LANGUAGE_SETTING = "ui/language"

# the stored value that means "follow the system locale"
SYSTEM_LANGUAGE = ""

SOURCE_LANGUAGE = "en"

TRANSLATIONS_PATH = Path(__file__).parent / "translations"

APP_CATALOG = "nitrokeyapp"
QT_CATALOG = "qtbase"

# Qt does not take ownership of an installed translator, so keep a reference
_installed: list[QTranslator] = []


def settings() -> QSettings:
    """The application settings, stored as an ini file in the user's config directory."""
    return QSettings(
        QSettings.Format.IniFormat, QSettings.Scope.UserScope, ORGANIZATION, APPLICATION
    )


def forced_language() -> str | None:
    """The language enforced via NKAPP_LANG, or None; it beats the setting."""
    forced = os.environ.get(NKAPP_LANG, "").strip()
    return forced or None


def stored_language() -> str:
    """The language written by the selector, or :data:`SYSTEM_LANGUAGE`."""
    stored = settings().value(LANGUAGE_SETTING, SYSTEM_LANGUAGE)
    return str(stored) if stored else SYSTEM_LANGUAGE


def configured_language() -> str:
    """The language to use, or :data:`SYSTEM_LANGUAGE` to follow the system locale."""
    return forced_language() or stored_language()


def set_configured_language(language: str) -> None:
    """Store the language to use on the next start."""
    config = settings()
    if language:
        config.setValue(LANGUAGE_SETTING, language)
    else:
        config.remove(LANGUAGE_SETTING)
    config.sync()


def available_languages() -> list[str]:
    """The locale codes we can actually offer, the source language first.

    An untranslated catalog compiles to an empty .qm and would offer a choice
    that changes nothing, so it is skipped until a translation lands.
    """
    languages = set()
    for catalog in TRANSLATIONS_PATH.glob(f"{APP_CATALOG}_*.qm"):
        translator = QTranslator()
        if not translator.load(str(catalog)) or translator.isEmpty():
            logger.debug(f"skipping {catalog.name}: nothing translated in it")
            continue
        languages.add(catalog.stem[len(APP_CATALOG) + 1 :])
    languages.discard(SOURCE_LANGUAGE)
    return [SOURCE_LANGUAGE, *sorted(languages)]


def language_name(language: str) -> str:
    """A label for `language`, in that language itself, for the language selector."""
    if not language:
        return QCoreApplication.translate("i18n", "System language")
    if language == SOURCE_LANGUAGE:
        # Qt resolves a bare "en" to en_US and would call that "American English"
        return "English"

    name = QLocale(language).nativeLanguageName()
    if not name:
        return language
    return name[:1].upper() + name[1:]


def _load(locale: QLocale, catalog: str, directories: list[Path]) -> QTranslator | None:
    for directory in directories:
        translator = QTranslator()
        # QTranslator walks the fallback chain itself, so de_DE finds a de catalog
        if translator.load(locale, catalog, "_", str(directory)):
            logger.debug(f"loaded {catalog} catalog from {directory}")
            return translator
    logger.debug(f"no {catalog} catalog for {locale.name()}")
    return None


def resolved_language() -> str:
    """The language to load catalogs for.

    Without a usable setting this takes the first language the system says the
    user prefers that we can serve, counting the source language as servable:
    someone who prefers English over German must not get a half German
    application just because we ship a German catalog and no English one.
    """
    forced = forced_language()
    if forced:
        return forced

    available = set(available_languages())

    stored = stored_language()
    if stored in available:
        return stored
    if stored:
        logger.warning(f"no catalog for the selected language {stored!r}")

    for tag in QLocale.system().uiLanguages():
        name = QLocale(tag).name()
        language = name.split("_")[0]
        if language == SOURCE_LANGUAGE:
            return SOURCE_LANGUAGE
        for candidate in (name, language):
            if candidate in available:
                return candidate
    return SOURCE_LANGUAGE


def install_translators(app: QCoreApplication) -> None:
    """Install the application and Qt catalogs matching the configured language."""
    language = resolved_language()
    locale = QLocale(language)
    if configured_language():
        # an explicit choice also switches number and date formatting
        QLocale.setDefault(locale)

    setting = configured_language() or "system"
    logger.info(f"using locale {locale.name()} (language setting: {setting})")

    if language == SOURCE_LANGUAGE:
        logger.debug("the source language needs no catalogs")
        return

    # Qt's own strings (dialog buttons, context menus); prefer the installed Qt,
    # fall back to the copies we ship for the bundled builds
    qt_directories = [
        Path(QLibraryInfo.path(QLibraryInfo.LibraryPath.TranslationsPath)),
        TRANSLATIONS_PATH,
    ]
    for catalog, directories in ((QT_CATALOG, qt_directories), (APP_CATALOG, [TRANSLATIONS_PATH])):
        translator = _load(locale, catalog, directories)
        if translator is None:
            continue
        app.installTranslator(translator)
        _installed.append(translator)
