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
# extras
import datetime
import time
from pathlib import Path
from queue import Queue
from typing import List, Optional, Tuple, Type, TypeVar
import webbrowser
# pyqt5
from PyQt5 import QtWidgets, uic
from PyQt5.QtCore import Qt, QThread, pyqtSignal, pyqtSlot
from PyQt5.Qt import QApplication, QProgressBar
# Nitrokey 2
from pynitrokey import libnk as nk_api
# Nitrokey 3
from pynitrokey.nk3 import list as list_nk3
# import wizards and stuff
from nitropyapp.setup_wizard import SetupWizard
from nitropyapp.qt_utils_mix_in import QtUtilsMixIn
from nitropyapp.about_dialog import AboutDialog
from nitropyapp.key_generation import KeyGeneration
from nitropyapp.change_pin_dialog import ChangePinDialog
from nitropyapp.storage_wizard import Storage
from nitropyapp.loading_screen import LoadingScreen
from nitropyapp.edit_button_widget import EditButtonsWidget
from nitropyapp.pin_dialog import PINDialog
from nitropyapp.insert_nitrokey import InsertNitrokey
from nitropyapp.windows_notification import WindowsUSBNotification
from nitropyapp.pynitrokey_for_gui import Nk3Context, list, version, wink, nk3_update, nk3_update_helper, change_pin
from nitropyapp.tray_notification import TrayNotification
from nitropyapp.nk3_button import Nk3Button
#import nitropyapp.libnk as nk_api
import nitropyapp.ui.breeze_resources
#pyrcc5 -o gui_resources.py ui/resources.qrc
import nitropyapp.gui_resources

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
#### PWS related callbacks

