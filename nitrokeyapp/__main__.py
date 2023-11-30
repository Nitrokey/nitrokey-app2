import sys
from contextlib import contextmanager
from types import TracebackType
from typing import Any, Callable, Generator, Optional, Type

from PySide6 import QtWidgets
from qt_material import apply_stylesheet

from nitrokeyapp import get_theme_path
from nitrokeyapp.gui import GUI
from nitrokeyapp.logger import init_logging, log_environment


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
    # set default material stylesheet if no system theme is set
    if not app.style().objectName() or app.style().objectName() == "fusion":
        apply_stylesheet(app, theme=get_theme_path())
    with init_logging() as log_file:
        log_environment()

        window = GUI(app, log_file)
        with exception_handler(window.trigger_handle_exception.emit):
            app.exec()


if __name__ == "__main__":
    main()
