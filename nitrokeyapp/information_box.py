from PyQt5 import QtCore, QtWidgets


class InfoBox:
    def __init__(
        self,
        information_frame: QtWidgets.QWidget,
        icon: QtWidgets.QWidget,
        text_label: QtWidgets.QLabel,
    ) -> None:
        self.information_frame = information_frame
        self.icon = icon
        self.text_label = text_label
        self.icon.setFixedSize(QtCore.QSize(22, 22))

    def set_text(self, text: str) -> None:
        self.text_label.setText(text)
        self.information_frame.show()
        QtCore.QTimer.singleShot(5000, self.hide)

    def set_text_durable(self, text: str) -> None:
        self.text_label.setText(text)
        self.information_frame.show()

    def hide(self) -> None:
        self.text_label.setText("")
        self.information_frame.hide()
