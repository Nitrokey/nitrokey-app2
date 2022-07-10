# use "pbs" for packaging...
# pip-run -> pyqt5
# pip-dev -> pyqt5-stubs
import sys
import os
import os.path
import functools
import platform
# windows
import subprocess

#tests
import datetime 
import time

from pathlib import Path
from queue import Queue
from tqdm import tqdm

from typing import List, Optional, Tuple, Type, TypeVar
from PyQt5 import QtWidgets, uic
from PyQt5.QtCore import Qt, QThread, pyqtSignal, pyqtSlot, QObject, QFile, QTextStream, QTimer, QSortFilterProxyModel, QSize, QRect
from PyQt5.Qt import QApplication, QClipboard, QLabel, QMovie, QIcon, QProgressBar,QProgressDialog, QMessageBox

from pynitrokey import libnk as nk_api
# Nitrokey 3
from pynitrokey.cli.exceptions import CliException
from pynitrokey.helpers import Retries, local_print
from pynitrokey.nk3.base import Nitrokey3Base
from pynitrokey.nk3.exceptions import TimeoutException
from pynitrokey.nk3.device import BootMode, Nitrokey3Device
from pynitrokey.nk3 import list as list_nk3
from pynitrokey.nk3 import open as open_nk3
from pynitrokey.nk3.updates import get_repo
from pynitrokey.nk3.utils import Version
from pynitrokey.updates import OverwriteError
from pynitrokey.nk3.bootloader import (
    RKHT,
    FirmwareMetadata,
    Nitrokey3Bootloader,
    check_firmware_image,
)
from spsdk.mboot.exceptions import McuBootConnectionError

# import wizards and stuff
from setup_wizard import SetupWizard
from qt_utils_mix_in import QtUtilsMixIn
from about_dialog import AboutDialog
from key_generation import KeyGeneration
from windows_notification import WindowsUSBNotification
from pynitrokey_for_gui import Nk3Context, list, test, version, wink, _download_latest_update, nk3_update, reboot, _reboot_to_bootloader, _perform_update

#import nitropyapp.libnk as nk_api
import nitropyapp.ui.breeze_resources 
#pyrcc5 -o gui_resources.py ui/resources.qrc
import nitropyapp.gui_resources



#import pysnooper
#@pysnooper.snoop
start_time = 0
block_time = 0
class BackendThread(QThread):
    hello = pyqtSignal()

    job_q = Queue()

    def __del__(self):
        self.wait()

    def add_job(self, signal, func, *f_va, **f_kw):
        self.job_q.put((signal, func, f_va, f_kw))

    def stop_loop(self):
        self.add_job(None, None)

    def run(self):
        self.hello.emit()
        while True:
            # blocking job-wait-loop
            job = self.job_q.get()
            if job is None:
                continue
            signal, func, vargs, kwargs = job

            # func == None means stop/end thread asap!
            if func is None:
                break

            # eval `func`, emit signal with results
            res = func(*vargs, **kwargs)
            signal.emit(res or {})

########################################################################################
########################################################################################
########################################################################################
########################################################################################
# Define function to import external files when using PyInstaller.
# def resource_path(relative_path):
#     """ Get absolute path to resource, works for dev and for PyInstaller """
#     try:
#         # PyInstaller creates a temp folder and stores path in _MEIPASS
#         base_path = sys._MEIPASS
#     except Exception:
#         base_path = os.path.abspath(".")
#
#     return os.path.join(base_path, relative_path)


# Import .ui forms for the GUI using function resource_path()
#securitySearchForm = resource_path("securitySearchForm.ui")
#popboxForm = resource_path("popbox.ui")

#Ui_MainWindow, QtBaseClass = uic.loadUiType(securitySearchForm)
#Ui_PopBox, QtSubClass = uic.loadUiType(popboxForm)

#pyrcc4 -py3 resources.qrc -o resources_rc.py
########################################################################################
########################################################################################
########################################################################################
########################################################################################
#### nk3
################c++ code from cli.nk3.init
#logger = logging.getLogger(__name__) 

class Storage(QtUtilsMixIn, QtWidgets.QWizard):
    def __init__(self, qt_app: QtWidgets.QApplication):
        QtWidgets.QWizard.__init__(self)
        QtUtilsMixIn.__init__(self)
        self.ok_insert = None
        self.app = qt_app
        
        
    def init_storage(self):
        self.wizardpage_hidden_volume_pw = self.get_widget(QtWidgets.QWizardPage, "wizardPage")
        self.hidden_pw_1 = self.get_widget(QtWidgets.QLineEdit, "HVPasswordEdit") 
        self.hidden_pw_2 = self.get_widget(QtWidgets.QLineEdit, "HVPasswordEdit_2") 
        self.wizardpage_hidden_volume_pw.registerField("hidden_pw_1*", self.hidden_pw_1)
        self.wizardpage_hidden_volume_pw.registerField("hidden_pw_2*", self.hidden_pw_2)
        self.show_hidden_pw = self.get_widget(QtWidgets.QCheckBox, "ShowPasswordCheckBox")

        self.storage_slider = self.get_widget(QtWidgets.QSlider, "horizontalSlider_storage")
        self.storage_blockspin = self.get_widget(QtWidgets.QDoubleSpinBox, "StartBlockSpin_3")

        self.radio_gb = self.get_widget(QtWidgets.QRadioButton, "rd_GB_3")
        self.radio_mb = self.get_widget(QtWidgets.QRadioButton, "rd_MB_3")

        self.confirm_creation = self.get_widget(QtWidgets.QCheckBox, "checkBox_confirm")

        self.lastpage = self.get_widget(QtWidgets.QWizardPage, "wizardPage_3")

        self.lastpage.registerField("confirm_creation*", self.confirm_creation)
        

        self.storage_blockspin.valueChanged.connect(self.change_value_2)
        self.storage_slider.valueChanged.connect(self.change_value)

        self.radio_gb.toggled.connect(self.swap_to_gb)
        self.radio_mb.toggled.connect(self.swap_to_mb)
        self.hidden_pw_2.textChanged.connect(self.same_storage)

    def same_storage(self):
        if self.hidden_pw_2.text() != self.hidden_pw_1.text():
            self.button(QtWidgets.QWizard.NextButton).setEnabled(False)
        else:
            self.button(QtWidgets.QWizard.NextButton).setEnabled(True)
    
    @pyqtSlot(int)   
    #### storage wizard
    def change_value(self, value):
        self.storage_blockspin.setValue(float(value))
        print(self.storage_blockspin.value)
        print(self.storage_slider.value)
    def change_value_2(self, value):
        self.storage_slider.setValue(float(value))
    @pyqtSlot()
    def swap_to_mb(self):
        if self.radio_mb.isChecked():
            self.storage_blockspin.setMaximum(30000)
            self.storage_slider.setMaximum(30000)
            self.storage_blockspin.setValue(float(self.storage_blockspin.value())*1000)
            self.storage_slider.setValue(float(self.storage_blockspin.value()))
            self.storage_slider.setSingleStep(300)
            self.storage_blockspin.setSingleStep(300)
            print(float(self.storage_slider.value()))
        
    def swap_to_gb(self):
        if self.radio_gb.isChecked():
            self.storage_blockspin.setValue(float(self.storage_blockspin.value())/1000)
            self.storage_slider.setValue(float(self.storage_blockspin.value()))
            
            self.storage_blockspin.setMaximum(30)
            self.storage_slider.setMaximum(30)
            self.storage_slider.setSingleStep(1)
            self.storage_blockspin.setSingleStep(1)

# isnt used anymore!
class InsertNitrokey(QtUtilsMixIn, QtWidgets.QDialog):
    def __init__(self, qt_app: QtWidgets.QApplication):
        QtWidgets.QDialog.__init__(self)
        QtUtilsMixIn.__init__(self)
        ui_dir = Path(__file__).parent.resolve().absolute() / "ui"
        self.app = qt_app
        self.ok_insert = None
        self.setup_wizard = SetupWizard(qt_app)
        self.setup_wizard.load_ui(ui_dir / "setup-wizard.ui", self.setup_wizard)
    def init_insertNitrokey(self):
        ## dialogs
        self.ok_insert = self.get_widget(QtWidgets.QPushButton, "pushButton_ok_insert")
         ## insert Nitrokey
        self.ok_insert.clicked.connect(self.ok_insert_btn)
            #### insert Nitrokey
    @pyqtSlot()
    def ok_insert_btn(self):
        self.hide()
        
        self.setup_wizard.show()
