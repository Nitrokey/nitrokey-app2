from PyQt5 import QtWidgets
from PyQt5.QtCore import pyqtSlot

from nitrokeyapp.qt_utils_mix_in import QtUtilsMixIn


class KeyGeneration(QtUtilsMixIn, QtWidgets.QWizard):
    def __init__(self, qt_app: QtWidgets.QApplication):
        QtWidgets.QWizard.__init__(self)
        QtUtilsMixIn.__init__(self)

        self.app = qt_app

    def init_keygen(self):
        # dialogs
        self.adsettings_button = self.get_widget(
            QtWidgets.QPushButton, "pushButton_wiz"
        )
        self.adsettings = self.get_widget(QtWidgets.QWidget, "adsettings_key")

        self.wizard_page_userinfo = self.get_widget(
            QtWidgets.QWizardPage, "wizardPage1"
        )

        self.placeholder_path = self.get_widget(QtWidgets.QLineEdit, "lineEdit")
        self.placeholder_path.setPlaceholderText("Path")

        self.with_backup = self.get_widget(QtWidgets.QRadioButton, "radioButton_3")
        self.lastpage_keygen = self.get_widget(QtWidgets.QWizardPage, "wizardPage")
        self.confirm_path = self.get_widget(QtWidgets.QLineEdit, "lineEdit")
        self.confirm_path.setEnabled(False)

        self.real_name = self.get_widget(QtWidgets.QLineEdit, "lineEdit_2")
        self.wizard_page_userinfo.registerField("real_name*", self.real_name)

        self.email = self.get_widget(QtWidgets.QLineEdit, "lineEdit_3")
        self.wizard_page_userinfo.comment_line = self.get_widget(
            QtWidgets.QLineEdit, "lineEdit_4"
        )
        self.wizard_page_userinfo.registerField("email*", self.email)

        self.comment_line = self.get_widget(QtWidgets.QLineEdit, "lineEdit_4")
        self.comment_line.setPlaceholderText("Optional")

        self.back_up_info = self.get_widget(QtWidgets.QLabel, "label_2")
        self.back_up_info.hide()
        # insert Nitrokey
        self.adsettings_button.clicked.connect(self.adsettings_func)
        self.collapse(self.adsettings, self.adsettings_button)
        self.with_backup.toggled.connect(self.finish_show_hide)
        self.confirm_path.textChanged.connect(self.finish_show_hide_2)
        # insert Nitrokey

    @pyqtSlot()
    def finish_show_hide(self):
        if self.with_backup.isChecked():
            self.button(QtWidgets.QWizard.FinishButton).setEnabled(False)
            self.lastpage_keygen.cleanupPage()
            self.confirm_path.setEnabled(True)
            self.back_up_info.show()
        else:
            self.button(QtWidgets.QWizard.FinishButton).setEnabled(True)
            self.lastpage_keygen.cleanupPage()
            self.confirm_path.setEnabled(False)
            self.back_up_info.hide()

    def finish_show_hide_2(self):
        if self.confirm_path.text():
            self.button(QtWidgets.QWizard.FinishButton).setEnabled(True)

    def adsettings_func(self):
        self.collapse(self.adsettings, self.adsettings_button)

    def loading(self):
        # dialogs
        self.ok_insert = self.get_widget(QtWidgets.QPushButton, "pushButton_ok_insert")
        # insert Nitrokey
        self.ok_insert.clicked.connect(self.ok_insert_btn)
        # insert Nitrokey

    @pyqtSlot()
    def ok_insert_btn(self):
        self.hide()

        self.setup_wizard.show()
