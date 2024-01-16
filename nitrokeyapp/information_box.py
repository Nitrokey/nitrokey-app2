from typing import Optional
from PySide6 import QtCore, QtWidgets, QtGui
from PySide6.QtCore import Slot, QObject

from nitrokeyapp.qt_utils_mix_in import QtUtilsMixIn

class InfoBox(QObject):
    def __init__(
        self,
        information_frame: QtWidgets.QWidget,
        icon: QtWidgets.QLabel,
        status: QtWidgets.QLabel,
        device: QtWidgets.QLabel,
        pin_icon: QtWidgets.QPushButton
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
        self.pin_icon.setStyleSheet("QPushButton { background-color: none; border: 0; margin: 0; padding: 0; width: 16; height: 16; }")
        self.set_pin_icon(False)
        self.pin_icon.hide()

        #self.information_frame.setStyleSheet("background-color:#666666; border: 0;");

    def set_status(self, text: str, timeout: int = 5000, icon: Optional[QtGui.QPixmap] = None) -> None:
        self.status.setText(text)
        self.information_frame.show()
        if not icon:
            self.icon.setPixmap(QtUtilsMixIn.get_pixmap("info_FILL0_wght500_GRAD0_opsz40.png"))
        else:
            self.icon.setPixmap(QtUtilsMixIn.get_pixmap(icon))
        self.icon.show()
        QtCore.QTimer.singleShot(timeout, self.hide_status)

    def hide_status(self) -> None:
        self.status.setText("")
        self.icon.hide()

    def set_touch_status(self) -> None:
        self.set_status("Press your Nitrokey to confirm...",
            timeout=15000,
            icon="touch_app_FILL0_wght500_GRAD0_opsz40.png")

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
            self.pin_icon.setIcon(QtUtilsMixIn.get_qicon("lock_open_FILL0_wght500_GRAD0_opsz40.png"))
            self.pin_icon.setToolTip("Passwords PIN is cached - click to clear")
        else:
            self.pin_icon.setIcon(QtUtilsMixIn.get_qicon("encrypted_FILL0_wght500_GRAD0_opsz40.png"))
            self.pin_icon.setToolTip("Passwords PIN locked")
        self.pin_icon.show()