# loading screen
class LoadingScreen(QtWidgets.QWidget):
    # def __init__(self):
    #     super().__init__()
    #     self.setFixedSize(128,128)  #128 128
    #     self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.CustomizeWindowHint)

    #     self.label_animation = QLabel(self)
    #     self.qprogressbar = QProgressBar(self)
    #     self.setGeometry(QRect(650,300,0,0))
        #self.movie = QMovie(":/images/ProgressWheel.GIF")
        #self.label_animation.setMovie(self.movie)
        
        #timer = QTimer(self)
        #self.startAnimation()
        #timer.singleShot(1000, self.stopAnimation)

    #    self.show()
    
    def startAnimation(self):
        self.movie.start()

    def stopAnimation(self):
        #self.movie.stop()
        self.close()
        GUI.user_info("success","You now have a main key with the capability\n to sign and certify and a subkey for encryption.  ",title ="Key generation was successful", parent=self.label_animation)
        
    #### PWS related callbacks

##### @fixme: PINDialog should be modal!
class PINDialog(QtUtilsMixIn, QtWidgets.QDialog):
    def __init__(self, qt_app: QtWidgets.QApplication):
        QtWidgets.QDialog.__init__(self)
        QtUtilsMixIn.__init__(self)
        self.app = qt_app

        self.checkbox, self.ok_btn, self.line_edit = None, None, None
        self.status, self.title = None, None
        self.ok_signal, self.tries_left = None, None

        self.opts = {}

    def init_gui(self):
        self.checkbox = self.get_widget(QtWidgets.QCheckBox, "checkBox")
        self.checkbox.stateChanged.connect(self.checkbox_toggled)

        self.ok_btn = self.get_widget(QtWidgets.QPushButton, "okButton")
        self.ok_btn.clicked.connect(self.ok_clicked)

        self.line_edit = self.get_widget(QtWidgets.QLineEdit, "lineEdit")
        self.status = self.get_widget(QtWidgets.QLabel, "status")
        self.title = self.get_widget(QtWidgets.QLabel, "label")

        self.reset()

    @pyqtSlot()
    def reset(self):
        self.status.setText("")
        self.title.setText("")
        self.ok_signal, self.tries_left = None, None
        self.line_edit.setText("")
        self.checkbox.setCheckState(0)
        self.opts = {}
        self.hide()

    @pyqtSlot(dict)
    def invoke(self, opts):
        self.opts = dct = opts

        self.tries_left = dct.get("retries", 0)
        who = dct.get("who")
        if self.tries_left == 0:
            self.user_warn(f"Please reset the {who} pin counter before continuing",
                           "No attempts left")
            self.reset()
            return

        self.status.setText(f"Attempts left: {self.tries_left}")
        self.title.setText(dct.get("title", self.title.text()))
        self.ok_signal = dct.get("sig")
        self.show()

    @pyqtSlot(int)
    def checkbox_toggled(self, state):
        if state == 0:
            self.line_edit.setEchoMode(QtWidgets.QLineEdit.Password)
        elif state == 2:
            self.line_edit.setEchoMode(QtWidgets.QLineEdit.Normal)

    @pyqtSlot()
    def ok_clicked(self):
        pin = self.line_edit.text()
        def_pin = self.opts.get("default", "(?)")
        # @fixme: get len-range from libnk.py
        if len(pin) < 6 or len(pin) > 20:
            self.line_edit.selectAll()
            self.user_warn("The pin requires to be 6-20 chars in length\n"
                f"default: {def_pin}", "Invalid PIN")
        else:
            self.ok_signal.emit(self.opts, pin)

class EditButtonsWidget(QtWidgets.QWidget):
    def __init__(self, table, pop_up_copy, res, parent=None):
        super().__init__(parent)
        self.table_pws = table
        self.pop_up_copy = pop_up_copy
        
        # add your buttons
        layout = QtWidgets.QHBoxLayout()
        layout.setContentsMargins(0,0,0,0)
        layout.setSpacing(0)

        Copy = QtWidgets.QPushButton('Icon')
        Copy.setFixedSize(65,65)
        Copy.clicked.connect(self.copy_to_clipboard_function)
        layout.addWidget(Copy)
        layout.addWidget(QtWidgets.QLabel(str(res)))
        
        self.setLayout(layout)
    @pyqtSlot()
    def copy_to_clipboard_function(self):
        buttons_index = self.table_pws.indexAt(self.pos())
        item = self.table_pws.item(buttons_index.row(), buttons_index.column()+3)
        QApplication.clipboard().setText(item.text())
            # qtimer popup
        self.time_to_wait = 5
        self.pop_up_copy.setText("Data added to clipboard.") #{0} for time display
        self.pop_up_copy.setStyleSheet("background-color: #2B5DD1; color: #FFFFFF ; border-style: outset;" 
        "padding: 2px ; font: bold 20px ; border-width: 6px ; border-radius: 10px ; border-color: #2752B8;")
        self.pop_up_copy.show()
        self.timer = QTimer(self)
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self.changeContent)
        self.timer.start()  
    def changeContent(self):
        self.pop_up_copy.setText("Data added to clipboard.")
        self.time_to_wait -= 1
        if self.time_to_wait <= 0:
            self.pop_up_copy.hide()
            self.timer.stop()
    def closeEvent(self, event):
        self.timer.stop()
        event.accept()

# nk3 button mit nk3context verbinden???
class Nk3Button(QtWidgets.QWidget):
    list_nk3_keys = []
    @classmethod
    def get(cls):
        return Nk3Button.list_nk3_keys
    def __init__(self, device, nitrokeys_window, nk3_lineedit_1, nk3_lineedit_2, nk3_lineedit_3, tabs, update_nk3_btn, progressBarUpdate):
        super().__init__()
        self.device = device
        self.uuid = self.device.uuid
        self.nitrokeys_window = nitrokeys_window
        self.tabs = tabs
        self.nk3_lineedit_1 = nk3_lineedit_1
        self.nk3_lineedit_2 = nk3_lineedit_2
        self.nk3_lineedit_3 = nk3_lineedit_3
        self.update_nk3_btn = update_nk3_btn
        self.progressBarUpdate = progressBarUpdate
        #########needs to create buttoGUIn in the vertical navigation with the nitrokey type and serial number as text
        self.btn_nk3 = QtWidgets.QPushButton("Nitrokey 3:"f"{self.device.uuid()%10000}")
        #self.btn_test.setFixedSize(65,65)
        self.btn_nk3.clicked.connect(lambda:self.nk3_btn_pressed())
        self.nitrokeys_window.setWidget(self.btn_nk3)  
        self.ctx = Nk3Context(self.device.path)
        self.update_nk3_btn.clicked.connect(lambda:nk3_update(self.ctx, self.progressBarUpdate, 0))
        Nk3Button.list_nk3_keys.append(self)
        print(Nk3Button.list_nk3_keys)
        print("das wollen wir sehen!!!!",type(self.device.path),type(self.device))
    @pyqtSlot()    
    def nk3_btn_pressed(self):
        print("geht bis hier!")
        self.tabs.show()
        self.tabs.setTabVisible(1, False)
        self.tabs.setTabVisible(2, False)
        self.tabs.setTabVisible(3, False)
        self.tabs.setTabVisible(4, False)
        self.tabs.setTabVisible(5, False)
        self.nk3_lineedit_1.setText(str(self.device.uuid()))
        self.nk3_lineedit_2.setText(str(self.device.path))
        self.nk3_lineedit_3.setText(str(self.device.version()))

    def __del__(self):
        print ("deleted")
        self.tabs.hide()
        self.nitrokeys_window.update()
        self.btn_nk3.hide()
