from PyQt5 import QtWidgets, uic
from PyQt5.QtCore import Qt, QThread, pyqtSignal, pyqtSlot, QObject, QFile, QTextStream, QTimer, QSortFilterProxyModel, QSize, QRect
from PyQt5.Qt import QApplication, QClipboard, QLabel, QMovie, QIcon, QProgressBar,QProgressDialog, QMessageBox
# import wizards and stuff
from setup_wizard import SetupWizard
from qt_utils_mix_in import QtUtilsMixIn
import nitropyapp.ui.breeze_resources 
import nitropyapp.gui_resources
from pathlib import Path

# isnt used atm
class InsertNitrokey(QtUtilsMixIn, QtWidgets.QDialog):
    def __init__(self, qt_app: QtWidgets.QApplication):
        QtWidgets.QDialog.__init__(self)
        QtUtilsMixIn.__init__(self)
        Path(__file__).parent.resolve().absolute() / "ui"
        self.app = qt_app
        self.ok_insert = None

    def init_insertNitrokey(self):
        ## dialogs
        self.ok_insert = self.get_widget(QtWidgets.QPushButton, "pushButton_ok_insert")
         ## insert Nitrokey
        self.ok_insert.clicked.connect(self.ok_insert_btn)

    @pyqtSlot()
    def ok_insert_btn(self):
        self.hide()
        
        self.setup_wizard.show()