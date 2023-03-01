# use "pbs" for packaging...
# pip-run -> pyqt5
# pip-dev -> pyqt5-stubs
import functools
import logging
import platform
import webbrowser
from queue import Queue

# Nitrokey 3
from pynitrokey.nk3 import list as list_nk3

# pyqt5
from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt, QThread, pyqtSignal, pyqtSlot

from nitrokeyapp.about_dialog import AboutDialog
from nitrokeyapp.change_pin_dialog import ChangePinDialog
from nitrokeyapp.insert_nitrokey import InsertNitrokey
from nitrokeyapp.key_generation import KeyGeneration
from nitrokeyapp.nk3_button import Nk3Button

# from nitrokeyapp.loading_screen import LoadingScreen
from nitrokeyapp.pin_dialog import PINDialog
from nitrokeyapp.qt_utils_mix_in import QtUtilsMixIn
from nitrokeyapp.set_pin_dialog import SetPinDialog

# import wizards and stuff
from nitrokeyapp.setup_wizard import SetupWizard
from nitrokeyapp.tray_notification import TrayNotification
from nitrokeyapp.ui.mainwindow_ui import Ui_MainWindow
from nitrokeyapp.windows_notification import WindowsUSBNotification

# import nitrokeyapp.ui.breeze_resources
# pyrcc5 -o gui_resources.py ui/resourcces.qrc
# import nitrokeyapp.gui_resources


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
# securitySearchForm = resource_path("securitySearchForm.ui")
# popboxForm = resource_path("popbox.ui")

# pyrcc4 -py3 resources.qrc -o resources_rc.py

logger = logging.getLogger(__name__)

# PWS related callbacks


