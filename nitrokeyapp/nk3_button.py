from PyQt5 import QtGui, QtWidgets
from PyQt5.QtCore import QSize

from nitrokeyapp.device_data import DeviceData


class Nk3Button(QtWidgets.QPushButton):
    def __init__(
        self,
        data: DeviceData,
    ) -> None:
        super().__init__(
            QtGui.QIcon(":/images/icon/usb_new.png"),
            "Nitrokey 3: " f"{str(data.uuid)[:5]}",
        )
        self.data = data
        # needs to create button in the vertical navigation with the nitrokey type and serial number as text
        self.setFixedSize(184, 40)
        self.setIconSize(QSize(20, 20))
        self.setStyleSheet(
            "border :4px solid ;"
            "border-color : #474642;"
            "border-width: 2px;"
            "border-radius: 5px;"
            "font-size: 14pt;"
        )
        # "font-weight: bold;")
