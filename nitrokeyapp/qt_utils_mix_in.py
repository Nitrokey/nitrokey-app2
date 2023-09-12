from typing import Optional, Type, TypeVar

from PyQt5 import QtGui, QtWidgets, uic
from PyQt5.QtCore import QObject, QSize

Q = TypeVar("Q", bound=QObject)


class QtUtilsMixIn:
    def __init__(self) -> None:
        self.widgets: dict[str, QObject] = {}

        # ensure we are always mixed-in with an QObject-ish class
        # TODO: should we restrict this further to QWidget?
        assert isinstance(self, QObject)

    def user_warn(
        self,
        msg: str,
        title: Optional[str] = None,
        parent: Optional[QtWidgets.QWidget] = None,
    ) -> None:
        if not parent and isinstance(self, QtWidgets.QWidget):
            parent = self
        QtWidgets.QMessageBox.warning(parent, title or msg, msg)

    def user_info(
        self,
        msg: str,
        title: Optional[str] = None,
        parent: Optional[QtWidgets.QWidget] = None,
    ) -> None:
        if not parent and isinstance(self, QtWidgets.QWidget):
            parent = self
        QtWidgets.QMessageBox.information(parent, title or msg, msg)

    def user_err(
        self,
        msg: str,
        title: Optional[str] = None,
        parent: Optional[QtWidgets.QWidget] = None,
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

    def load_ui(self, filename: str, qt_obj: Type) -> bool:
        uic.loadUi(filename, qt_obj)
        return True

    def collapse(
        self, frame: QtWidgets.QWidget, expand_button: QtWidgets.QPushButton
    ) -> None:
        # Find out if the state is on or off
        state = expand_button.isChecked()
        if not state:
            expand_button.setIcon(QtGui.QIcon(":/icons/right_arrow.png"))
            expand_button.setIconSize(QSize(12, 12))
            frame.setFixedHeight(0)
            # Set window Height
            # self.setFixedHeight(self.sizeHint().height())
        else:
            expand_button.setIcon(QtGui.QIcon(":/icons/down_arrow.png"))
            oSize = frame.sizeHint()
            frame.setFixedHeight(oSize.height())
            # Set window Height
            # self.setFixedHeight(self.sizeHint().height())