class GUI(QtUtilsMixIn, QtWidgets.QMainWindow):

    sig_connected = pyqtSignal(dict)
    sig_disconnected = pyqtSignal()
    sig_lock = pyqtSignal(dict)

    sig_ask_pin = pyqtSignal(dict)
    sig_auth = pyqtSignal(dict, str)
    sig_confirm_auth = pyqtSignal(str)

    sig_status_upd = pyqtSignal(dict)

    sig_unlock_pws = pyqtSignal(dict)
    sig_unlock_hv = pyqtSignal(dict)
    sig_unlock_ev = pyqtSignal(dict)

    change_value = pyqtSignal(int)

    
    def __init__(self, qt_app: QtWidgets.QApplication):
        QtWidgets.QMainWindow.__init__(self)
        QtUtilsMixIn.__init__(self)
        self.backend_thread.hello.connect(self.backend_cb_hello)
        self.backend_thread.start()
        # linux
        if  platform.system() == "Linux":
            # pyudev stuff 
            import pyudev
            from pyudev.pyqt5 import MonitorObserver
            # start monitoring usb
            self.context = pyudev.Context()
            self.monitor = pyudev.Monitor.from_netlink(self.context)
            self.monitor.filter_by(subsystem='usb')
            self.observer = MonitorObserver(self.monitor)
            self.observer.deviceEvent.connect(self.device_connect)
            self.monitor.start()
        # windows
        if platform.system() == "Windows":
            print("OS:Windows")
           
            w = WindowsUSBNotification(self.detect_nk3)
            #win32gui.PumpMessages()
            print("not trapped")
        
        ################################################################################
        # load UI-files and prepare them accordingly
        ui_dir = Path(__file__).parent.resolve().absolute() / "ui"
        ui_files = {
            "main": (ui_dir / "mainwindow_alternative.ui").as_posix(),
            "pin": (ui_dir / "pindialog.ui").as_posix()
        }

        self.load_ui(ui_files["main"], self)
        self.pin_dialog = PINDialog(qt_app)
        self.pin_dialog.load_ui(ui_files["pin"], self.pin_dialog)
        self.pin_dialog.init_gui()
        _get = self.get_widget
        _qt = QtWidgets

        ################################################################################
        # playground

        ## os notification
        self.tray = QtWidgets.QSystemTrayIcon()  
        self.tray.setIcon(QIcon(":/images/new/down_arrow.png"))

        self.key_generation = KeyGeneration(qt_app)
        self.key_generation.load_ui(ui_dir / "key_generation.ui", self.key_generation)
        self.key_generation.init_keygen()

        self.about_dialog = AboutDialog(qt_app)
        self.about_dialog.load_ui(ui_dir / "aboutdialog.ui", self.about_dialog)
        
        self.setup_wizard = SetupWizard(qt_app)
        self.setup_wizard.load_ui(ui_dir / "setup-wizard.ui", self.setup_wizard)
        self.setup_wizard.init_setup()
        self.storage = Storage(qt_app)
        self.storage.load_ui(ui_dir / "storage.ui", self.storage)
        self.storage.init_storage()
        

        self.insert_Nitrokey = InsertNitrokey(qt_app)
        self.insert_Nitrokey.load_ui(ui_dir / "insert_Nitrokey.ui", self.insert_Nitrokey)
        self.insert_Nitrokey.init_insertNitrokey()

        ################################################################################
        #### get widget objects
        
        ## wizard
 
        
        ## app wide widgets
        self.status_bar = _get(_qt.QStatusBar, "statusBar")
        self.menu_bar = _get(_qt.QMenuBar, "menuBar")
        self.tabs = _get(_qt.QTabWidget, "tabWidget")
        self.tab_overview = _get(_qt.QWidget, "tab_5")
        self.tab_otp_conf = _get(_qt.QWidget, "tab")
        self.tab_otp_gen = _get(_qt.QWidget, "tab_2")
        self.tab_pws = _get(_qt.QWidget, "tab_3")
        self.tab_settings = _get(_qt.QWidget, "tab_4")
        self.tab_fido2 = _get(_qt.QWidget, "tab_6")
        self.tab_storage = _get(_qt.QWidget, "tab_7")
        self.about_button = _get(_qt.QPushButton, "btn_about")
        self.help_btn = _get(_qt.QPushButton, "btn_dial_help")
        self.quit_button = _get(_qt.QPushButton, "btn_dial_quit") 
        self.settings_btn = _get(_qt.QPushButton, "btn_settings")
        self.lock_btn = _get(_qt.QPushButton, "btn_dial_lock")
        self.pro_btn =  _get(_qt.QPushButton, "pushButton_pro")
        self.storage_btn =  _get(_qt.QPushButton, "pushButton_storage")
        self.fido2_btn =  _get(_qt.QPushButton, "pushButton_fido2")
        self.others_btn = _get(_qt.QPushButton, "pushButton_others")
        self.l_insert_Nitrokey = _get(_qt.QFrame, "label_insert_Nitrokey")
        ## overview 
        self.unlock_pws_btn = _get(_qt.QPushButton, "PWS_ButtonEnable")
        self.frame_p = _get(_qt.QFrame, "frame_pro")
        self.frame_s = _get(_qt.QFrame, "frame_storage")
        self.frame_f = _get(_qt.QFrame, "frame_fido2")
        self.navigation_frame = _get(_qt.QFrame, "vertical_navigation")
        self.nitrokeys_window = _get(_qt.QScrollArea, "Nitrokeys") 
        self.hidden_volume = _get(_qt.QPushButton, "btn_dial_HV")
        ### nk3
        self.nk3_lineedit_1 = _get(_qt.QLineEdit, "nk3_lineedit_1")
        self.nk3_lineedit_2 = _get(_qt.QLineEdit, "nk3_lineedit_2")
        self.nk3_lineedit_3 = _get(_qt.QLineEdit, "nk3_lineedit_3")
        self.update_nk3_btn = _get(_qt.QPushButton, "update_nk3_btn")

        self.progressBarUpdate = _get(_qt.QProgressBar, "progressBar_Update")
        self.progressBarUpdate.hide()
        ## PWS
        self.information_label = _get(_qt.QLabel, "label_16")
        self.scrollArea = _get(_qt.QScrollArea, "scrollArea")
        self.groupbox_parameter = _get(_qt.QWidget, "widget_parameters")
        self.groupbox_notes = _get(_qt.QWidget, "widget_notes")
        self.groupbox_secretkey = _get(_qt.QWidget, "widget_secretkey")
        self.expand_button_secretkey = _get(_qt.QPushButton, "expand_button_secret")
        self.expand_button_notes = _get(_qt.QPushButton, "expand_button_notes")
        self.expand_button_parameter = _get(_qt.QPushButton, "expand_button_parameter")
        self.groupbox_pws = _get(_qt.QWidget, "widget_pws")
        self.table_pws = _get(_qt.QTableWidget, "Table_pws")
        self.pws_editslotname = _get(_qt.QLineEdit, "PWS_EditSlotName")
        self.pws_editloginname = _get(_qt.QLineEdit, "PWS_EditLoginName")
        self.pws_editpassword = _get(_qt.QLineEdit, "PWS_EditPassword")
        self.pws_editnotes = _get(_qt.QTextEdit, "textEdit_notes")
        self.pws_editOTP = _get(_qt.QLineEdit, "PWS_EditOTP")
        self.add_pws_btn = _get(_qt.QPushButton, "PWS_ButtonAdd")
        self.delete_pws_btn = _get(_qt.QPushButton, "PWS_ButtonDelete")
        self.cancel_pws_btn_2 = _get(_qt.QPushButton, "PWS_ButtonClose")
        self.add_table_pws_btn = _get(_qt.QPushButton, "PWS_ButtonSaveSlot")
        self.searchbox = _get(_qt.QLineEdit, "Searchbox")
        self.show_hide_btn = _get(_qt.QCheckBox, "show_hide")
        self.show_hide_btn_2 = _get(_qt.QCheckBox, "show_hide_2")
        self.pop_up_copy = _get(_qt.QLabel, "pop_up_copy")
        self.copy_name = _get(_qt.QPushButton, "copy_1")
        self.copy_username = _get(_qt.QPushButton, "copy_2")
        self.copy_pw = _get(_qt.QPushButton, "copy_3")
        self.copy_otp = _get(_qt.QPushButton, "copy_4")
        self.copy_current_otp = _get(_qt.QPushButton, "pushButton_otp_copy")
        self.qr_code = _get(_qt.QPushButton, "pushButton_4")
        self.random_otp = _get(_qt.QPushButton, "pushButton_7")
        
        ## smartcard
        self.pushButton_add_key = _get(_qt.QPushButton, "pushButton_add_keys")
        self.main_key = _get(_qt.QGroupBox, "groupBox_mainkey")
        self.sub_key_key = _get(_qt.QGroupBox, "groupBox_subkey")
        ## FIDO2
        self.add_btn = _get(_qt.QPushButton, "pushButton_add")
        self.table_fido2 = _get(_qt.QTableWidget, "Table_fido2")
        # OTP widgets
        self.radio_hotp_2 = _get(_qt.QRadioButton, "radioButton")
        self.radio_totp_2 = _get(_qt.QRadioButton, "radioButton_2")
        self.frame_hotp = _get(_qt.QFrame, "frame_hotp")
        self.frame_totp = _get(_qt.QFrame, "frame_totp")
        #self.radio_hotp = _get(_qt.QRadioButton, "radioButton")
        #self.radio_totp = _get(_qt.QRadioButton, "radioButton_2")
        #self.otp_combo_box = _get(_qt.QComboBox, "slotComboBox")
        #self.otp_name = _get(_qt.QLineEdit, "nameEdit")
        #self.otp_len_label = _get(_qt.QLabel, "label_5")
        #self.otp_erase_btn = _get(_qt.QPushButton, "eraseButton")
        #self.otp_save_btn = _get(_qt.QPushButton, "writeButton")
        #self.otp_cancel_btn = _get(_qt.QPushButton, "cancelButton")
        #self.otp_secret = _get(_qt.QLineEdit, "secretEdit")
        #self.otp_secret_type_b32 = _get(_qt.QRadioButton, "base32RadioButton")
        #self.otp_secret_type_hex = _get(_qt.QRadioButton, "hexRadioButton")
        #self.otp_gen_len = _get(_qt.QSpinBox, "secret_key_generated_len")
        #self.otp_gen_secret_btn = _get(_qt.QPushButton, "randomSecretButton")
        #self.otp_gen_secret_clipboard_btn = _get(_qt.QPushButton, "btn_copyToClipboard")
        #self.otp_gen_secret_hide = _get(_qt.QCheckBox, "checkBox")
        ################################################################################
        # set some props, initial enabled/visible, finally show()
        self.setAttribute(Qt.WA_DeleteOnClose)

        #self.tabs.setCurrentIndex(0)
        self.tabs.setCurrentWidget(self.tab_overview)
        self.tabs.currentChanged.connect(self.slot_tab_changed)

        self.init_gui()
        self.show()

        self.device = None

        ################################################################################
        ######nk3
        self.help_btn.clicked.connect(self.device_connect)
        #self.change_value.connect(self.setprogressbar)
        #self.update_nk3_btn.clicked.connect(lambda: nk3_update(self.ctx,0))
        #self.connect_signal_slots(lambda:self.update_nk3_btn.clicked, self.change_value, [GUI.setProgressVal], lambda:nk3_update(self.ctx,0))
        # Nitrokey 3 update
        #self.firmware_started=lambda:self.user_info("Firmware Update started")
        #self.update_nk3_btn.clicked.connect(lambda:self.backend_thread.add_job(self.change_value,nk3_update(self.ctx, 0)))
        #self.update_nk3_btn.clicked.connect(lambda:nk3_update(self.ctx, self.progressBarUpdate, 0))
        
        self.quit_button.clicked.connect(self.slot_quit_button_pressed)
        self.lock_btn.clicked.connect(self.slot_lock_button_pressed)
        self.unlock_pws_btn.clicked.connect(self.unlock_pws_button_pressed)
        self.about_button.clicked.connect(self.about_button_pressed)
        self.pro_btn.clicked.connect(self.pro_btn_pressed)
        self.storage_btn.clicked.connect(self.storage_btn_pressed)
        self.fido2_btn.clicked.connect(self.fido2_btn_pressed)
        ################################################################################
        #### connections for functional signals
        ## generic / global
        self.connect_signal_slots(self.pro_btn.clicked, self.sig_connected,
            [self.job_nk_connected, 
            ### otp_combo_box is missing
            #self.toggle_otp
            self.load_active_slot
            ], self.job_connect_device)
        self.sig_status_upd.connect(self.update_status_bar)
        self.sig_disconnected.connect(self.init_gui)
        ## overview

        ### storage
        self.hidden_volume.clicked.connect(self.create_hidden_volume)
        self.storage.show_hidden_pw.stateChanged.connect(self.slot_hidden_hide)

        self.setup_wizard.button(QtWidgets.QWizard.FinishButton).clicked.connect(self.init_pin_setup)
        ## setup
        self.storage.button(QtWidgets.QWizard.FinishButton).clicked.connect(self.init_storage_setup)
        ## smart card
        self.pushButton_add_key.clicked.connect(self.add_key)
        self.key_generation.button(QtWidgets.QWizard.FinishButton).clicked.connect(self.loading)
        ## pws stuff
        self.table_pws.cellClicked.connect(self.table_pws_function)
        self.add_pws_btn.clicked.connect(self.add_pws)
        self.add_table_pws_btn.clicked.connect(self.add_table_pws)
        self.cancel_pws_btn_2.clicked.connect(self.cancel_pws_2)
        self.delete_pws_btn.clicked.connect(self.delete_pws)
        self.ButtonChangeSlot.clicked.connect(self.change_pws)

        self.copy_name.clicked.connect(self.copyname)
        self.copy_username.clicked.connect(self.copyusername)
        self.copy_pw.clicked.connect(self.copypw)
        self.copy_otp.clicked.connect(self.copyotp)
        ### groupboxes pws
        self.expand_button_parameter.clicked.connect(self.groupbox_parameters_collapse)
        self.expand_button_notes.clicked.connect(self.groupbox_manageslots_collapse)
        self.expand_button_secretkey.clicked.connect(self.groupbox_secretkey_collapse)
        ##self.groupbox_pws.clicked.connect(self.groupbox_pws_collapse)
        self.searchbox.textChanged.connect(self.filter_the_table)
        self.searchbox.setPlaceholderText("Search")
        self.show_hide_btn.stateChanged.connect(self.slot_pws_hide)
        self.show_hide_btn_2.stateChanged.connect(self.slot_otp_hide)

        ## otp stuff
        self.radio_totp_2.clicked.connect(self.slot_toggle_otp_2)
        self.radio_hotp_2.clicked.connect(self.slot_toggle_otp_2)

        #self.radio_totp.toggled.connect(self.slot_toggle_otp)
        #self.radio_hotp.toggled.connect(self.slot_toggle_otp)

        #self.otp_combo_box.currentIndexChanged.connect(self.slot_select_otp)
        # self.otp_erase_btn.clicked.connect(self.slot_erase_otp)
        # self.otp_cancel_btn.clicked.connect(self.slot_cancel_otp)
        # self.otp_save_btn.clicked.connect(self.slot_save_otp)

        # self.otp_secret.textChanged.connect(self.slot_otp_save_enable)
        # self.otp_name.textChanged.connect(self.slot_otp_save_enable)

        # self.otp_gen_secret_btn.clicked.connect(self.slot_random_secret)
        # self.otp_gen_secret_hide.stateChanged.connect(self.slot_secret_hide)
        
        ## auth related
        self.sig_ask_pin.connect(self.pin_dialog.invoke)
        self.sig_auth.connect(self.slot_auth)
        self.sig_confirm_auth.connect(self.slot_confirm_auth)

        self.sig_lock.connect(self.slot_lock)

    #nk3 stuff
        
    def info_success(self):
        self.user_info(self, "success")
    def time_block(self):
        global block_time
        global start_time
        if block_time == 0:
            start_time = datetime.datetime.utcnow()
            return True
            
        else:
            passed_time = datetime.datetime.utcnow() - start_time  
            if passed_time.total_seconds() > 1:
                block_time = 0  
                return False

    ### experimental idea to differ between removed and added
    def device_connect(self):
        global block_time
        for dvc in iter(functools.partial(self.monitor.poll, 3), None):
            if dvc.action == "remove" and self.time_block():
                
                list_of_removed = []
                time.sleep(1)
                if len(list_nk3()):
                    print("list nk3:", list_nk3())
                    list_of_nk3s = [x.uuid for x in list_nk3()]
                    list_of_removed_help = [y for y in Nk3Button.get() if (y.uuid not in list_of_nk3s)]
                    list_of_removed = list_of_removed + list_of_removed_help
                else:
                    list_of_removed = list_of_removed + Nk3Button.get()
                print("list_of_removed", list_of_removed)
                for k in list_of_removed:
                    print(list_of_removed)
                    print("removed", k)
                    k.__del__()
                    Nk3Button.list_nk3_keys.remove(k)
                block_time = 1   
                    #self.detect_nk3()
                    #self.nitrokeys_window.findChild(QtWidgets.QPushButton,"Nitrokey 3:3743").hide()
            elif dvc.action == "bind" and self.time_block():
                print("bind")
                time.sleep(0.1)
                func1 = lambda w: (w.setEnabled(False), w.setVisible(False))
                self.apply_by_name(["pushButton_storage","pushButton_pro", "btn_dial_HV"], func1) # overview
                ############## devs for the libraries
                devs = nk_api.BaseLibNitrokey.list_devices()
            
                print(devs)
                dev = None
                if len(devs) > 0:
                    _dev = devs[tuple(devs.keys())[0]]
                    # enable and show needed widgets
                    func = lambda w: (w.setEnabled(True), w.setVisible(True))
                    if _dev["model"] == 1:
                        dev = nk_api.NitrokeyPro()
                        print("pro")
                        self.apply_by_name(["pushButton_pro", "btn_dial_HV"], func) # overview
                    elif _dev["model"] == 2:
                        dev = nk_api.NitrokeyStorage()
                        print("storage")
                        self.apply_by_name(["pushButton_storage", "btn_dial_HV"], func) # overview 
                                
                                    
                    else:
                        #func = lambda w: (w.setEnabled(False), w.setVisible(False))
                        #self.apply_by_name(["pushButton_storage","pushButton_pro", "btn_dial_HV"], func) # overview
                        print("removed button(s)")
                        self.msg("Unknown device model detected")
                        return {"connected": False}
                self.detect_nk3()
                block_time = 1

    def detect_nk3(self):
        nk3s = list_nk3()
        print(nk3s)
        if len(nk3s) > 0:
            self.device = nk3s[0]
            uuid = self.device.uuid()
            if uuid:
                print(f"{self.device.path}: {self.device.name} {self.device.uuid():X}")
            else:
                print(f"{self.device.path}: {self.device.name}")
            self.one_nk3_btn = Nk3Button(self.device, self.nitrokeys_window, self.nk3_lineedit_1, self.nk3_lineedit_2, self.nk3_lineedit_3, self.tabs, self.update_nk3_btn, self.progressBarUpdate)
            #self.sendmessage("Nitrokey 3 connected.")
            self.tray.show() 
            self.tray.setToolTip("Nitrokey 3")
            self.tray.showMessage("Nitrokey 3 connected.","Nitrokey 3 connected.", msecs=2000)
            self.device = None 
        
        else:
            print("no nk3 in list. no admin?")
            self.tray.show() 
            self.tray.setToolTip("Nitrokey 3")
            self.tray.showMessage("Nitrokey 3 not connected.","Nitrokey 3 not connected.", msecs=2000)
        
    @pyqtSlot()   
    #### press f1 for connecting keys
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_F1:
            self.key_method()
        elif event.key() == Qt.Key_F2:
            self.key_method_1()
        elif event.key() == Qt.Key_F3:
            self.key_method_2()
        

    def key_method(self):
        print('F1 key pressed') 
        self.l_insert_Nitrokey.hide()  
        self.storage_btn.show()

    def key_method_1(self):
        print('F2 key pressed') 
        self.l_insert_Nitrokey.hide()  
        self.fido2_btn.show()
    def key_method_2(self):
        print('F3 key pressed') 
        self.l_insert_Nitrokey.hide()  
        self.pro_btn.show()
    ### helper (not in use for now)
    def get_active_otp(self):
        who = "totp" if self.radio_totp_2.isChecked() else "hotp"
        idx = self.otp_combo_box.currentIndex()
        return who, idx, self.device.TOTP if who == "totp" else self.device.HOTP,
        ############## get the current password slots from the key
    @pyqtSlot()
    def load_active_slot_name(self):
        if self.device is not None:
            return self.device.TOTP
        else:
            print("device is none")
    def load_active_slot(self):
        all_otp = self.load_active_slot_name()
        for index in range(10):
            name = all_otp.get_name(index)
            if name:
                self.add_table_pws_from_key(index)
                
                    
    def ask_pin(self, who):
        assert who in ["user", "admin"]
        who_cap = who.capitalize()
        dct = dict(
                title=f"{who_cap} PIN:",
                retries=self.device.user_pin_retries if who == "user" else
                        self.device.admin_pin_retries,
                sig=self.sig_auth,
                default=self.device.default_user_pin if who == "user" else
                        self.device.default_admin_pin,
                who=who
        )

        self.sig_ask_pin.emit(dct)
        self.msg(f"need {who_cap} auth")
        return

    def msg(self, what):
        what = what if isinstance(what, dict) else {"msg": what}
        self.sig_status_upd.emit(what)
    ### helper (in use)
    #### overview
    @pyqtSlot()
    def create_hidden_volume(self):
        self.storage.exec()
    @pyqtSlot()
    def loading(self):
        self.loading_screen = LoadingScreen()
        #self.main_key.show()
        #self.sub_key_key.show()
    #### PIN setup
    @pyqtSlot()
    def init_pin_setup(self):
        self.tabs.setEnabled(True)
        self.user_info("You have successfully configured the User and Admin PIN.\n These can be changed at any time in the device settings.",title ="PIN configuration was successful")
 
    #### storage setup
    @pyqtSlot()
    def init_storage_setup(self):
        print("it works")
        self.user_info("You now have successfully created your hidden volume.  ",title ="Hidden Volume generation was successful")   
    #### smartcard
    @pyqtSlot()
    def add_key(self):
        self.key_generation.exec()
    #### pws
    @pyqtSlot()
    def table_pws_function(self):
        index=(self.table_pws.currentIndex())
        item = self.table_pws.item(index.row(), index.column()+1)
        item2 = self.table_pws.item(index.row(), index.column()+2)
        item3 = self.table_pws.item(index.row(), index.column()+3)
        item4  = self.table_pws.item(index.row(), index.column()+4)
        item5  = self.table_pws.item(index.row(), index.column()+5)
        
        print(index.row(), index.column())
        print(item.text())
        self.scrollArea.show()
        self.information_label.show()
        self.pws_editslotname.setText(item.text())
        self.pws_editloginname.setText(item2.text())
        self.pws_editpassword.setText(item3.text())
        self.pws_editOTP.setText(item4.text())
        self.pws_editnotes.setText(item5.text())
        self.PWS_ButtonSaveSlot.setVisible(False)
        self.ButtonChangeSlot.setVisible(True)
        self.PWS_ButtonDelete.setVisible(True)
        ### hides the otp creation stuff
        self.copy_current_otp.show()
        self.qr_code.hide()
        self.random_otp.hide()
        self.copy_otp.hide()
        self.pws_editOTP.setEchoMode(QtWidgets.QLineEdit.Password)
        self.show_hide_btn_2.hide()
    def add_table_pws(self):

        row = self.table_pws.rowCount()
        self.table_pws.insertRow(row)
        # self.table_pws.setItem(row , 0, (QtWidgets.QTableWidgetItem("Name")))
        # self.table_pws.setItem(row , 1, (QtWidgets.QTableWidgetItem("Username")))

        index = (self.table_pws.currentIndex())
        qline = self.pws_editslotname.text()
        qline2 = self.pws_editloginname.text()
        qline3 = self.pws_editpassword.text()
        qline4 = self.pws_editOTP.text()
        qline5 = self.pws_editnotes.toPlainText()
        res = "{} {} {}".format(qline, "\n", qline2)

        ##### creates otp on key

        if not self.device.is_auth_admin:
            self.ask_pin("admin")
            return

        name = qline
        if len(name) == 0:
            self.user_err("need non-empty name")
            return

        secret = qline4
        idx = row
        who = "totp"
        print(type(secret))
        print(type(idx))
        print(type(name))
        # @fixme: what are the secret allowed lengths/chars
        #if len(secret)
        print(row)

        ret = self.device.TOTP.write(idx, name, qline4)
        if not ret.ok:
            self.msg(f"failed writing to {who.upper()} slot #{idx+1} err: {ret.name}")
            print("ret not ok")
        else:
            self.msg(f"wrote {who.upper()} slot #{idx+1}")
            self.otp_secret.clear()
            self.slot_select_otp(idx)
            print("ret ok")
        
        self.table_pws.setCellWidget(row , 0, (EditButtonsWidget(self.table_pws, self.pop_up_copy, res)))
        self.table_pws.setItem(row , 1, (QtWidgets.QTableWidgetItem(qline)))
        self.table_pws.setItem(row , 2, (QtWidgets.QTableWidgetItem(qline2)))
        self.table_pws.setItem(row , 3, (QtWidgets.QTableWidgetItem(qline3)))
        self.table_pws.setItem(row , 4, (QtWidgets.QTableWidgetItem(qline4)))
        self.table_pws.setItem(row , 5, (QtWidgets.QTableWidgetItem(qline5)))
        self.pws_editslotname.setText("")
        self.pws_editloginname.setText("")
        self.pws_editpassword.setText("")
        self.pws_editOTP.setText("")
        self.pws_editnotes.setText("")
    ######################## adds the data existing of the key to the table
    def add_table_pws_from_key(self, x):
        row = self.table_pws.rowCount()
        print(row)
        self.table_pws.insertRow(row)
        # self.table_pws.setItem(row , 0, (QtWidgets.QTableWidgetItem("Name")))
        # self.table_pws.setItem(row , 1, (QtWidgets.QTableWidgetItem("Username")))

        index = (self.table_pws.currentIndex())
        qline = self.device.TOTP.get_name(x)
        qline2 = ""
        qline3 = ""
        qline4 = self.device.TOTP.get_code(x)
        qline5 = ""
        res = "{} {} {}".format(qline, "\n", qline2)

        

            
        self.table_pws.setCellWidget(row , 0, (EditButtonsWidget(self.table_pws, self.pop_up_copy, res)))
        self.table_pws.setItem(row , 1, (QtWidgets.QTableWidgetItem(qline)))
        self.table_pws.setItem(row , 2, (QtWidgets.QTableWidgetItem(qline2)))
        self.table_pws.setItem(row , 3, (QtWidgets.QTableWidgetItem(qline3)))
        self.table_pws.setItem(row , 4, (QtWidgets.QTableWidgetItem(qline4)))
        self.table_pws.setItem(row , 5, (QtWidgets.QTableWidgetItem(qline5)))
        self.pws_editslotname.setText("")
        self.pws_editloginname.setText("")
        self.pws_editpassword.setText("")
        self.pws_editOTP.setText("")
        self.pws_editnotes.setText("")

    def add_pws(self):
        self.scrollArea.show()
        self.information_label.show()
        self.PWS_ButtonSaveSlot.setVisible(True)
        self.ButtonChangeSlot.setVisible(False)
        self.PWS_ButtonDelete.setVisible(False)
        #self.set_visible(QtWidgets.QFrame, ["groupbox_pw"], True)
        #self.set_enabled(QtWidgets.QFrame, ["groupbox_pw"], True)
        #self.set_enabled(QtWidgets.QPushButton, ["PWS_ButtonSaveSlot", "PWS_ButtonClose"], True)
        self.pws_editslotname.setText("")
        self.pws_editloginname.setText("")
        self.pws_editpassword.setText("")
        self.pws_editOTP.setText("")
        self.pws_editnotes.setText("")
        ### shows the otp creation stuff again
        self.copy_current_otp.hide()
        self.qr_code.show()
        self.random_otp.show()
        self.copy_otp.show()
        self.pws_editOTP.setEchoMode(QtWidgets.QLineEdit.Normal)
        self.show_hide_btn_2.show()

    def delete_pws(self):
        index=(self.table_pws.currentIndex())
        self.table_pws.removeRow(index.row())
        self.table_pws.setCurrentCell(0, 0)
        
