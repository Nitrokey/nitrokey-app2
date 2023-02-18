from pathlib import Path

from PyQt5 import QtWidgets
from PyQt5.QtCore import pyqtSlot

# from nitrokeyapp.setup_wizard import SetupWizard
from nitrokeyapp.qt_utils_mix_in import QtUtilsMixIn
from nitrokeyapp.ui.insert_Nitrokey_ui import Ui_Insert_Nitrokey

# isnt used atm
class InsertNitrokey(QtUtilsMixIn, QtWidgets.QDialog):
    def __init__(self, qt_app: QtWidgets.QApplication):
        QtWidgets.QDialog.__init__(self)
        QtUtilsMixIn.__init__(self)
        Path(__file__).parent.resolve().absolute() / "ui"
        self.app = qt_app
        self.ok_insert = None
        self.ui = Ui_Insert_Nitrokey()
        self.ui.setupUi(self)

        # dialogs
        self.ok_insert = self.ui.pushButton_ok_insert
        # insert Nitrokey
        self.ok_insert.clicked.connect(self.ok_insert_btn)

    @pyqtSlot()
    def ok_insert_btn(self):
        self.hide()

        self.setup_wizard.show()
