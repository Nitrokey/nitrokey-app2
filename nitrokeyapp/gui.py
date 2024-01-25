import logging
import platform
import webbrowser
from types import TracebackType
from typing import Optional, Type

if platform.system() == "Linux":
    import pyudev

# Nitrokey 3
from pynitrokey.nk3 import Nitrokey3Device

# pyqt5
from PySide6 import QtWidgets
from PySide6.QtCore import Qt, QTimer, Signal, Slot
from PySide6.QtGui import QCursor

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
from nitrokeyapp.welcome_tab import WelcomeTab
from nitrokeyapp.windows_notification import WindowsUSBNotifi

logger = logging.getLogger(__name__)


class TouchDialog(QtWidgets.QMessageBox):
    def __init__(self, parent: QtWidgets.QWidget) -> None:
        super().__init__(parent)

        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.setWindowTitle("Touch Confirmation")
        self.setText("Press the button on the Nitrokey 3 if the LED blinks.")

    @Slot()
    def start(self) -> None:
        self.show()

    @Slot()
    def stop(self) -> None:
        self.close()


class TouchIndicator(QtWidgets.QWidget):
    def __init__(self, info_box: InfoBox, parent: "GUI") -> None:
        super().__init__(parent)

        # TODO: dont pass entire top-lvl obj
        self.owner = parent
        self.active_btn: Optional[Nk3Button] = None
        self.info_box = info_box

        # show status bar info 750ms late
        t = QTimer(self)
        t.setSingleShot(True)
        t.setInterval(750)
        t.timeout.connect(self.info_box.set_touch_status)
        self.info_box_timer: QTimer = t

    @Slot()
    def start(self) -> None:
        if self.active_btn:
            return

        self.info_box_timer.start()

        for btn in self.owner.device_buttons:
            if btn.data == self.owner.selected_device:
                self.active_btn = btn
                break
        if self.active_btn:
            self.active_btn.start_touch()

    @Slot()
    def stop(self) -> None:
        if self.active_btn:
            self.active_btn.stop_touch()
            self.active_btn = None

        # self.info_box.hide_status()
        if self.info_box_timer.isActive():
            self.info_box_timer.stop()
        self.info_box.hide_touch()


