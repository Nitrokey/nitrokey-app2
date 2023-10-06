# use "pbs" for packaging...
# pip-run -> pyqt5
# pip-dev -> pyqt5-stubs
import functools
import logging
import platform
import webbrowser
from types import TracebackType
from typing import Optional, Type

# Nitrokey 3
from pynitrokey.nk3 import Nitrokey3Device

# pyqt5
from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt, pyqtSignal, pyqtSlot
from PyQt5.QtGui import QCursor

# from nitrokeyapp.about_dialog import AboutDialog
from nitrokeyapp.device_data import DeviceData
from nitrokeyapp.device_view import DeviceView
from nitrokeyapp.error_dialog import ErrorDialog
from nitrokeyapp.information_box import InfoBox
from nitrokeyapp.nk3_button import Nk3Button
from nitrokeyapp.overview_tab import OverviewTab

# from nitrokeyapp.loading_screen import LoadingScreen
from nitrokeyapp.qt_utils_mix_in import QtUtilsMixIn
from nitrokeyapp.secrets_tab import SecretsTab

# import wizards and stuff
from nitrokeyapp.ui.mainwindow import Ui_MainWindow
from nitrokeyapp.welcome_tab import WelcomeTab
from nitrokeyapp.windows_notification import WindowsUSBNotifi

logger = logging.getLogger(__name__)


class TouchDialog(QtWidgets.QMessageBox):
    def __init__(self, parent: QtWidgets.QWidget) -> None:
        super().__init__(parent)

        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.setWindowTitle("Touch Confirmation")
        self.setText("Press the button on the Nitrokey 3 if the LED blinks.")

    @pyqtSlot()
    def start(self) -> None:
        self.show()

    @pyqtSlot()
    def stop(self) -> None:
        self.close()


