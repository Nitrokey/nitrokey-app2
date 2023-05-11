import sys
from contextlib import contextmanager
from types import TracebackType
from typing import Any, Callable, Generator, Optional, Type

from PyQt5 import QtWidgets

import nitrokeyapp.ui.resources_rc  # noqa: F401
from nitrokeyapp.gui import GUI
from nitrokeyapp.logger import init_logging


@contextmanager
def exception_handler(
    hook: Callable[[Type[BaseException], BaseException, Optional[TracebackType]], Any],
) -> Generator[None, None, None]:
    old_hook = sys.excepthook
    sys.excepthook = hook
    try:
        yield
    finally:
        sys.excepthook = old_hook


def main() -> None:
    app = QtWidgets.QApplication(sys.argv)
    init_logging()
    window = GUI(app)  # noqa: F841
    with exception_handler(window.trigger_handle_exception.emit):
        app.exec()


if __name__ == "__main__":
    main()
