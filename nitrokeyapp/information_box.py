from typing import Optional

from PySide6 import QtCore, QtWidgets
from PySide6.QtCore import QObject, Slot

from nitrokeyapp.qt_utils_mix_in import QtUtilsMixIn


class InfoBox(QObject):
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
        self.device = device

        self.icon = icon
        self.icon.setFixedSize(QtCore.QSize(16, 16))
        self.icon.hide()

        self.pin_icon = pin_icon
        self.pin_icon.setStyleSheet(
            "QPushButton { background-color: none; border: 0; margin: 0; padding: 0; width: 16; height: 16; }"
        )
        self.set_pin_icon(False)
        self.pin_icon.hide()

        # self.information_frame.setStyleSheet("background-color:#666666; border: 0;");

        self.hide_timer = QtCore.QTimer(self)
        self.hide_timer.setSingleShot(True)
        self.hide_timer.setInterval(7000)
        self.hide_timer.timeout.connect(self.hide_status)

    @Slot(str, int, str)
    def set_status(
        self, text: str, timeout: int = 7000, icon: Optional[str] = None
    ) -> None:
        self.status.setText(text)
        self.status.show()
        self.information_frame.show()
        if not icon:
            self.icon.setPixmap(QtUtilsMixIn.get_pixmap("info.svg"))
        else:
            self.icon.setPixmap(QtUtilsMixIn.get_pixmap(icon))
        self.icon.show()

        if self.hide_timer.isActive():
            self.hide_timer.stop()
        self.hide_timer.setInterval(timeout)
        self.hide_timer.start()

    @Slot(str)
    def set_error_status(self, text: str) -> None:
        icon = "warning.svg"
        self.set_status(text, timeout=12000, icon=icon)

    @Slot()
    def hide_status(self) -> None:
        self.status.setText("")
        self.icon.hide()

    @Slot()
    def set_touch_status(self) -> None:
        self.set_status(
            "Press your Nitrokey to confirm...", timeout=15000, icon="touch.svg"
        )

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

    @Slot(bool)
    def set_pin_icon(self, pin_cached: bool = True) -> None:
        if pin_cached:
            self.pin_icon.setIcon(QtUtilsMixIn.get_qicon("dialpad.svg"))
            self.pin_icon.setToolTip("Passwords PIN is cached - click to clear")
        else:
            self.pin_icon.setIcon(QtUtilsMixIn.get_qicon("dialpad_off.svg"))
            self.pin_icon.setToolTip("Passwords PIN locked")
        self.pin_icon.show()
