import sys
from collections.abc import Callable, Generator
from contextlib import contextmanager
from types import TracebackType
from typing import Any

import click
from PySide6 import QtWidgets

from nitrokeyapp import __version__
from nitrokeyapp.gui import GUI
from nitrokeyapp.logger import init_logging, log_environment

CONTEXT_SETTINGS = {"help_option_names": ["-h", "--help"], "ignore_unknown_options": True}


@contextmanager
def exception_handler(
    hook: Callable[[type[BaseException], BaseException, TracebackType | None], Any],
) -> Generator[None, None, None]:
    old_hook = sys.excepthook
    sys.excepthook = hook
    try:
        yield
    finally:
        sys.excepthook = old_hook


def run_gui(argv: list[str]) -> None:
    app = QtWidgets.QApplication(argv)
    app.setDesktopFileName("com.nitrokey.nitrokey-app2")

    with init_logging() as log_file:
        log_environment()

        window = GUI(app, log_file)
        with exception_handler(window.trigger_handle_exception.emit):
            app.exec()


@click.command(context_settings=CONTEXT_SETTINGS)
@click.version_option(__version__, "-V", "--version")
@click.argument("qt_args", nargs=-1, type=click.UNPROCESSED)
def main(qt_args: tuple[str, ...]) -> None:
    """Graphical application to manage Nitrokey devices.

    Without arguments the graphical user interface is started. Any additional
    arguments are passed on to Qt, for example: -platform offscreen
    """
    run_gui([sys.argv[0], *qt_args])


if __name__ == "__main__":
    main()