class GUI(QtUtilsMixIn, QtWidgets.QMainWindow):

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

            w = WindowsUSBNotification(self.detect_nk3, self.remove_nk3)
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
        # import other ui-files

        self.key_generation = KeyGeneration(qt_app)
        self.key_generation.load_ui(ui_dir / "key_generation.ui", self.key_generation)
        self.key_generation.init_keygen()

        self.about_dialog = AboutDialog(qt_app)
        self.about_dialog.load_ui(ui_dir / "aboutdialog.ui", self.about_dialog)

        self.setup_wizard = SetupWizard(qt_app)
        self.setup_wizard.load_ui(ui_dir / "setup-wizard.ui", self.setup_wizard)
        self.setup_wizard.init_setup()

        self.insert_Nitrokey = InsertNitrokey(qt_app)
        self.insert_Nitrokey.load_ui(ui_dir / "insert_Nitrokey.ui", self.insert_Nitrokey)
        self.insert_Nitrokey.init_insertNitrokey()

        self.change_pin_dialog = ChangePinDialog(qt_app)
        self.change_pin_dialog.load_ui(ui_dir / "change_pin_dialog.ui", self.change_pin_dialog)
        self.change_pin_dialog.init_change_pin()
        ################################################################################
        #### get widget objects
        ## app wide widgets
        self.status_bar = _get(_qt.QStatusBar, "statusBar")
        self.menu_bar = _get(_qt.QMenuBar, "menuBar")
        self.tabs = _get(_qt.QTabWidget, "tabWidget")
        self.tab_otp_conf = _get(_qt.QWidget, "tab")
        self.tab_otp_gen = _get(_qt.QWidget, "tab_2")
        self.tab_pws = _get(_qt.QWidget, "tab_3")
        self.tab_settings = _get(_qt.QWidget, "tab_4")
        self.tab_overview = _get(_qt.QWidget, "tab_5")
        self.tab_fido2 = _get(_qt.QWidget, "tab_6")
        self.tab_storage = _get(_qt.QWidget, "tab_7")
        self.about_button = _get(_qt.QPushButton, "btn_about")
        self.help_btn = _get(_qt.QPushButton, "btn_dial_help")
        self.quit_button = _get(_qt.QPushButton, "btn_dial_quit")
        self.settings_btn = _get(_qt.QPushButton, "btn_settings")
        self.lock_btn = _get(_qt.QPushButton, "btn_dial_lock")
        self.l_insert_Nitrokey = _get(_qt.QFrame, "label_insert_Nitrokey")
        self.progressBarUpdate = _get(_qt.QProgressBar, "progressBar_Update")
        ## overview
        self.navigation_frame = _get(_qt.QFrame, "vertical_navigation")
        self.nitrokeys_window = _get(_qt.QScrollArea, "Nitrokeys")
        self.layout_nk_btns = QtWidgets.QVBoxLayout()
        self.layout_nk_btns.setContentsMargins(0,0,0,0)
        self.layout_nk_btns.setSpacing(0)
        self.layout_nk_btns.setAlignment(Qt.AlignTop)
        ### nk3 frame
        self.nk3_lineedit_uuid = _get(_qt.QLineEdit, "nk3_lineedit_uuid")
        self.nk3_lineedit_path = _get(_qt.QLineEdit, "nk3_lineedit_path")
        self.nk3_lineedit_version = _get(_qt.QLineEdit, "nk3_lineedit_version")
        self.update_nk3_btn = _get(_qt.QPushButton, "update_nk3_btn")
        self.nitrokey3_frame = _get(_qt.QFrame, "Nitrokey3")
        self.buttonLayout_nk3 = _get(_qt.QVBoxLayout, "buttonLayout_nk3")
        ################################################################################
        # set some props, initial enabled/visible, finally show()
        self.setAttribute(Qt.WA_DeleteOnClose)

        self.tabs.setCurrentWidget(self.tab_overview)
        self.tabs.currentChanged.connect(self.slot_tab_changed)

        self.init_gui()
        self.show()

        self.device = None

        ################################################################################
        ######nk3
        self.help_btn.clicked.connect(lambda:webbrowser.open('https://docs.nitrokey.com/nitrokey3'))
        self.lock_btn.clicked.connect(self.slot_lock_button_pressed)
        self.about_button.clicked.connect(self.about_button_pressed)
        #self.settings_btn.clicked.connect()
        ################################################################################
        #### connections for functional signals
        ## generic / global
        ## overview
    ### experimental idea to differ between removed and added
    def device_connect(self):
        for dvc in iter(functools.partial(self.monitor.poll, 3), None):
            if dvc.action == "remove":
                print("removed")
                self.remove_nk3()
            elif dvc.action == "bind":
                print("BIND")
                self.detect_nk3()

    def detect_nk3(self):
        if len(list_nk3()):
            list_of_added = [y.uuid for y in Nk3Button.get()]
            print("list of added:", list_of_added)
            for x in list_nk3():
                if  x.uuid() not in list_of_added:
                    self.device = x
                    uuid = self.device.uuid()
                    if uuid:
                        print(f"{self.device.path}: {self.device.name} {self.device.uuid():X}")
                    else:
                        print(f"{self.device.path}: {self.device.name}")
                        print("no uuid")
                    Nk3Button(self.device, self.nitrokeys_window, self.layout_nk_btns, self.nitrokey3_frame, self.nk3_lineedit_uuid, self.nk3_lineedit_path, self.nk3_lineedit_version, self.tabs, self.update_nk3_btn, self.progressBarUpdate, self.change_pin_open_dialog, self.change_pin_dialog, self.buttonLayout_nk3)
                    TrayNotification("Nitrokey 3", "Nitrokey 3 connected.","Nitrokey 3 connected.")
                    self.device = None
                    print("nk3 connected")
                    self.l_insert_Nitrokey.hide()
                else:
                    nk3_btn_same_uuid = [y for y in Nk3Button.get() if (y.uuid == x.uuid())]
                    for i in nk3_btn_same_uuid:
                        if x.path != i.path:
                            i.update(x)
        else:
            print("no nk3 in list. no admin?")
    
    def remove_nk3(self):
        list_of_removed = []
        if len(list_nk3()):
            print("list nk3:", list_nk3())
            list_of_nk3s = [x.uuid() for x in list_nk3()]
            list_of_removed_help = [y for y in Nk3Button.get() if (y.uuid not in list_of_nk3s)]
            list_of_removed = list_of_removed + list_of_removed_help
        else:
            list_of_removed = list_of_removed + Nk3Button.get()
        for k in list_of_removed:
            k.__del__()
            Nk3Button.list_nk3_keys.remove(k)

    def show_only_this_tab(self,a):
        for idx in range(self.tabs.count()):
            self.tabs.setTabEnabled(idx, False)
            self.tabs.setTabVisible(idx, False) 
        self.tabs.setTabEnabled(a, True)
        self.tabs.setTabVisible(a, True)

    def init_gui(self):
        self.show_only_this_tab(0)
        self.nitrokey3_frame.hide()
        self.progressBarUpdate.hide()
        self.detect_nk3()

    #### backend callbacks
    @pyqtSlot()
    def backend_cb_hello(self):
        print(f"hello signaled from worker, started successfully")

    @pyqtSlot(int)
    def slot_tab_changed(self, idx):
        pass

    #### main-window callbacks
    @pyqtSlot()
    def about_button_pressed(self):
        self.about_dialog.show()

    @pyqtSlot()
    def change_pin_open_dialog(self):
        self.change_pin_dialog.show()

    @pyqtSlot()
    def slot_lock_button_pressed(self):
        # removes side buttos for nk3 (for now)
        print("locked")
        for x in Nk3Button.get():
            x.__del__()
