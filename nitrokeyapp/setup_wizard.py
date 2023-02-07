from PyQt5 import QtWidgets

from nitrokeyapp.qt_utils_mix_in import QtUtilsMixIn


class SetupWizard(QtUtilsMixIn, QtWidgets.QWizard):
    def __init__(self, qt_app: QtWidgets.QApplication):
        QtWidgets.QWizard.__init__(self)
        QtUtilsMixIn.__init__(self)
        self.app = qt_app

    def init_setup(self):
        self.userpin_page = self.get_widget(QtWidgets.QWizardPage, "wizardPage")
        self.userpin_1 = self.get_widget(QtWidgets.QLineEdit, "lineEdit")
        self.userpin_2 = self.get_widget(QtWidgets.QLineEdit, "lineEdit_2")
        self.userpin_page.registerField("user_pin_1*", self.userpin_1)
        self.userpin_page.registerField("user_pin_2*", self.userpin_2)

        self.adminpin_page = self.get_widget(QtWidgets.QWizardPage, "wizardPage2")
        self.adminpin_1 = self.get_widget(QtWidgets.QLineEdit, "lineEdit_4")
        self.adminpin_2 = self.get_widget(QtWidgets.QLineEdit, "lineEdit_3")
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
