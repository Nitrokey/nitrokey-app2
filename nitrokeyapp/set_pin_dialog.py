from PyQt5 import QtWidgets

from nitrokeyapp.qt_utils_mix_in import QtUtilsMixIn
from nitrokeyapp.ui.set_pin_dialog_ui import Ui_ChangePinDialog


class SetPinDialog(QtUtilsMixIn, QtWidgets.QDialog):
    def __init__(self, parent=None):
        QtWidgets.QDialog.__init__(self, parent)
        QtUtilsMixIn.__init__(self)

        self.ui = Ui_ChangePinDialog()
        self.ui.setupUi(self)
        self.new_pin = self.ui.lineEdit_new_pin_set
        self.new_pin.setEchoMode(QtWidgets.QLineEdit.Password)
        self.confirm_new_pin = self.ui.lineEdit_confirm_new_pin_set
        self.confirm_new_pin.setEchoMode(QtWidgets.QLineEdit.Password)
        self.btn_ok = self.ui.buttonBox.button(QtWidgets.QDialogButtonBox.Ok)
        self.confirm_new_pin.textChanged.connect(self.same_pin)
        self.new_pin.textChanged.connect(self.same_pin)
        self.btn_ok.setEnabled(False)

    def same_pin(self):

        if (
            self.new_pin.text() != self.confirm_new_pin.text()
            or self.new_pin.text() == ""
        ):
            self.btn_ok.setEnabled(False)
        else:
            self.btn_ok.setEnabled(True)
