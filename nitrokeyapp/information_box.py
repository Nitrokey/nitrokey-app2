from PySide6 import QtCore, QtWidgets


class InfoBox:
    def __init__(
        self,
        information_frame: QtWidgets.QWidget,
        icon: QtWidgets.QWidget,
        status: QtWidgets.QLabel,
        device: QtWidgets.QLabel
    ) -> None:
        self.information_frame = information_frame
        self.icon = icon
        self.status = status
        self.device = device
        self.icon.setFixedSize(QtCore.QSize(16, 16))
        self.information_frame.show()

    def set_status(self, text: str, timeout: int = 5000) -> None:
        self.status.setText(text)
        self.information_frame.show()
        QtCore.QTimer.singleShot(timeout, self.hide_status)

    def hide_status(self) -> None:
        self.status.setText("")

    def set_device(self, text: str) -> None:
        self.device.setText(text)

    def hide_device(self) -> None:
        self.device.setText("")

    def hide(self) -> None:
        self.device.setText("")
        self.status.setText("")



    #def set_text_durable(self, text: str) -> None:
    #    self.text_label.setText(text)



