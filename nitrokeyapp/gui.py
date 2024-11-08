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
    trigger_update_devices = Signal()
    trigger_refresh_devices = Signal()

    def __init__(self, qt_app: QtWidgets.QApplication, log_file: str):
        QtWidgets.QMainWindow.__init__(self)
        QtUtilsMixIn.__init__(self)

        # start monitoring usb
        monitor = USBMonitor()
        monitor.start_monitoring(
            on_connect=self.detect_added_devices,
            on_disconnect=self.detect_removed_devices,
        )

        self.trigger_update_devices.connect(self.update_devices)

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
                view.common_ui.info.error.connect(self.info_box.set_error_status)
                view.common_ui.info.pin_cached.connect(self.info_box.set_pin_icon)
                view.common_ui.info.pin_cleared.connect(self.info_box.unset_pin_icon)
                self.info_box.pin_pressed.connect(view.common_ui.info.pin_pressed)

                view.common_ui.prompt.confirm.connect(self.prompt_box.confirm)
                self.prompt_box.confirmed.connect(view.common_ui.prompt.confirmed)

                view.common_ui.progress.start.connect(self.progress_box.show)
                view.common_ui.progress.stop.connect(self.progress_box.hide)
                view.common_ui.progress.progress.connect(self.progress_box.update)

                view.common_ui.gui.refresh_devices.connect(self.refresh_devices)

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

    def toggle_update_btn(self) -> None:
        device_count = len(self.device_manager)
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

        if not devs:
            logger.info("failed adding device")
            return

        # add as nk3 device
        logger.info(f"nk3 connected: {devs}")

        self.trigger_update_devices.emit()

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
        self.trigger_update_devices.emit()

    @Slot()
    def refresh_devices(self) -> None:
        """clear `self.device_manager` and fully refresh devices"""
        self.selected_device = None
        self.device_manager.clear()

        self.detect_added_devices()

    @Slot()
    def update_devices(self) -> None:
        """update device button view based on `self.device_manager` contents"""

        # always clear right view on update_devices
        self.hide_device()
        self.selected_device = None

        for widget in self.device_buttons:
            widget.setParent(None)  # type: ignore [call-overload]
            widget.destroy()
        self.device_buttons.clear()

        for device_data in self.device_manager:
            btn = Nk3Button(device_data, self.show_device)
            self.device_buttons.append(btn)
            self.ui.nitrokeyButtonsLayout.addWidget(btn)

            if not self.selected_device:
                self.selected_device = device_data

        if len(self.device_manager) > 0:
            self.l_insert_nitrokey.hide()
            self.hide_navigation()
            if self.selected_device:
                self.show_device(self.selected_device)
            self.toggle_update_btn()
        else:
            self.l_insert_nitrokey.show()

    def init_gui(self) -> None:
        self.hide_device()
        self.detect_added_devices()

    def show_navigation(self) -> None:
        for btn in self.device_buttons:
            btn.fold()

        self.ui.vertical_navigation.setMinimumWidth(80)
        self.ui.vertical_navigation.setMaximumWidth(80)
        self.ui.btn_dial_help.hide()

        self.ui.main_logo.setFixedWidth(64)
        self.ui.main_logo.setFixedHeight(64)
        self.ui.main_logo.setContentsMargins(0, 0, 0, 0)

    def hide_navigation(self) -> None:
        for btn in self.device_buttons:
            btn.unfold()

        self.ui.vertical_navigation.setMinimumWidth(200)
        self.ui.vertical_navigation.setMaximumWidth(200)
        self.ui.btn_dial_help.show()

        self.ui.main_logo.setFixedWidth(190)
        self.ui.main_logo.setFixedHeight(200)
        self.ui.main_logo.setContentsMargins(30, 40, 40, 40)

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

        for btn in self.device_buttons:
            btn.set_stylesheet_small()

    def hide_device(self) -> None:
        self.selected_device = None

        self.info_box.hide_device()
        self.tabs.hide()
        self.hide_navigation()
        self.welcome_widget.show()

        for btn in self.device_buttons:
            btn.set_stylesheet_big()

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
