#!/usr/bin/env python3
"""Maintain the Qt Linguist catalogs of the application.

    update    refresh nitrokeyapp/translations/*.ts from the .py and .ui sources
    release   compile the .ts files into the .qm catalogs that ship with the app
    check     fail if `update` would change a .ts file (used by the CI)

Everything is driven by the tools that come with PySide6; see
docs/translations.md.
"""

import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PACKAGE = ROOT / "nitrokeyapp"
TRANSLATIONS = PACKAGE / "translations"

APP_CATALOG = "nitrokeyapp"
QT_CATALOG = "qtbase"

# the languages we maintain a catalog for; to add one, put its locale code here
# and run `make translations-update`
LANGUAGES = ("de",)

# relative locations keep the references stable across checkouts, -no-obsolete
# drops removed strings, so a .ts diff shows wording changes and nothing else
LUPDATE_OPTIONS = ["-locations", "relative", "-no-obsolete"]

LOAD_UI = re.compile(r"""load_ui\(\s*["']([^"']+\.ui)["']""")


def tool(name: str) -> str:
    """Locate one of the PySide6 command line tools."""
    candidates = [name, str(Path(sys.executable).parent / name)]
    for candidate in candidates:
        found = shutil.which(candidate)
        if found:
            return found
    raise SystemExit(f"{name} not found; is PySide6 installed in this environment?")


def python_sources() -> list[Path]:
    sources = (p for p in PACKAGE.rglob("*.py") if "__pycache__" not in p.parts)
    # sort on the posix form: sorting Path objects orders by the native separator
    # and lupdate writes the sources in the order it gets them
    return sorted(sources, key=lambda p: p.as_posix())


def ui_sources() -> list[Path]:
    """The .ui files that are actually loaded; the package also holds unused ones."""
    names = set()
    for source in python_sources():
        names.update(LOAD_UI.findall(source.read_text(encoding="utf-8")))

    files = []
    for name in sorted(names):
        path = PACKAGE / "ui" / name
        if not path.exists():
            raise SystemExit(f"{path} is loaded but does not exist")
        files.append(path)
    return files


def catalog(language: str) -> Path:
    return TRANSLATIONS / f"{APP_CATALOG}_{language}.ts"


def relative(paths: list[Path]) -> list[str]:
    return [p.relative_to(ROOT).as_posix() for p in paths]


def update() -> None:
    TRANSLATIONS.mkdir(parents=True, exist_ok=True)
    sources = relative(python_sources()) + relative(ui_sources())
    for language in LANGUAGES:
        destination = catalog(language)
        command = [tool("pyside6-lupdate"), *sources, *LUPDATE_OPTIONS, "-ts", str(destination)]
        subprocess.run(command, check=True, cwd=ROOT)


def release() -> None:
    missing = [language for language in LANGUAGES if not catalog(language).exists()]
    if missing:
        raise SystemExit(f"no catalog for {', '.join(missing)}; run `make translations-update`")

    for language in LANGUAGES:
        source = catalog(language)
        command = [
            tool("pyside6-lrelease"),
            str(source),
            "-qm",
            str(source.with_suffix(".qm")),
        ]
        subprocess.run(command, check=True, cwd=ROOT)

    copy_qt_catalogs()


def copy_qt_catalogs() -> None:
    """Ship Qt's own translations next to ours, for the bundled builds.

    A PyInstaller bundle does not necessarily contain the translations of the Qt
    installation, so without this the buttons of the standard dialogs would stay
    English even in a fully translated application.
    """
    from PySide6.QtCore import QLibraryInfo

    qt_translations = Path(QLibraryInfo.path(QLibraryInfo.LibraryPath.TranslationsPath))
    for language in LANGUAGES:
        source = qt_translations / f"{QT_CATALOG}_{language}.qm"
        if not source.exists():
            print(f"warning: Qt ships no {source.name}, skipping", file=sys.stderr)
            continue
        shutil.copyfile(source, TRANSLATIONS / source.name)


def check() -> None:
    """Re-run `update` in place, compare, and restore -- the locations lupdate
    writes are relative to the catalog, so it cannot be run in a scratch directory."""
    before = {
        language: catalog(language).read_bytes()
        for language in LANGUAGES
        if catalog(language).exists()
    }
    try:
        update()
        outdated = [
            language for language in LANGUAGES if catalog(language).read_bytes() != before.get(language)
        ]
    finally:
        for language in LANGUAGES:
            if language in before:
                catalog(language).write_bytes(before[language])
            elif catalog(language).exists():
                catalog(language).unlink()

    if outdated:
        raise SystemExit(
            f"the catalogs for {', '.join(outdated)} are out of date; "
            "run `make translations-update` and commit the result"
        )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["update", "release", "check"])
    arguments = parser.parse_args()

    {"update": update, "release": release, "check": check}[arguments.command]()


if __name__ == "__main__":
    main()
