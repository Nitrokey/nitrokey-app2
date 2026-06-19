from pathlib import Path
from typing import Any, Optional, Type, TypeVar

from PySide6 import QtGui, QtWidgets
from PySide6.QtCore import QDir, QObject, QSize, Qt

from nitrokeyapp.ui_loader import UiLoader

Q = TypeVar("Q", bound=QObject)

# icons that ship a light- and dark-mode variant under ui/icons/{light,dark}_mode/
_THEMED_ICONS: dict[str, tuple[str, str]] = {
    "app_logo.svg": ("light_mode/app_logo.svg", "dark_mode/app_logo_white.svg"),
    "close.svg": ("light_mode/close.svg", "dark_mode/close_colored.svg"),
    "content_copy.svg": ("light_mode/content_copy.svg", "dark_mode/content_copy_colored.svg"),
    "delete.svg": ("light_mode/delete.svg", "dark_mode/delete_white.svg"),
    "dialpad.svg": ("light_mode/dialpad.svg", "dark_mode/dialpad_white.svg"),
    "dialpad_off.svg": ("light_mode/dialpad_off.svg", "dark_mode/dialpad_off_white.svg"),
    "done.svg": ("light_mode/done.svg", "dark_mode/done_colored.svg"),
    "down_arrow.svg": ("light_mode/down_arrow.svg", "dark_mode/down_arrow_colored.svg"),
    "edit.svg": ("light_mode/edit.svg", "dark_mode/edit_colored.svg"),
    "lock.svg": ("light_mode/lock.svg", "dark_mode/lock_colored.svg"),
    "lock_open.svg": ("light_mode/lock_open.svg", "dark_mode/lock_open_colored.svg"),
    "refresh.svg": ("light_mode/refresh.svg", "dark_mode/refresh_colored.svg"),
    "right_arrow.svg": ("light_mode/right_arrow.svg", "dark_mode/right_arrow_colored.svg"),
    "visibility.svg": ("light_mode/visibility.svg", "dark_mode/visibility_colored.svg"),
    "visibility_off.svg": ("light_mode/visibility_off.svg", "dark_mode/visibility_off_colored.svg"),
}


class QtUtilsMixIn:
    def __init__(self) -> None:
        self.widgets: dict[str, QObject] = {}

        # ensure we are always mixed-in with an QObject-ish class
        # TODO: should we restrict this further to QWidget?
        assert isinstance(self, QObject)

    @staticmethod
    def load_ui(filename: str, base_instance: Optional[QtWidgets.QWidget] = None) -> Any:
        # returning `Any` to avoid  `mypy` going crazy due to monkey-patching
        loader = UiLoader(base_instance, customWidgets=None)
        p_dir = (Path(__file__).parent / "ui").absolute()
        loader.setWorkingDirectory(QDir(p_dir.as_posix()))
        p_file = p_dir / filename
        return loader.load(p_file.as_posix())

    @staticmethod
    def _icon_relpath(filename: str) -> str:
        variants = _THEMED_ICONS.get(filename)
        if variants is None:
            return filename
        light, dark = variants
        app = QtWidgets.QApplication.instance()
        is_dark = (
            app is not None and app.styleHints().colorScheme() == Qt.ColorScheme.Dark  # type: ignore [attr-defined]
        )
        return dark if is_dark else light

    @staticmethod
    def get_qicon(filename: str) -> QtGui.QIcon:
        p = Path(__file__).parent / "ui" / "icons" / QtUtilsMixIn._icon_relpath(filename)
        return QtGui.QIcon(p.as_posix())

    @staticmethod
    def get_pixmap(filename: str) -> QtGui.QPixmap:
        p = Path(__file__).parent / "ui" / "icons" / QtUtilsMixIn._icon_relpath(filename)
        return QtGui.QPixmap(p.as_posix())

    def user_warn(
        self, msg: str, title: Optional[str] = None, parent: Optional[QtWidgets.QWidget] = None
    ) -> None:
        if not parent and isinstance(self, QtWidgets.QWidget):
            parent = self
        QtWidgets.QMessageBox.warning(parent, title or msg, msg)

    def user_info(
        self, msg: str, title: Optional[str] = None, parent: Optional[QtWidgets.QWidget] = None
    ) -> None:
        if not parent and isinstance(self, QtWidgets.QWidget):
            parent = self
        QtWidgets.QMessageBox.information(parent, title or msg, msg)

    def user_err(
        self, msg: str, title: Optional[str] = None, parent: Optional[QtWidgets.QWidget] = None
    ) -> None:
        if not parent and isinstance(self, QtWidgets.QWidget):
            parent = self
        QtWidgets.QMessageBox.critical(parent, title or msg, msg)

    def get_widget(self, qt_cls: Type[Q], name: str = "") -> Q:
        """while finding widgets, why not cache them into a map"""
        widget = self.widgets.get(name)
        if not widget:
            # ensure `self` will always be mixed-in with a QObject derived class
            assert isinstance(self, QObject)
            # TODO: what should we do if this is None?
            widget = self.findChild(qt_cls, name)  # type: ignore
            assert widget
            self.widgets[name] = widget
        return widget  # type: ignore

    def collapse(self, frame: QtWidgets.QWidget, expand_button: QtWidgets.QPushButton) -> None:
        # Find out if the state is on or off
        state = expand_button.isChecked()
        if not state:
            expand_button.setIcon(self.get_qicon("right_arrow.svg"))
            expand_button.setIconSize(QSize(12, 12))
            frame.setFixedHeight(0)
            # Set window Height
            # self.setFixedHeight(self.sizeHint().height())
        else:
            expand_button.setIcon(self.get_qicon("down_arrow.svg"))
            oSize = frame.sizeHint()
            frame.setFixedHeight(oSize.height())
            # Set window Height
            # self.setFixedHeight(self.sizeHint().height())