#############################################classes for the nitrokeys
#class Nitrokey_3(QtWidgets.QWidget):

# you use show() and hide() function to make it visible or not where you want it
    def change_pws(self):
        row = (self.table_pws.currentIndex()).row()
        self.table_pws.insertRow(row)

        index = (self.table_pws.currentIndex())
        qline = self.pws_editslotname.text()
        qline2 = self.pws_editloginname.text()
        qline3 = self.pws_editpassword.text()
        qline4 = self.pws_editOTP.text()
        qline5 = self.pws_editnotes.toPlainText()
        res = "{} {} {}".format(qline, "\n", qline2)

               
        self.table_pws.setCellWidget(row , 0, (EditButtonsWidget(self.table_pws, self.pop_up_copy, res)))
        self.table_pws.setItem(row , 1, (QtWidgets.QTableWidgetItem(qline)))
        self.table_pws.setItem(row , 2, (QtWidgets.QTableWidgetItem(qline2)))
        self.table_pws.setItem(row , 3, (QtWidgets.QTableWidgetItem(qline3)))
        self.table_pws.setItem(row , 4, (QtWidgets.QTableWidgetItem(qline4)))
        self.table_pws.setItem(row , 5, (QtWidgets.QTableWidgetItem(qline5)))


        
        self.table_pws.removeRow(index.row())
        self.table_pws.setCurrentCell(index.row()-1, 0)
    
    def filter_the_table(self):
        #searchbox
        for iterator in range(self.table_pws.rowCount()):
            self.table_pws.showRow(iterator)
            if (self.searchbox.text() not in self.table_pws.item(iterator,1).text()):
                self.table_pws.hideRow(iterator)

    def cancel_pws_2(self):
        self.set_visible(QtWidgets.QFrame, ["groupbox_pw"], True) #changed to true
        #self.set_enabled(QtWidgets.QFrame, ["groupbox_pw"], False)
        #self.set_enabled(QtWidgets.QPushButton, ["PWS_ButtonSaveSlot", "PWS_ButtonClose"], False)
    #### collapsing groupboxes
    def groupbox_parameters_collapse(self):
        self.collapse(self.groupbox_parameter, self.expand_button_parameter)
    # def groupbox_pws_collapse(self):
    #     self.collapse(self.groupbox_pws)
    def groupbox_manageslots_collapse(self):
        self.collapse(self.groupbox_notes, self.expand_button_notes)
    def groupbox_secretkey_collapse(self):
        self.collapse(self.groupbox_secretkey, self.expand_button_secretkey)
    @pyqtSlot(int)
    def slot_otp_hide(self, state):
        if state == 2:
            self.pws_editOTP.setEchoMode(QtWidgets.QLineEdit.Password)
        elif state == 0:
            self.pws_editOTP.setEchoMode(QtWidgets.QLineEdit.Normal)
    @pyqtSlot(int)
    def slot_pws_hide(self, state):
        if state == 2:
            self.pws_editpassword.setEchoMode(QtWidgets.QLineEdit.Password)
        elif state == 0:
            self.pws_editpassword.setEchoMode(QtWidgets.QLineEdit.Normal)
    @pyqtSlot(int)
    def slot_hidden_hide(self, state):
        if state == 0:
            self.storage.hidden_pw_1.setEchoMode(QtWidgets.QLineEdit.Password)
            self.storage.hidden_pw_2.setEchoMode(QtWidgets.QLineEdit.Password)
        elif state == 2:
            self.storage.hidden_pw_1.setEchoMode(QtWidgets.QLineEdit.Normal)
            self.storage.hidden_pw_2.setEchoMode(QtWidgets.QLineEdit.Normal)
    @pyqtSlot()
    def copyname(self):
        QApplication.clipboard().setText(self.pws_editslotname.text())
        # qtimer popup
        self.time_to_wait = 5
        self.pop_up_copy.setText("Data added to clipboard.") #{0} for time display
        self.pop_up_copy.setStyleSheet("background-color: #2B5DD1; color: #FFFFFF ; border-style: outset;" 
        "padding: 2px ; font: bold 20px ; border-width: 6px ; border-radius: 10px ; border-color: #2752B8;")
        self.pop_up_copy.show()
        self.timer = QTimer(self)
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self.changeContent)
        self.timer.start()  
    def changeContent(self):
        self.pop_up_copy.setText("Data added to clipboard.")
        self.time_to_wait -= 1
        if self.time_to_wait <= 0:
                self.pop_up_copy.hide()
                self.timer.stop()
    def closeEvent(self, event):
        lambda:self.timer.stop()
        event.accept()
    def copyusername(self):
        QApplication.clipboard().setText(self.pws_editloginname.text())
        # qtimer popup
        self.time_to_wait = 5
        self.pop_up_copy.setText("Data added to clipboard.") #{0} for time display
        self.pop_up_copy.setStyleSheet("background-color: #2B5DD1; color: #FFFFFF ; border-style: outset;" 
        "padding: 2px ; font: bold 20px ; border-width: 6px ; border-radius: 10px ; border-color: #2752B8;")
        self.pop_up_copy.show()
        self.timer = QTimer(self)
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self.changeContent)
        self.timer.start()  
    def copypw(self):
        QApplication.clipboard().setText(self.pws_editpassword.text())
        # qtimer popup
        self.time_to_wait = 5
        self.pop_up_copy.setText("Data added to clipboard.") #{0} for time display
        self.pop_up_copy.setStyleSheet("background-color: #2B5DD1; color: #FFFFFF ; border-style: outset;" 
        "padding: 2px ; font: bold 20px ; border-width: 6px ; border-radius: 10px ; border-color: #2752B8;")
        self.pop_up_copy.show()
        self.timer = QTimer(self)
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self.changeContent)
        self.timer.start()  
    def copyotp(self):
        QApplication.clipboard().setText(self.pws_editOTP.text())
        # qtimer popup
        self.time_to_wait = 5
        self.pop_up_copy.setText("Data added to clipboard.") #{0} for time display
        self.pop_up_copy.setStyleSheet("background-color: #2B5DD1; color: #FFFFFF ; border-style: outset;" 
        "padding: 2px ; font: bold 20px ; border-width: 6px ; border-radius: 10px ; border-color: #2752B8;")
        self.pop_up_copy.show()
        self.timer = QTimer(self)
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self.changeContent)
        self.timer.start()  

    #### FIDO2 related callbacks
    @pyqtSlot()
    def slot_toggle_otp_2(self):
        if self.radio_hotp_2.isChecked():
            self.radio_totp_2.setChecked(False)
            self.frame_hotp.show()
            self.frame_totp.hide()
        else:
            self.radio_hotp_2.setChecked(False)
            self.frame_totp.show()
            self.frame_hotp.hide()