class GUI(QtUtilsMixIn, QtWidgets.QMainWindow):
    trigger_handle_exception = Signal(object, BaseException, object)
    sig_device_change = Signal(object)

    def __init__(self, qt_app: QtWidgets.QApplication, log_file: str):
        QtWidgets.QMainWindow.__init__(self)
        QtUtilsMixIn.__init__(self)

        # linux
        if platform.system() == "Linux":
            # start monitoring usb
            self.context = pyudev.Context()
            self.monitor = pyudev.Monitor.from_netlink(self.context)
            self.monitor.filter_by(subsystem="usb")
            # pyudev.pyside6 integration doesn't work properly
            self.observer = pyudev.MonitorObserver(
                self.monitor, lambda action, device: self.sig_device_change.emit(action)
            )
            self.observer.start()

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
        # self.ui === self -> this tricks mypy due to monkey-patching self
        self.ui = self.load_ui("mainwindow.ui", self)

        self.info_box = InfoBox(
            self.ui.information_frame,
            self.ui.status_icon,
            self.ui.status,
            self.ui.device_info,
            self.ui.pin_icon,
        )

        self.welcome_widget = WelcomeTab(self.log_file, self)

        # hint for mypy
        self.content = self.ui.content
        self.content.layout().addWidget(self.welcome_widget)

        # self.touch_dialog = TouchDialog(self)
        self.touch_dialog = TouchIndicator(self.info_box, self)

        self.overview_tab = OverviewTab(self.info_box, self)
        self.secrets_tab = SecretsTab(self.info_box, self)
        self.views: list[DeviceView] = [self.overview_tab, self.secrets_tab]
        for view in self.views:
            if view.worker:
                view.worker.busy_state_changed.connect(self.set_busy)
                view.worker.error.connect(self.handle_error)
                view.worker.start_touch.connect(self.touch_dialog.start)
                view.worker.stop_touch.connect(self.touch_dialog.stop)

        # main window widgets
        self.home_button = self.ui.btn_home
        self.help_btn = self.ui.btn_dial_help

        self.l_insert_nitrokey = self.ui.label_insert_Nitrokey

        # set some props, initial enabled/visible, finally show()
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)

        # hint for mypy
        self.tabs = self.ui.tabs
        for view in self.views:
            self.tabs.addTab(view.widget, view.title)
        self.tabs.currentChanged.connect(self.slot_tab_changed)

        # set some spacing between Nitrokey buttons
        self.ui.nitrokeyButtonsLayout.setSpacing(8)
        self.sig_device_change.connect(self.device_connect)

        self.help_btn.clicked.connect(
            lambda: webbrowser.open("https://docs.nitrokey.com/nitrokey3")
        )
        self.home_button.clicked.connect(self.home_button_pressed)

        self.init_gui()
        self.show()

    @Slot(object)
    def device_connect(self, action: str) -> None:
        if action == "remove":
            logger.info("device removed event")
            self.detect_removed_devices()

        elif action == "bind":
            logger.info("device bind event")
            self.detect_added_devices()

    @Slot(object, BaseException, object)
    def handle_exception(
        self,
        ty: Type[BaseException],
        e: BaseException,
        tb: Optional[TracebackType],
    ) -> None:
        logger.error("Unhandled exception", exc_info=(ty, e, tb))

        dialog = ErrorDialog(self.log_file, self)
        dialog.set_exception(ty, e, tb)

    def toggle_update_btn(self) -> None:
        device_count = len(self.devices)
        if device_count == 0:
            self.l_insert_nitrokey.show()
        self.overview_tab.set_update_enabled(device_count == 1)

    def detect_added_devices(self) -> None:
        try:
            nk3_list = Nitrokey3Device.list()
        except Exception as e:
            logger.info(repr(e))
            return

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
            try:
                nk3_list = [device.uuid() for device in Nitrokey3Device.list()]
            except Exception as e:
                logger.info(f"detect removed failed: {e}")
                return
            logger.info(f"list nk3: {nk3_list}")

            list_of_removed = [
                data
                for data in self.devices
                if ((data.uuid not in nk3_list) and not data.updating)
            ]

        for data in list_of_removed:
            self.remove_device(data)

        if list_of_removed:
            who = [d.uuid_prefix for d in list_of_removed]
            logger.info(f"nk3 instance(s) removed: {' '.join(who)}")
            self.info_box.set_status(f"Nitrokey 3 removed: {' '.join(who)}")
            self.toggle_update_btn()

    def add_device(self, data: DeviceData) -> None:
        button = Nk3Button(data)
        button.clicked.connect(lambda: self.device_selected(data))
        self.ui.nitrokeyButtonsLayout.addWidget(button)
        self.devices.append(data)
        self.device_buttons.append(button)
        if self.selected_device:
            button.fold()
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

    def refresh(self, set_busy: bool = True) -> None:
        """
        Should be called if the selected device or the selected tab is changed
        """
        if set_busy:
            self.overview_tab.busy_state_changed.connect(self.set_busy)

        if self.selected_device:
            self.welcome_widget.hide()
            self.info_box.set_device(f"Nitrokey 3 - {self.selected_device.uuid_prefix}")
            self.views[self.tabs.currentIndex()].refresh(self.selected_device)
            self.tabs.show()

            self.ui.vertical_navigation.setMinimumWidth(80)
            self.ui.vertical_navigation.setMaximumWidth(80)
            self.ui.btn_dial_help.hide()
            for btn in self.device_buttons:
                btn.fold()
            self.ui.main_logo.setMaximumWidth(48)
            self.ui.main_logo.setMaximumHeight(48)
            self.ui.main_logo.setMinimumWidth(48)
            self.ui.main_logo.setMinimumHeight(48)

        else:
            self.info_box.hide_device()
            for view in self.views:
                view.reset()
            self.tabs.hide()

            self.ui.vertical_navigation.setMinimumWidth(200)
            self.ui.btn_dial_help.show()
            for btn in self.device_buttons:
                btn.unfold()
            self.ui.main_logo.setMaximumWidth(120)
            self.ui.main_logo.setMaximumHeight(120)
            self.ui.main_logo.setMinimumWidth(64)
            self.ui.main_logo.setMinimumHeight(64)

    def init_gui(self) -> None:
        self.tabs.hide()
        self.detect_added_devices()

    def device_selected(self, data: DeviceData) -> None:
        self.selected_device = data
        self.info_box.set_device(f"Nitrokey 3 - {data.uuid_prefix}")
        self.refresh()

    def widget_show(self) -> None:
        device_count = len(self.devices)
        if device_count == 1:
            data = self.devices[0]
            self.device_selected(data)
            # TODO: solve centrally
            self.tabs.setCurrentIndex(0)
        else:
            self.tabs.hide()
            self.welcome_widget.show()
            self.selected_device = None
            self.info_box.hide_device()
            self.refresh(set_busy=False)

    @Slot(int)
    def slot_tab_changed(self, idx: int) -> None:
        # TODO: not a good place
        for view in self.views:
            view.reset()
        if idx == 0:
            self.info_box.pin_icon.hide()
        else:
            self.info_box.pin_icon.show()

        self.refresh()

    # main-window callbacks
    @Slot()
    def home_button_pressed(self) -> None:
        for view in self.views:
            view.reset()
        self.welcome_widget.show()
        self.tabs.hide()
        self.selected_device = None
        self.refresh()

    @Slot(bool)
    def set_busy(self, busy: bool) -> None:
        if busy:
            self.setCursor(QCursor(Qt.CursorShape.WaitCursor))
            self.home_button.setEnabled(False)
            self.tabs.setEnabled(False)
        else:
            self.unsetCursor()
            self.home_button.setEnabled(True)
            self.tabs.setEnabled(True)

        # TODO: setEnabled?
        # self.setEnabled(not busy)

    @Slot(str, Exception)
    def handle_error(self, sender: str, exc: Exception) -> None:
        msg = f"{sender} - {exc}"
        self.info_box.set_error_status(msg)
        # self.user_err(msg, "Error", self)
