# use "pbs" for packaging...
# pip-run -> pyqt5
# pip-dev -> pyqt5-stubs
import functools
import logging
import platform
import webbrowser
from itertools import filterfalse
from typing import Optional

# Nitrokey 3
from pynitrokey.nk3 import Nitrokey3Device
from pynitrokey.nk3 import list as list_nk3
from pynitrokey.nk3.bootloader.lpc55 import Nitrokey3BootloaderLpc55
from pynitrokey.nk3.bootloader.nrf52 import Nitrokey3BootloaderNrf52

# pyqt5
from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt, pyqtSlot

from nitrokeyapp.about_dialog import AboutDialog
from nitrokeyapp.information_box import InfoBox
from nitrokeyapp.nk3_button import Nk3Button

# from nitrokeyapp.loading_screen import LoadingScreen
from nitrokeyapp.qt_utils_mix_in import QtUtilsMixIn

# import wizards and stuff
from nitrokeyapp.ui.mainwindow import Ui_MainWindow
from nitrokeyapp.windows_notification import WindowsUSBNotifi

# import nitrokeyapp.ui.breeze_resources
# pyrcc5 -o gui_resources.py ui/resourcces.qrc
# import nitrokeyapp.gui_resources

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
            WindowsUSBNotifi(self.detect_nk3, self.remove_nk3)

        # loads main ui
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        # import other ui-files
        # used
        self.about_dialog = AboutDialog(qt_app)

        # get widget objects
        # app wide widgets
        # self.status_bar = _get(_qt.QStatusBar, "statusBar")
        # self.menu_bar = _get(_qt.QMenuBar, "menuBar")
        self.information_frame = self.ui.information_frame
        self.label_information_icon = self.ui.label_information_icon
        self.label_information = self.ui.label_information
        self.info_frame = InfoBox(
            self.information_frame, self.label_information_icon, self.label_information
        )
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
        self.progressbardownload = self.ui.progressBar_Download
        self.progressbarfinalization = self.ui.progressBar_Finalization
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

        self.device: Optional[Nitrokey3Device] = None

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
    def device_connect(self) -> None:
        import pyudev

        dvc: pyudev.Device
        for dvc in iter(functools.partial(self.monitor.poll, 3), None):
            if dvc.action == "remove":
                logger.info("removed")
                self.remove_nk3()
            elif dvc.action == "bind":
                logger.info("BIND")
                self.detect_nk3()

    def device_in_bootloader(self, device: object) -> bool:
        return isinstance(device, Nitrokey3BootloaderNrf52) or isinstance(
            device, Nitrokey3BootloaderLpc55
        )

    def toggle_update_btn(self) -> None:
        if len(Nk3Button.get()) == 0:
            self.l_insert_nitrokey.show()
        if len(Nk3Button.get()) > 1:
            self.info_frame.set_text_durable(
                "Please remove all Nitrokey 3 devices except the one you want to update."
            )
            for i in Nk3Button.get():
                i.own_update_btn.setEnabled(False)
                i.own_update_btn.setToolTip(
                    "Please remove all Nitrokey 3 devices except the one you want to update."
                )
        else:
            for i in Nk3Button.get():
                self.info_frame.hide()
                i.own_update_btn.setEnabled(True)
                i.own_update_btn.setToolTip("")

    def detect_nk3(self) -> None:
        nk3_list = list_nk3()
        nk3_list = list(filterfalse(self.device_in_bootloader, nk3_list))
        if len(nk3_list):
            list_of_added = [str(y.uuid)[:-4] for y in Nk3Button.get()]
            logger.info(f"list of added: {list_of_added}")
            for device in nk3_list:
                if str(device.uuid())[:-4] not in list_of_added:
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
                        self.progressbardownload,
                        self.progressbarfinalization,
                        # self.change_pin_open_dialog,
                        # self.set_pin_open_dialog,
                        # self.change_pin_dialog,
                        # self.set_pin_dialog,
                        self.buttonlayout_nk3,
                        self.info_frame,
                    )
                    self.device = None
                    logger.info("nk3 connected")
                    self.l_insert_nitrokey.hide()
                    self.toggle_update_btn()
                else:
                    nk3_btn_same_uuid = [
                        y
                        for y in Nk3Button.get()
                        if str(y.uuid)[:-4] == str(device.uuid())[:-4]
                    ]
                    for i in nk3_btn_same_uuid:
                        if device.path != i.path:
                            i.set_device(device)
        else:
            logger.info("no nk3 in list. no admin?")

    def remove_nk3(self) -> None:
        list_of_removed: list[Nk3Button] = []
        nk3_list_1 = list_nk3()
        nk3_list_1 = list(filterfalse(self.device_in_bootloader, nk3_list_1))
        if Nk3Button.get():
            if len(nk3_list_1):
                logger.info(f"list nk3: {nk3_list_1}")
                list_of_nk3s = [str(x.uuid())[:-4] for x in nk3_list_1]
                list_of_removed_help = [
                    y
                    for y in Nk3Button.get()
                    if (
                        (str(y.uuid)[:-4] not in list_of_nk3s)
                        and (y.ctx.updating is False)
                    )
                ]
                list_of_removed = list_of_removed + list_of_removed_help
            elif Nk3Button.get()[0].ctx.updating is False:
                list_of_removed = list_of_removed + Nk3Button.get()
            for k in list_of_removed:
                k.__del__()
                logger.info("nk3 instance removed")
                self.toggle_update_btn()
                self.info_frame.set_text("Nitrokey 3 removed.")

    def show_only_this_tabs(self, *args: int) -> None:
        for idx in range(self.tabs.count()):
            self.tabs.setTabEnabled(idx, False)
            self.tabs.setTabVisible(idx, False)
        for i in args:
            self.tabs.setTabEnabled(i, True)
            self.tabs.setTabVisible(i, True)

    def init_gui(self) -> None:
        self.show_only_this_tabs(0, 1)
        self.info_frame.hide()
        self.nitrokey3_frame.hide()
        self.progressbarupdate.hide()
        self.progressbardownload.hide()
        self.progressbarfinalization.hide()
        self.lock_btn.setEnabled(False)
        self.settings_btn.setEnabled(False)
        self.detect_nk3()

    @pyqtSlot(int)
    def slot_tab_changed(self, idx: int) -> None:
        pass

    # main-window callbacks
    @pyqtSlot()
    def about_button_pressed(self) -> None:
        self.about_dialog.exec_()

    @pyqtSlot()
    def slot_lock_button_pressed(self) -> None:
        # removes side buttos for nk3 (for now)
        logger.info("nk3 instance removed (lock button)")
        for x in Nk3Button.get():
            x.__del__()
