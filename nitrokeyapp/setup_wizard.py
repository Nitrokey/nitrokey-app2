from PyQt5 import QtWidgets

from nitrokeyapp.qt_utils_mix_in import QtUtilsMixIn
from nitrokeyapp.ui.setup_wizard_ui import Ui_PINSetup


class SetupWizard(QtUtilsMixIn, QtWidgets.QWizard):
    def __init__(self, qt_app: QtWidgets.QApplication):
        QtWidgets.QWizard.__init__(self)
        QtUtilsMixIn.__init__(self)
        self.app = qt_app
        self.ui = Ui_PINSetup()
        self.ui.setupUi(self)

        self.userpin_page = self.ui.wizardPage
        self.userpin_1 = self.ui.lineEdit
        self.userpin_2 = self.ui.lineEdit_2
        self.userpin_page.registerField("user_pin_1*", self.userpin_1)
        self.userpin_page.registerField("user_pin_2*", self.userpin_2)

        self.adminpin_page = self.ui.wizardPage2
        self.adminpin_1 = self.ui.lineEdit_4
        self.adminpin_2 = self.ui.lineEdit_3
        self.adminpin_page.registerField("admin_pin_1*", self.adminpin_1)
        self.adminpin_page.registerField("admin_pin_2*", self.adminpin_2)

        self.userpin_2.textChanged.connect(self.same_setup_wizard)
        self.adminpin_2.textChanged.connect(self.same_setup_wizard_2)

    def same_setup_wizard(self):
        if self.userpin_1.text() != self.userpin_2.text():
            self.button(QtWidgets.QWizard.NextButton).setEnabled(False)
        else:
            self.button(QtWidgets.QWizard.NextButton).setEnabled(True)

    def same_setup_wizard_2(self):
        if self.adminpin_1.text() != self.adminpin_2.text():
            self.button(QtWidgets.QWizard.FinishButton).setEnabled(False)
        else:
            self.button(QtWidgets.QWizard.FinishButton).setEnabled(True)

    def closeEvent(self, event):
        reply = QtWidgets.QMessageBox.question(
            self,
            "Message",
            "Are you sure to exit?",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
            QtWidgets.QMessageBox.No,
        )

        if reply == QtWidgets.QMessageBox.Yes:
            event.accept()

        else:
            event.ignore()