class GUI(QtUtilsMixIn, QtWidgets.QMainWindow):
    trigger_handle_exception = pyqtSignal(object, BaseException, object)

    def __init__(self, qt_app: QtWidgets.QApplication, log_file: str):
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
            WindowsUSBNotifi(self.detect_added_devices, self.detect_removed_devices)

        self.devices: list[DeviceData] = []
        self.device_buttons: list[Nk3Button] = []
        self.selected_device: Optional[DeviceData] = None
        self.log_file = log_file

        self.trigger_handle_exception.connect(self.handle_exception)

        # loads main ui
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.info_box = InfoBox(
            self.ui.information_frame,
            self.ui.label_information_icon,
            self.ui.label_information,
        )
        self.widgetTab = self.ui.widgetTab
        self.widgetTab = WelcomeTab(self.widgetTab, self.log_file)
        # self.about_dialog = AboutDialog(log_file, qt_app)
        self.touch_dialog = TouchDialog(self)
        self.overview_tab = OverviewTab(self.info_box, self)
        self.views: list[DeviceView] = [self.overview_tab, SecretsTab(self)]
        for view in self.views:
            if view.worker:
                view.worker.busy_state_changed.connect(self.set_busy)
                view.worker.error.connect(self.error)
                view.worker.start_touch.connect(self.touch_dialog.start)
                view.worker.stop_touch.connect(self.touch_dialog.stop)

        # get widget objects
        # app wide widgets
        # self.status_bar = _get(_qt.QStatusBar, "statusBar")
        # self.menu_bar = _get(_qt.QMenuBar, "menuBar")
        self.tabs = self.ui.tabWidget
        self.home_button = self.ui.btn_home
        self.help_btn = self.ui.btn_dial_help
        # self.quit_button = self.ui.btn_dial_quit
        self.settings_btn = self.ui.btn_settings
        self.lock_btn = self.ui.btn_dial_lock
        self.l_insert_nitrokey = self.ui.label_insert_Nitrokey
        # set some props, initial enabled/visible, finally show()
        self.setAttribute(Qt.WA_DeleteOnClose)

        for view in self.views:
            self.tabs.addTab(view.widget, view.title)
        self.tabs.currentChanged.connect(self.slot_tab_changed)

        self.init_gui()
        self.show()

        # nk3
        self.help_btn.clicked.connect(
            lambda: webbrowser.open("https://docs.nitrokey.com/nitrokey3")
        )
        self.lock_btn.clicked.connect(self.slot_lock_button_pressed)
        self.home_button.clicked.connect(self.home_button_pressed)
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
                self.detect_removed_devices()
            elif dvc.action == "bind":
                logger.info("BIND")
                self.detect_added_devices()

    @pyqtSlot(object, BaseException, object)
    def handle_exception(
        self,
        ty: Type[BaseException],
        e: BaseException,
        tb: Optional[TracebackType],
    ) -> None:
        logger.error("Unhandled exception", exc_info=(ty, e, tb))

        dialog = ErrorDialog(self.log_file, self)
        dialog.set_exception(ty, e, tb)
        dialog.show()

    def toggle_update_btn(self) -> None:
        device_count = len(self.devices)
        if device_count == 0:
            self.l_insert_nitrokey.show()
        self.overview_tab.set_update_enabled(device_count == 1)

    def detect_added_devices(self) -> None:
        nk3_list = Nitrokey3Device.list()
        if len(nk3_list):
            list_of_added = [device.uuid_prefix for device in self.devices]
            logger.info(f"list of added: {list_of_added}")
            for device in nk3_list:
                data = DeviceData(device)
                if data.uuid_prefix not in list_of_added:
                    if data.uuid:
                        logger.info(f"{data.path}: Nitrokey 3 {data.uuid}")
                    else:
                        logger.info(f"{data.path}: Nitrokey 3 without UUID")
                    self.add_device(data)
                    logger.info("nk3 connected")
                    self.l_insert_nitrokey.hide()
                    self.toggle_update_btn()
                else:
                    if (
                        self.selected_device
                        and self.selected_device.uuid_prefix == data.uuid_prefix
                        and self.selected_device.path != data.path
                    ):
                        self.selected_device = data
                        self.refresh()
        else:
            logger.info("no nk3 in list. no admin?")

    def detect_removed_devices(self) -> None:
        list_of_removed: list[DeviceData] = []
        if self.devices:
            nk3_list = [str(device.uuid())[:-4] for device in Nitrokey3Device.list()]
            logger.info(f"list nk3: {nk3_list}")
            list_of_removed = [
                data
                for data in self.devices
                if ((data.uuid_prefix not in nk3_list) and not data.updating)
            ]

        for data in list_of_removed:
            self.remove_device(data)

        if list_of_removed:
            logger.info("nk3 instance removed")
            self.toggle_update_btn()
            self.info_box.set_text("Nitrokey 3 removed.")

    def add_device(self, data: DeviceData) -> None:
        button = Nk3Button(data)
        button.clicked.connect(lambda: self.device_selected(data))
        self.ui.nitrokeyButtonsLayout.addWidget(button)
        self.devices.append(data)
        self.device_buttons.append(button)
        self.widget_show()

    def remove_device(self, data: DeviceData) -> None:
        if self.selected_device == data:
            self.selected_device = None
            self.refresh()

        for button in self.device_buttons:
            if button.data.uuid == data.uuid:
                self.ui.nitrokeyButtonsLayout.removeWidget(button)
                self.device_buttons.remove(button)
                button.close()

        self.devices.remove(data)
        self.widget_show()

    def refresh(self) -> None:
        """
        Should be called if the selected device or the selected tab is changed
        """
        if self.selected_device:
            self.widgetTab.hide()
            self.views[self.tabs.currentIndex()].refresh(self.selected_device)
            self.tabs.show()
        else:
            for view in self.views:
                view.reset()
            self.tabs.hide()

    def init_gui(self) -> None:
        self.tabs.hide()
        self.info_box.hide()
        self.lock_btn.setEnabled(False)
        self.settings_btn.setEnabled(False)
        self.detect_added_devices()

    def device_selected(self, data: DeviceData) -> None:
        self.selected_device = data
        self.refresh()

    def widget_show(self) -> None:
        device_count = len(self.devices)
        if device_count == 1:
            data = self.devices[0]
            self.device_selected(data)
        else:
            self.tabs.hide()
            self.widgetTab.show()

    @pyqtSlot(int)
    def slot_tab_changed(self, idx: int) -> None:
        self.refresh()

    # main-window callbacks
    @pyqtSlot()
    def home_button_pressed(self) -> None:
        self.widgetTab.show()
        self.tabs.hide()

    @pyqtSlot()
    def slot_lock_button_pressed(self) -> None:
        # removes side buttos for nk3 (for now)
        logger.info("nk3 instance removed (lock button)")
        for data in self.devices:
            self.remove_device(data)

    @pyqtSlot(bool)
    def set_busy(self, busy: bool) -> None:
        if busy:
            self.setCursor(QCursor(Qt.WaitCursor))
        else:
            self.unsetCursor()
        # TODO: setEnabled?
        # self.setEnabled(not busy)

    @pyqtSlot(str)
    def error(self, error: str) -> None:
        # TODO: improve
        self.user_err(error, "Error")