#########################################################################################
# not in use for now
    #### OTP related callbacks
    @pyqtSlot()
    def slot_random_secret(self):
        self.otp_secret_type_hex.setChecked(True)
        cnt = int(self.otp_gen_len.text())
        self.otp_secret.setText(self.device.gen_random(cnt, hex=True).decode("utf-8"))

    @pyqtSlot()
    def slot_cancel_otp(self):
        _, _, otp_obj = self.get_active_otp()

        self.otp_secret.clear()
        self.slot_select_otp()

    @pyqtSlot()
    def slot_erase_otp(self):
        who, idx, otp_obj = self.get_active_otp()

        if not self.device.is_auth_admin:
            self.ask_pin("admin")
            return

        ret = otp_obj.erase(idx)
        if not ret.ok:
            self.msg(f"failed erase {who.upper()} #{idx + 1} err: {ret.name}")
        else:
            self.msg(f"erased {who.upper()} #{idx + 1}")
            self.slot_select_otp(idx)

    @pyqtSlot()
    def slot_otp_save_enable(self):
        self.otp_save_btn.setEnabled(True)
        self.otp_cancel_btn.setEnabled(True)

    @pyqtSlot()
    def slot_save_otp(self):
        who, idx, otp_obj = self.get_active_otp()

        if not self.device.is_auth_admin:
            self.ask_pin("admin")
            return

        name = self.otp_name.text()
        if len(name) == 0:
            self.user_err("need non-empty name")
            return

        secret = self.otp_secret.text()
        # @fixme: what are the secret allowed lengths/chars
        #if len(secret)

        ret = otp_obj.write(idx, name, secret)
        if not ret.ok:
            self.msg(f"failed writing to {who.upper()} slot #{idx+1} err: {ret.name}")
        else:
            self.msg(f"wrote {who.upper()} slot #{idx+1}")
            self.otp_secret.clear()
            self.slot_select_otp(idx)
    @pyqtSlot()
    def slot_select_otp(self, force_idx=None):
        who, idx, otp_obj = self.get_active_otp()

        if force_idx is not None and idx != force_idx:
            idx = force_idx
            self.otp_combo_box.setCurrentIndex(idx)

        if idx < 0 or idx is None:
            return

        name = otp_obj.get_name(idx)
        self.otp_name.setText(name)
        self.otp_combo_box.setItemText(idx, f"{who.upper()} #{idx+1} ({name})")

        if name:
            self.sig_status_upd.emit({"msg": otp_obj.get_code(idx)})

        self.otp_cancel_btn.setEnabled(False)
        self.otp_save_btn.setEnabled(False)

    @pyqtSlot()
    def slot_toggle_otp(self):
        who, idx, otp_obj = self.get_active_otp()
        if who == "totp":
            # labels
            self.otp_len_label.setText("TOTP length:")
            #self.set_visible(QtWidgets.QLabel, ["label_6"], False)
            self.set_visible(QtWidgets.QLabel, ["intervalLabel"], True)

            # spacers + spin-box
            self.set_visible(QtWidgets.QSpinBox, ["intervalSpinBox"], True)

            # moving seed
            self.set_visible(QtWidgets.QPushButton,
                ["setToRandomButton", "setToZeroButton"], False)
            self.set_visible(QtWidgets.QLineEdit, ["counterEdit"], False)
        else:
            # labels
            self.otp_len_label.setText("HOTP length:")
            self.set_visible(QtWidgets.QLabel, ["intervalLabel"], False)
            #self.set_visible(QtWidgets.QLabel, ["label_6"], True)

            # spacers + spin-box
            self.set_visible(QtWidgets.QSpinBox, ["intervalSpinBox"], False)

            # moving seed
            self.set_visible(QtWidgets.QPushButton,
                             ["setToRandomButton", "setToZeroButton"], True)
            self.set_visible(QtWidgets.QLineEdit, ["counterEdit"], True)

        # drop down contents
        self.otp_combo_box.clear()
        for idx in range(otp_obj.count):
            name = otp_obj.get_name(idx) or ""
            self.otp_combo_box.addItem(f"{who.upper()} #{idx+1} ({name})")
            if idx == 0:
                self.otp_name.setText(name)

    @pyqtSlot(int)
    def slot_secret_hide(self, state):
        if state == 2:
            self.otp_secret.setEchoMode(QtWidgets.QLineEdit.Password)
        elif state == 0:
            self.otp_secret.setEchoMode(QtWidgets.QLineEdit.Normal)

    @pyqtSlot(str)
    def slot_confirm_auth(self, who):
        self.unlock_pws_btn.setEnabled(False)
        self.lock_btn.setEnabled(True)

        self.msg(f"{who.capitalize()} authenticated!")

    @pyqtSlot(dict)
    def slot_lock(self, status):
        self.unlock_pws_btn.setEnabled(True)
        self.lock_btn.setEnabled(False)
        self.sig_disconnected.emit()

    #### app-wide slots
    @pyqtSlot(dict, str)
    def slot_auth(self, opts, pin=None):
        who = opts.get("who")
        assert who in ["user", "admin"]
        who_cap = who.capitalize()

        auth_func = self.device.user_auth if who == "user" else self.device.admin_auth
        if pin is not None and auth_func(pin).ok:
            self.sig_confirm_auth.emit(who)
            self.pin_dialog.reset()
            self.user_info(f"{who_cap} auth successful", parent=self.pin_dialog)
        else:
            self.user_err(f"The provided {who}-PIN is not correct, please retry!",
                          f"{who_cap} not authenticated",
                          parent=self.pin_dialog)
            self.ask_pin(who)
