from PySide6 import QtCore, QtWidgets
from PySide6.QtCore import QObject, Qt, Signal, Slot

from nitrokeyapp.qt_utils_mix_in import QtUtilsMixIn
from nitrokeyapp.utils import resolved_color_scheme


def _status_colors() -> tuple[str, str]:
    """(normal, error) status text color, taken from the palettes in __main__.py"""
    if resolved_color_scheme() == Qt.ColorScheme.Dark:
        return "#c9d1d9", "#ff6b5b"
    return "#24292f", "#c0392b"


class InfoUi(QObject):
    error = Signal(str)
    info = Signal(str)
    pin_cached = Signal()
    pin_cleared = Signal()
    pin_pressed = Signal()

    def __init__(self) -> None:
        super().__init__()


class InfoBox(QObject):
    pin_pressed = Signal()

    def __init__(
        self,
        information_frame: QtWidgets.QWidget,
        icon: QtWidgets.QLabel,
        status: QtWidgets.QLabel,
        device: QtWidgets.QLabel,
        pin_icon: QtWidgets.QPushButton,
    ) -> None:
        super().__init__()
        self.information_frame = information_frame
        self.information_frame.show()

        self.status = status
        self.status.setText("")
        self.status.hide()
        self.device = device

        self.icon = icon
        self.icon.setFixedSize(QtCore.QSize(16, 16))
        self.icon.hide()

        self.icon_name = "info.svg"
        self.is_error = False

        self.pin_icon = pin_icon
        self.pin_icon.setStyleSheet(
            "QPushButton { background-color: none; border: 0; margin: 0; padding: 0; width: 16; height: 16; }"
        )
        self.set_pin_icon(False)
        self.pin_icon.hide()
        self.pin_icon.clicked.connect(self.pin_pressed)

        # self.send_status.connect(lambda s: self.set_status(s))
        # self.send_error_status.connect(self.set_error_status)

        # self.information_frame.setStyleSheet("background-color:#666666; border: 0;");

        self.hide_timer = QtCore.QTimer(self)
        self.hide_timer.setSingleShot(True)
        self.hide_timer.setInterval(7000)
        self.hide_timer.timeout.connect(self.hide_status)

    @Slot(str, int, str)
    def set_status(self, text: str, timeout: int = 7000, icon: str | None = None) -> None:
        self.show_status(text, timeout, icon or "info.svg", is_error=False)

    @Slot(str)
    def set_error_status(self, text: str) -> None:
        self.show_status(text, 12000, "warning.svg", is_error=True)

    def show_status(self, text: str, timeout: int, icon: str, is_error: bool) -> None:
        self.status.setText(text)
        self.icon_name = icon
        self.is_error = is_error
        self.apply_theme()

        self.status.show()
        self.information_frame.show()
        self.icon.show()

        if self.hide_timer.isActive():
            self.hide_timer.stop()
        self.hide_timer.setInterval(timeout)
        self.hide_timer.start()

    def apply_theme(self) -> None:
        """set the status color and icon matching the active color scheme"""
        normal, error = _status_colors()
        if self.is_error:
            self.status.setStyleSheet(f"color: {error}; font-weight: bold;")
        else:
            self.status.setStyleSheet(f"color: {normal};")
        self.icon.setPixmap(QtUtilsMixIn.get_pixmap(self.icon_name))

    @Slot()
    def refresh_theme(self) -> None:
        """re-resolve the status color and icon after a light/dark mode switch"""
        if self.status.text():
            self.apply_theme()

    @Slot()
    def hide_status(self) -> None:
        self.status.setText("")
        self.status.setStyleSheet("")
        self.is_error = False
        self.icon.hide()

    @Slot()
    def set_touch_status(self) -> None:
        self.set_status("Press your Nitrokey to confirm...", 15000, "touch.svg")

    @Slot()
    def hide_touch(self) -> None:
        # TODO: no good
        if "Press" in self.status.text():
            self.hide_status()

    def set_device(self, text: str) -> None:
        self.device.setText(text)

    def hide_device(self) -> None:
        self.device.setText("")
        self.pin_icon.hide()

    def hide(self) -> None:
        self.device.setText("")
        self.hide_status()
        self.pin_icon.hide()

    @Slot()
    def unset_pin_icon(self) -> None:
        self.set_pin_icon(False)

    @Slot()
    def set_pin_icon(self, pin_cached: bool = True) -> None:
        if pin_cached:
            self.pin_icon.setIcon(QtUtilsMixIn.get_qicon("dialpad.svg"))
            self.pin_icon.setToolTip("Passwords PIN is cached - click to clear")
        else:
            self.pin_icon.setIcon(QtUtilsMixIn.get_qicon("dialpad_off.svg"))
            self.pin_icon.setToolTip("Passwords PIN locked")
        self.pin_icon.show()
