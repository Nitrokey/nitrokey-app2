from typing import Any

from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt, pyqtSlot

from nitrokeyapp.qt_utils_mix_in import QtUtilsMixIn
from nitrokeyapp.ui.pindialog import Ui_PinDialog


# @fixme: PINDialog should be modal!
class PINDialog(QtUtilsMixIn, QtWidgets.QDialog):
    def __init__(self, qt_app: QtWidgets.QApplication) -> None:
        QtWidgets.QDialog.__init__(self)
        QtUtilsMixIn.__init__(self)
        self.app = qt_app
        self.ui = Ui_PinDialog()
        self.ui.setupUi(self)
        self.ok_signal, self.tries_left = None, None

        self.opts: dict[str, Any] = {}

        self.checkbox = self.get_widget(QtWidgets.QCheckBox, "checkBox")
        self.checkbox.stateChanged.connect(self.checkbox_toggled)

        self.ok_btn = self.get_widget(QtWidgets.QPushButton, "okButton")
        self.ok_btn.clicked.connect(self.ok_clicked)

        self.line_edit = self.get_widget(QtWidgets.QLineEdit, "lineEdit")
        self.status = self.get_widget(QtWidgets.QLabel, "status")
        self.title = self.get_widget(QtWidgets.QLabel, "label")

        self.reset()

    @pyqtSlot()
    def reset(self) -> None:
        self.status.setText("")
        self.title.setText("")
        self.ok_signal, self.tries_left = None, None
        self.line_edit.setText("")
        self.checkbox.setCheckState(Qt.CheckState.Unchecked)
        self.opts = {}
        self.hide()

    @pyqtSlot(dict)
    def invoke(self, opts: dict[str, Any]) -> None:
        self.opts = dct = opts

        self.tries_left = dct.get("retries", 0)
        who = dct.get("who")
        if self.tries_left == 0:
            self.user_warn(
                f"Please reset the {who} pin counter before continuing",
                "No attempts left",
            )
            self.reset()
            return

        self.status.setText(f"Attempts left: {self.tries_left}")
        self.title.setText(dct.get("title", self.title.text()))
        self.ok_signal = dct.get("sig")
        self.show()

    @pyqtSlot(int)
    def checkbox_toggled(self, state: int) -> None:
        if state == 0:
            self.line_edit.setEchoMode(QtWidgets.QLineEdit.Password)
        elif state == 2:
            self.line_edit.setEchoMode(QtWidgets.QLineEdit.Normal)

    @pyqtSlot()
    def ok_clicked(self) -> None:
        pin = self.line_edit.text()
        def_pin = self.opts.get("default", "(?)")
        # @fixme: get len-range from libnk.py
        if len(pin) < 6 or len(pin) > 20:
            self.line_edit.selectAll()
            self.user_warn(
                "The pin requires to be 6-20 chars in length\n" f"default: {def_pin}",
                "Invalid PIN",
            )
        else:
            self.ok_signal.emit(self.opts, pin)