###############################################################################################

    @pyqtSlot()
    def init_gui(self):
        self.init_otp_conf()
        """self.init_otp_general()"""
        self.init_pws()
        # detect already connected nk3s
        self.detect_nk3()

    @pyqtSlot()
    def job_connect_device(self):
        devs = nk_api.BaseLibNitrokey.list_devices()
        dev = None
        if self.device is not None:
            return {"device": self.device, "connected": self.device.connected,
                    "status": self.device.status, "serial": self.device.serial}
        ####### "serial" to get the serial number
        if len(devs) > 0:
            _dev = devs[tuple(devs.keys())[0]]

            if _dev["model"] == 1:
                dev = nk_api.NitrokeyPro()
                print("pro")
                #print(self.device.status)
                #print(self.device.serial)
            elif _dev["model"] == 2:
                dev = nk_api.NitrokeyStorage()
                print("storage")
                #print(self.device.status)
                #print(self.device.serial)
            
            else:
                self.msg("Unknown device model detected")
                return {"connected": False}

            try:
                dev.connect()
                self.device = dev
            except nk_api.DeviceNotFound as e:
                self.device = None
                self.msg("Connection failed, already in use?")
                return {"connected": False}

        if not self.device.connected:
            self.device = None
            return {"connected": False}

        status = dev.status
        self.msg({"status": status, "connected": status["connected"]})

        return {"connected": status["connected"], "status": status, "device": dev}

    @pyqtSlot(dict)
    def update_status_bar(self, res_dct):
        cur_msg = self.status_bar.currentMessage
        append_msg = lambda s: self.status_bar.showMessage(
            s + ((" || " + cur_msg().strip()) if cur_msg().strip() else ""))

        # directly show passed 'msg'
        if "msg" in res_dct:
            append_msg(res_dct["msg"])
            return

        # not connected, show default message
        if not res_dct.get("connected"):
            self.status_bar.showMessage("Not connected")
            return

        # connected, show status information (if available)
        info = res_dct.get("status")
        if info:
            append_msg(f"Device: {info['model'].friendly_name}")
            append_msg(f"Serial: {info['card_serial_u32']}")
            append_msg(f"FW Version: {info['fw_version'][0]}.{info['fw_version'][1]}")
            append_msg(f"PIN Retries - (Admin/User): "
                       f"{info['admin_pin_retries']}/{info['user_pin_retries']}")

    @pyqtSlot(dict)
    def job_nk_connected(self, res_dct):
        if not res_dct["connected"]:
            self.msg("Not connected")
            return

        info = res_dct["status"]

        # enable and show needed widgets
        func = lambda w: (w.setEnabled(True), w.setVisible(True))
        self.apply_by_name([#"tab_pws", "btn_dial_lock",    # overview
                            #"frame", #"groupbox_manageslots", "groupbox_parameters",      # otp
                            #"frame_4",                         # otp config
                            #"groupbox_pw"                          # pws
                           ], func)

        if info["model"] == nk_api.DeviceModel.NK_STORAGE:
            self.apply_by_name(["pushButton_storage", "btn_dial_HV"], func) # overview
        elif info["model"] == nk_api.DeviceModel.NK_PRO:
            self.apply_by_name(["pushButton_pro", "btn_dial_HV"], func) # overview
    #### backend callbacks
    @pyqtSlot()
    def backend_cb_hello(self):
        print(f"hello signaled from worker, started successfully")

    @pyqtSlot(int)
    def slot_tab_changed(self, idx):
        pass

    #### main-window callbacks
    @pyqtSlot()
    def pro_btn_pressed(self):
        self.tabs.show()
        self.tabs.setTabEnabled(1, True)
        self.tabs.setTabEnabled(2, True)
        self.tabs.setTabEnabled(3, True)
        self.tabs.setTabEnabled(4, False)
        self.tabs.setTabEnabled(5, False)
        # set stylesheet of tabwidget to QTabBar::tab:disabled { width: 0; height: 0; margin: 0; padding: 0; border: none; } if you want to make the tabs invisible.
        #self.pro_btn.setStyleSheet(green)
        self.storage_btn.setChecked(False)
        self.fido2_btn.setChecked(False)
        self.frame_s.setVisible(False)
        self.frame_f.setVisible(False)
        self.frame_p.setVisible(True)
    @pyqtSlot()
    def storage_btn_pressed(self):
        self.tabs.show()
        self.tabs.setTabEnabled(1, True)
        self.tabs.setTabEnabled(2, True)
        self.tabs.setTabEnabled(3, True)
        self.tabs.setTabEnabled(4, True)
        self.tabs.setTabEnabled(5, False)
        self.pro_btn.setChecked(False)
        #self.storage_btn.setStyleSheet(green)
        self.fido2_btn.setChecked(False)
        self.frame_s.setVisible(True)
        self.frame_f.setVisible(False)
        self.setup_wizard.exec()

    @pyqtSlot()
    def fido2_btn_pressed(self):
        self.tabs.show()
        self.tabs.setTabEnabled(1, False)
        self.tabs.setTabEnabled(2, False)
        self.tabs.setTabEnabled(3, False)
        self.tabs.setTabEnabled(4, False)
        self.tabs.setTabEnabled(5, True)
        self.pro_btn.setChecked(False)
        self.storage_btn.setChecked(False)
        #self.fido2_btn.setStyleSheet(green)
        self.frame_s.setVisible(False)
        self.frame_f.setVisible(True)
        self.frame_p.setVisible(False)
    @pyqtSlot()
    def about_button_pressed(self):
        self.about_dialog.show()
        ##test
    @pyqtSlot()
    def slot_quit_button_pressed(self):
        self.backend_thread.stop_loop()
        self.backend_thread.wait()
        #self.app.quit()
        QApplication.quit() 

    @pyqtSlot()
    def slot_lock_button_pressed(self):
        if not self.device.connected:
            self.msg({"connected": False})
            self.sig_disconnected.emit()
            return

        self.device.lock()
        self.msg("Locked device!")
        self.sig_lock.emit(self.device.status)

    @pyqtSlot()
    def unlock_pws_button_pressed(self):
        if not self.device.connected:
            self.msg({"connected": False})
            self.sig_disconnected.emit()
            return

        self.ask_pin("user")


    #### init main windows
    @pyqtSlot()
    def init_overview(self):
        names = ["btn_dial_EV", "btn_dial_HV", "btn_dial_PWS", "btn_dial_lock"]
        self.set_enabled(QtWidgets.QPushButton, names, False)

    @pyqtSlot()
    def init_otp_conf(self):
        #self.set_enabled(QtWidgets.QGroupBox, ["groupbox_pw", "groupbox_manageslots", "groupbox_parameters"], False)
        #self.set_enabled(QtWidgets.QPushButton, ["writeButton", "cancelButton"], False)
        #btns = ["setToRandomButton", "setToZeroButton"]
        #self.set_visible(QtWidgets.QPushButton, btns, False)
        #lbls = ["l_supportedLength", "labelNotify", "label_6"]
        #self.set_visible(QtWidgets.QLabel, lbls , False)
        self.set_visible(QtWidgets.QProgressBar, ["progressBar"], False)
        #self.set_visible(QtWidgets.QLineEdit, ["counterEdit"], False)
        self.radio_totp_2.setChecked(True)
        self.radio_hotp_2.setChecked(False)
        #self.set_visible(QtWidgets.QFrame, ["groupbox_manageslots", "groupbox_parameters"], False)
    """@pyqtSlot()
    def init_otp_general(self):
        self.set_enabled(QtWidgets.QFrame, ["frame_4"], False)
        names = ["generalCancelButton", "writeGeneralConfigButton"]
        self.set_enabled(QtWidgets.QPushButton, names, False)"""

    @pyqtSlot()
    def init_pws(self):
        btn_cls = QtWidgets.QPushButton
        #self.set_visible(QtWidgets.QFrame, ["groupbox_pw"], False)
        #self.set_enabled(QtWidgets.QFrame, ["groupbox_pw"], False)
        self.set_visible(btn_cls, ["PWS_Lock"], False)
        self.set_visible(QtWidgets.QProgressBar, ["PWS_progressBar"], False)
        names = ["PWS_ButtonEnable", "PWS_ButtonSaveSlot", "PWS_ButtonClose"]
        #self.set_enabled(btn_cls, names, False)
        #self.set_enabled(QtWidgets.QLabel, ["l_utf8_info"], False)
        self.collapse(self.groupbox_parameter,  self.expand_button_parameter)
        self.collapse(self.groupbox_notes,  self.expand_button_notes)
        self.collapse(self.groupbox_secretkey, self.expand_button_secretkey)
        #self.groupbox_secretkey.hide()
        self.ButtonChangeSlot.setVisible(False)
        self.PWS_ButtonDelete.setVisible(False)
        self.frame_pro.hide()
        self.frame_fido2.hide()
        self.frame_storage.hide()
        self.frame_hotp.hide()
        self.expand_button_secret.hide()
        self.scrollArea.hide()
        self.information_label.hide()
        self.copy_current_otp.hide()
        #self.loading_screen = LoadingScreen()

        self.main_key.hide()
        self.sub_key_key.hide()
     
        self.tabs.hide()
        self.pro_btn.hide()
        self.storage_btn.hide()
        self.fido2_btn.hide()
        self.others_btn.hide()
        self.show()

def main():
    # backend thread init
    QtUtilsMixIn.backend_thread = BackendThread()

    app = QtWidgets.QApplication(sys.argv)
  
    # set stylesheet
    file = QFile(":/light.qss")
    file.open(QFile.ReadOnly | QFile.Text)
    stream = QTextStream(file)
    app.setStyleSheet(stream.readAll())
    window = GUI(app)
    app.exec()

if __name__ == "__main__":
    main()
    