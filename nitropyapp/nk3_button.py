from PyQt5 import QtWidgets, uic
from PyQt5.QtCore import Qt, QThread, pyqtSignal, pyqtSlot, QObject, QFile, QTextStream, QTimer, QSortFilterProxyModel, QSize, QRect
from PyQt5.Qt import QApplication, QClipboard, QLabel, QIcon, QProgressBar, QProgressDialog, QMessageBox
from nitropyapp.qt_utils_mix_in import QtUtilsMixIn
from nitropyapp.change_pin_dialog import ChangePinDialog
from nitropyapp.pynitrokey_for_gui import Nk3Context, list, version, wink, nk3_update, nk3_update_helper, change_pin
import nitropyapp.ui.breeze_resources
import nitropyapp.gui_resources

class Nk3Button(QtWidgets.QWidget):
    list_nk3_keys = []
    @classmethod
    def get(cls):
        return Nk3Button.list_nk3_keys
    def __init__(self, device, nitrokeys_window, layout_nk_btns, nitrokey3_frame, nk3_lineedit_uuid, nk3_lineedit_path, nk3_lineedit_version, tabs, update_nk3_btn, progressBarUpdate, change_pin_open_dialog, change_pin_dialog):
        super().__init__()
        self.device = device
        self.uuid = self.device.uuid()
        self.path = self.device.path
        self.version = self.device.version()
        self.change_pin_open_dialog = change_pin_open_dialog
        self.change_pin_dialog = change_pin_dialog
        self.nitrokeys_window = nitrokeys_window
        self.layout_nk_btns = layout_nk_btns
        self.nitrokey3_frame = nitrokey3_frame
        self.tabs = tabs
        self.nk3_lineedit_uuid = nk3_lineedit_uuid
        self.nk3_lineedit_path = nk3_lineedit_path
        self.nk3_lineedit_version = nk3_lineedit_version
        self.update_nk3_btn = update_nk3_btn
        self.progressBarUpdate = progressBarUpdate
        #########needs to create button in the vertical navigation with the nitrokey type and serial number as text
        self.btn_nk3 = QtWidgets.QPushButton(QIcon(":/images/icon/usb_new.png"),"Nitrokey 3:"f"{self.device.uuid()%10000}")
        self.btn_nk3.setFixedSize(184,40)
        self.btn_nk3.setIconSize(QSize(20, 20))
        self.btn_nk3.clicked.connect(lambda:self.nk3_btn_pressed())
        self.btn_nk3.setStyleSheet("border :4px solid ;"
                     "border-color : #474642;"
                     "border-width: 2px;"
                     "border-radius: 5px;"
                     "font-size: 14pt;"
                     "font-color: #474642;")
                     #"font-weight: bold;")
        self.layout_nk_btns.addWidget(self.btn_nk3)
        self.widget_nk_btns = QtWidgets.QWidget()
        self.widget_nk_btns.setLayout(self.layout_nk_btns)
        self.nitrokeys_window.setWidget(self.widget_nk_btns)
        # buttons get placed over the place holder
        self.own_update_btn = QtWidgets.QPushButton("Update Nitrokey 3"f"{self.device.uuid()%10000}", self.nitrokey3_frame)
        self.own_change_pin = QtWidgets.QPushButton("Change Nitrokey 3 PIN "f"{self.device.uuid()%10000}", self.nitrokey3_frame)
        self.own_update_btn.setGeometry(12,134,413,27)
        self.own_change_pin.setGeometry(12,166,413,27)
        self.ctx = Nk3Context(self.device.path)
        self.own_update_btn.clicked.connect(lambda:nk3_update_helper(self.ctx, self.progressBarUpdate, 0, 0))
        self.own_change_pin.clicked.connect(self.change_pin_open_dialog)
        self.change_pin_dialog.btn_ok.clicked.connect(lambda:change_pin(self.ctx, self.change_pin_dialog.current_pin.text(), self.change_pin_dialog.new_pin.text(), self.change_pin_dialog.confirm_new_pin.text()))
        Nk3Button.list_nk3_keys.append(self)
    @pyqtSlot()
    def nk3_btn_pressed(self):
        self.tabs.show()
        for i in range(1,6):
            self.tabs.setTabVisible(i, False)
        self.nk3_lineedit_uuid.setText(str(self.uuid))
        self.nk3_lineedit_path.setText(str(self.path))
        self.nk3_lineedit_version.setText(str(self.version))
        for i in Nk3Button.get():
            i.own_update_btn.hide()
            i.own_change_pin.hide()
        self.own_update_btn.show()
        self.own_change_pin.show()

    def __del__(self):
        print ("deleted")
        self.tabs.hide()
        self.nitrokeys_window.update()
        self.btn_nk3.hide()

    def update(self, device):
        self.device = device
        self.path = self.device.path
        self.version = self.device.version()
        self.nk3_lineedit_path.setText(str(self.path))
        self.nk3_lineedit_version.setText(str(self.version))
        self.ctx = Nk3Context(self.device.path)