class GUI(QtUtilsMixIn, QtWidgets.QMainWindow):
    def __init__(self, qt_app: QtWidgets.QApplication):
        QtWidgets.QMainWindow.__init__(self)
        QtUtilsMixIn.__init__(self)
        self.backend_thread.hello.connect(self.backend_cb_hello)
        self.backend_thread.start()
        # linux
        if platform.system() == "Linux":
            # pyudev stuff
            import pyudev
            from pyudev.pyqt5 import MonitorObserver

            # start monitoring usb
            self.context = pyudev.Context()
            self.monitor = pyudev.Monitor.from_netlink(self.context)
            self.monitor.filter_by(subsystem="usb")
            self.observer = MonitorObserver(self.monitor)
            self.observer.deviceEvent.connect(self.device_connect)
            self.monitor.start()
        # windows
        if platform.system() == "Windows":
            logger.info("OS:Windows")
            WindowsUSBNotification(self.detect_nk3, self.remove_nk3)

        # loads main ui
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        # import other ui-files
        # used
        self.change_pin_dialog = ChangePinDialog(self)
        self.set_pin_dialog = SetPinDialog(self)
        self.about_dialog = AboutDialog(qt_app)
        # unused (atm)
        self.key_generation = KeyGeneration(qt_app)
        self.setup_wizard = SetupWizard(qt_app)
        self.insert_nitrokey = InsertNitrokey(qt_app)
        self.pin_dialog = PINDialog(qt_app)

        # get widget objects
        # app wide widgets
        # self.status_bar = _get(_qt.QStatusBar, "statusBar")
        # self.menu_bar = _get(_qt.QMenuBar, "menuBar")
        self.tabs = self.ui.tabWidget
        self.tab_otp_conf = self.ui.tab
        self.tab_otp_gen = self.ui.tab_2
        self.tab_pws = self.ui.tab_3
        self.tab_settings = self.ui.tab_4
        self.tab_overview = self.ui.tab_5
        # self.tab_fido2 = self.ui.tab_6
        # self.tab_storage = self.ui.tab_7
        self.about_button = self.ui.btn_about
        self.help_btn = self.ui.btn_dial_help
        # self.quit_button = self.ui.btn_dial_quit
        self.settings_btn = self.ui.btn_settings
        self.lock_btn = self.ui.btn_dial_lock
        self.l_insert_nitrokey = self.ui.label_insert_Nitrokey
        self.progressbarupdate = self.ui.progressBar_Update
        # overview
        self.navigation_frame = self.ui.vertical_navigation
        self.nitrokeys_window = self.ui.Nitrokeys
        self.layout_nk_btns = QtWidgets.QVBoxLayout()
        self.layout_nk_btns.setContentsMargins(0, 0, 0, 0)
        self.layout_nk_btns.setSpacing(0)
        self.layout_nk_btns.setAlignment(Qt.AlignTop)
        # nk3 frame
        self.nk3_lineedit_uuid = self.ui.nk3_lineedit_uuid
        self.nk3_lineedit_path = self.ui.nk3_lineedit_path
        self.nk3_lineedit_version = self.ui.nk3_lineedit_version
        self.nitrokey3_frame = self.ui.Nitrokey3
        self.buttonlayout_nk3 = self.ui.buttonLayout_nk3
        # set some props, initial enabled/visible, finally show()
        self.setAttribute(Qt.WA_DeleteOnClose)

        self.tabs.setCurrentWidget(self.tab_overview)
        self.tabs.currentChanged.connect(self.slot_tab_changed)

        self.init_gui()
        self.show()

        self.device = None

        # nk3
        self.help_btn.clicked.connect(
            lambda: webbrowser.open("https://docs.nitrokey.com/nitrokey3")
        )
        self.lock_btn.clicked.connect(self.slot_lock_button_pressed)
        self.about_button.clicked.connect(self.about_button_pressed)
        # self.settings_btn.clicked.connect()
        # connections for functional signals
        # generic / global
        # overview

    # experimental idea to differ between removed and added
    def device_connect(self):
        for dvc in iter(functools.partial(self.monitor.poll, 3), None):
            if dvc.action == "remove":
                logger.info("removed")
                self.remove_nk3()
            elif dvc.action == "bind":
                logger.info("BIND")
                self.detect_nk3()

    def detect_nk3(self):
        if len(list_nk3()):
            list_of_added = [y.uuid for y in Nk3Button.get()]
            logger.info("list of added:", list_of_added)
            for device in list_nk3():
                if device.uuid() not in list_of_added:
                    self.device = device
                    uuid = self.device.uuid()
                    if uuid:
                        logger.info(
                            f"{self.device.path}: {self.device.name} {self.device.uuid()}"
                        )
                    else:
                        logger.info(f"{self.device.path}: {self.device.name}")
                        logger.info("no uuid")
                    Nk3Button(
                        self.device,
                        self.nitrokeys_window,
                        self.layout_nk_btns,
                        self.nitrokey3_frame,
                        self.nk3_lineedit_uuid,
                        self.nk3_lineedit_path,
                        self.nk3_lineedit_version,
                        self.tabs,
                        self.progressbarupdate,
                        self.change_pin_open_dialog,
                        self.set_pin_open_dialog,
                        self.change_pin_dialog,
                        self.set_pin_dialog,
                        self.buttonlayout_nk3,
                    )
                    TrayNotification(
                        "Nitrokey 3", "Nitrokey 3 connected.", "Nitrokey 3 connected."
                    )
                    self.device = None
                    logger.info("nk3 connected")
                    self.l_insert_nitrokey.hide()
                else:
                    nk3_btn_same_uuid = [
                        y for y in Nk3Button.get() if y.uuid == device.uuid()
                    ]
                    for i in nk3_btn_same_uuid:
                        if device.path != i.path:
                            i.update(device)
        else:
            logger.info("no nk3 in list. no admin?")

    def remove_nk3(self):
        list_of_removed = []
        if len(list_nk3()):
            logger.info("list nk3:", list_nk3())
            list_of_nk3s = [x.uuid() for x in list_nk3()]
            list_of_removed_help = [
                y for y in Nk3Button.get() if y.uuid not in list_of_nk3s
            ]
            list_of_removed = list_of_removed + list_of_removed_help
        else:
            list_of_removed = list_of_removed + Nk3Button.get()
        for k in list_of_removed:
            k.__del__()
            logger.info("nk3 instance removed")

    def show_only_this_tab(self, tab):
        for idx in range(self.tabs.count()):
            self.tabs.setTabEnabled(idx, False)
            self.tabs.setTabVisible(idx, False)
        self.tabs.setTabEnabled(tab, True)
        self.tabs.setTabVisible(tab, True)

    def init_gui(self):
        self.show_only_this_tab(0)
        self.tabs.hide()
        self.nitrokey3_frame.hide()
        self.progressbarupdate.hide()
        self.lock_btn.setEnabled(False)
        self.settings_btn.setEnabled(False)
        self.detect_nk3()

    # backend callbacks
    @pyqtSlot()
    def backend_cb_hello(self):
        logger.info("hello signaled from worker, started successfully")

    @pyqtSlot(int)
    def slot_tab_changed(self, idx):
        pass

    # main-window callbacks
    @pyqtSlot()
    def about_button_pressed(self):
        self.about_dialog.exec_()

    @pyqtSlot()
    def change_pin_open_dialog(self):
        self.change_pin_dialog.exec_()

    @pyqtSlot()
    def set_pin_open_dialog(self):
        self.set_pin_dialog.exec_()

    @pyqtSlot()
    def slot_lock_button_pressed(self):
        # removes side buttos for nk3 (for now)
        logger.info("nk3 instance removed (lock button)")
        for x in Nk3Button.get():
            x.__del__()
