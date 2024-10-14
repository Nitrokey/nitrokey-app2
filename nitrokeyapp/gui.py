import logging
import webbrowser
from time import sleep
from types import TracebackType
from typing import Dict, Optional, Type

from PySide6 import QtWidgets
from PySide6.QtCore import QEvent, Qt, Signal, Slot
from PySide6.QtGui import QCursor
from usbmonitor import USBMonitor

from nitrokeyapp.device_data import DeviceData
from nitrokeyapp.device_manager import DeviceManager
from nitrokeyapp.device_view import DeviceView
from nitrokeyapp.error_dialog import ErrorDialog
from nitrokeyapp.information_box import InfoBox
from nitrokeyapp.nk3_button import Nk3Button
from nitrokeyapp.overview_tab import OverviewTab
from nitrokeyapp.progress_box import ProgressBox
from nitrokeyapp.prompt_box import PromptBox
from nitrokeyapp.qt_utils_mix_in import QtUtilsMixIn
from nitrokeyapp.secrets_tab import SecretsTab
from nitrokeyapp.settings_tab import SettingsTab
from nitrokeyapp.touch import TouchIndicator

# import wizards and stuff
from nitrokeyapp.welcome_tab import WelcomeTab

logger = logging.getLogger(__name__)


class GUI(QtUtilsMixIn, QtWidgets.QMainWindow):
    trigger_handle_exception = Signal(object, BaseException, object)
    trigger_add_device = Signal(DeviceData)
    trigger_remove_device = Signal(DeviceData)

    def __init__(self, qt_app: QtWidgets.QApplication, log_file: str):
        QtWidgets.QMainWindow.__init__(self)
        QtUtilsMixIn.__init__(self)

        # start monitoring usb
        monitor = USBMonitor()
        monitor.start_monitoring(
            on_connect=self.detect_added_devices,
            on_disconnect=self.detect_removed_devices,
        )
        self.trigger_add_device.connect(self.add_device)
        self.trigger_remove_device.connect(self.remove_device)

        # self.devices: list[DeviceData] = []
        self.device_manager = DeviceManager()
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

        self.prompt_box = PromptBox(self)

        self.progress_box = ProgressBox(self.ui.progress_bar)

        self.welcome_widget = WelcomeTab(self.log_file, self)

        # hint for mypy
        self.content = self.ui.content
        self.content.layout().addWidget(self.welcome_widget)

        self.touch_dialog = TouchIndicator(self.info_box, self)

        self.overview_tab = OverviewTab(self)
        self.secrets_tab = SecretsTab(self)
        self.settings_tab = SettingsTab(self)

        self.views: list[DeviceView] = [
            self.overview_tab,
            self.secrets_tab,
            self.settings_tab,
        ]
        for view in self.views:
            if view.worker:

                view.worker.busy_state_changed.connect(self.set_busy)

                view.common_ui.touch.start.connect(self.touch_dialog.start)
                view.common_ui.touch.stop.connect(self.touch_dialog.stop)

                view.common_ui.info.info.connect(self.info_box.set_status)
                view.common_ui.info.error.connect(
                    self.info_box.set_error_status
                )
                view.common_ui.info.pin_cached.connect(
                    self.info_box.set_pin_icon
                )
                view.common_ui.info.pin_cleared.connect(
                    self.info_box.unset_pin_icon
                )
                self.info_box.pin_pressed.connect(
                    view.common_ui.info.pin_pressed
                )

                view.common_ui.prompt.confirm.connect(self.prompt_box.confirm)
                self.prompt_box.confirmed.connect(
                    view.common_ui.prompt.confirmed
                )

                view.common_ui.progress.start.connect(self.progress_box.show)
                view.common_ui.progress.stop.connect(self.progress_box.hide)
                view.common_ui.progress.progress.connect(
                    self.progress_box.update
                )

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
        self.tabs.currentChanged.connect(self.tab_changed)

        # set some spacing between Nitrokey buttons
        self.ui.nitrokeyButtonsLayout.setSpacing(8)

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

    def toggle_update_btn(self) -> None:
        device_count = self.device_manager.count()
        if device_count == 0:
            self.l_insert_nitrokey.show()
        self.overview_tab.set_update_enabled(device_count <= 1)

    def detect_added_devices(
        self,
        device_id: Optional[str] = None,
        device_info: Optional[Dict[str, str]] = None,
    ) -> None:
        # retry for up to 2secs
        for tries in range(8):
            devs = self.device_manager.add()
            if devs:
                break
            sleep(0.25)

        # show device as the connection might been updated
        if len(devs) == 0 and self.selected_device:
            self.show_device(self.selected_device)

        if not devs:
            logger.info("failed adding device")
            return

        # add as nk3 device
        logger.info(f"nk3 connected: {devs}")

        for dev in devs:
            self.trigger_add_device.emit(dev)

    def detect_removed_devices(
        self,
        device_id: Optional[str] = None,
        device_info: Optional[Dict[str, str]] = None,
    ) -> None:
        devs = self.device_manager.remove()
        if not devs:
            logger.info("failed removing device")
            return

        logger.info(f"nk3 disconnected: {devs}")
        for dev in devs:
            self.trigger_remove_device.emit(dev)

    @Slot(DeviceData)
    def add_device(self, data: DeviceData) -> None:
        self.toggle_update_btn()

        desc = str(data.uuid) if not data.is_bootloader else "NK3 (BL)"
        self.info_box.set_status(f"Nitrokey 3 added: {desc}")

        button = Nk3Button(data)
        button.clicked.connect(lambda: self.show_device(data))
        self.ui.nitrokeyButtonsLayout.addWidget(button)
        self.device_buttons.append(button)

        if not self.selected_device:
            self.selected_device = data

        self.l_insert_nitrokey.hide()

    @Slot(DeviceData)
    def remove_device(self, data: DeviceData) -> None:
        self.toggle_update_btn()
        if self.selected_device == data:
            self.selected_device = None
            self.hide_device()

        desc = str(data.uuid) if not data.is_bootloader else "NK3 (BL)"

        self.info_box.set_status(f"Nitrokey 3 removed: {desc}")

        def remove_button(btn: Nk3Button) -> None:
            self.ui.nitrokeyButtonsLayout.removeWidget(button)
            self.device_buttons.remove(button)
            button.destroy()

        for button in self.device_buttons:
            if button.data.is_bootloader:
                if button.data.path == data.path:
                    remove_button(button)
            elif button.data.uuid == data.uuid:
                remove_button(button)

        if self.device_manager.count() == 0:
            self.l_insert_nitrokey.show()

    def init_gui(self) -> None:
        self.hide_device()
        self.detect_added_devices()
        device_count = self.device_manager.count()
        if device_count == 1:
            data = self.device_manager._devices[0]
            self.show_device(data)

        self.overview_tab.busy_state_changed.connect(self.set_busy)

    def show_navigation(self) -> None:
        for btn in self.device_buttons:
            btn.fold()

        self.ui.vertical_navigation.setMinimumWidth(80)
        self.ui.vertical_navigation.setMaximumWidth(80)
        self.ui.btn_dial_help.hide()

        self.ui.main_logo.setMaximumWidth(48)
        self.ui.main_logo.setMaximumHeight(48)
        self.ui.main_logo.setMinimumWidth(48)
        self.ui.main_logo.setMinimumHeight(48)

    def hide_navigation(self) -> None:
        for btn in self.device_buttons:
            btn.unfold()

        self.ui.vertical_navigation.setMinimumWidth(200)
        self.ui.vertical_navigation.setMaximumWidth(200)
        self.ui.btn_dial_help.show()

        self.ui.main_logo.setMaximumWidth(120)
        self.ui.main_logo.setMaximumHeight(120)
        self.ui.main_logo.setMinimumWidth(64)
        self.ui.main_logo.setMinimumHeight(64)

    def show_device(self, data: DeviceData) -> None:
        self.selected_device = data
        for btn in self.device_buttons:
            if btn.data == data:
                btn.setChecked(True)
            else:
                btn.setChecked(False)

        self.info_box.set_device(data.name)
        self.tabs.show()
        self.tabs.setCurrentIndex(0)

        if self.selected_device.is_too_old:
            self.tabs.setTabEnabled(1, False)
            self.tabs.setTabEnabled(2, False)
        else:
            self.tabs.setTabEnabled(1, True)
            self.tabs.setTabEnabled(2, True)

        self.show_navigation()
        self.welcome_widget.hide()

        # enforce refreshing the current view
        view = self.views[self.tabs.currentIndex()]
        view.refresh(data, force=True)

    def hide_device(self) -> None:
        self.selected_device = None

        self.info_box.hide_device()
        self.tabs.hide()
        self.hide_navigation()
        self.welcome_widget.show()

    @Slot(int)
    def tab_changed(self, idx: int) -> None:
        view = self.views[self.tabs.currentIndex()]
        view.refresh(self.selected_device)

        if idx == 1:
            self.info_box.pin_icon.show()
        else:
            self.info_box.pin_icon.hide()

    # main-window callbacks
    @Slot()
    def home_button_pressed(self) -> None:
        self.hide_device()

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

    # error & exception handling
    @Slot(str, Exception)
    def handle_error(self, sender: str, exc: Exception) -> None:
        msg = f"{sender} - {exc}"
        self.info_box.set_error_status(msg)
        # self.user_err(msg, "Error", self)

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

    def closeEvent(self, event: QEvent) -> None:
        self.overview_tab.worker_thread.quit()
        self.settings_tab.worker_thread.quit()
        self.secrets_tab.worker_thread.quit()
        event.accept()
