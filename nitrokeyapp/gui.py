import logging
import signal
import webbrowser
from types import FrameType, TracebackType

from nitrokey import _VID_NITROKEY
from nitrokey.trussed import Model
from PySide6 import QtWidgets
from PySide6.QtCore import QEvent, Qt, QThread, QTimer, Signal, Slot
from PySide6.QtGui import QCursor
from usbmonitor import USBMonitor
from usbmonitor.attributes import ID_USB_INTERFACES, ID_VENDOR_ID

from nitrokeyapp.device_data import DeviceData
from nitrokeyapp.device_view import DeviceView
from nitrokeyapp.device_worker import DeviceWorker
from nitrokeyapp.error_dialog import ErrorDialog
from nitrokeyapp.fido2_tab import Fido2Tab
from nitrokeyapp.information_box import InfoBox
from nitrokeyapp.nk3_button import Nk3Button
from nitrokeyapp.overview_tab import OverviewTab
from nitrokeyapp.progress_box import ProgressBox
from nitrokeyapp.prompt_box import PromptBox
from nitrokeyapp.qt_utils_mix_in import QtUtilsMixIn
from nitrokeyapp.secrets_tab import SecretsTab
from nitrokeyapp.settings_tab import SettingsTab
from nitrokeyapp.touch import TouchIndicator
from nitrokeyapp.utils import check_ccid_config, should_use_ccid

# import wizards and stuff
from nitrokeyapp.welcome_tab import WelcomeTab

logger = logging.getLogger(__name__)

PASSKEYS_TAB_INDEX = 2
PASSKEYS_ADMIN_REQUIRED_MESSAGE = (
    "Managing passkeys requires administrator privileges on Windows. "
    "Please restart the Nitrokey App as administrator to list or delete passkeys."
)

UPDATE_IN_PROGRESS_MESSAGE = (
    "A firmware update is in progress. Please wait until it has finished "
    "before closing the application."
)

SIGNAL_WAKEUP_INTERVAL_MS = 200


class GUI(QtUtilsMixIn, QtWidgets.QMainWindow):
    trigger_handle_exception = Signal(object, BaseException, object)

    trigger_add_devices = Signal()
    trigger_remove_devices = Signal()
    trigger_refresh_devices = Signal()

    def __init__(self, qt_app: QtWidgets.QApplication, log_file: str):
        QtWidgets.QMainWindow.__init__(self)
        QtUtilsMixIn.__init__(self)

        self.device_worker_thread = QThread()
        self.device_worker = DeviceWorker()
        self.device_worker.moveToThread(self.device_worker_thread)
        self.device_worker_thread.start()

        self.trigger_add_devices.connect(self.device_worker.detect_added_devices)
        self.trigger_remove_devices.connect(self.device_worker.detect_removed_devices)
        self.trigger_refresh_devices.connect(self.device_worker.refresh_devices)
        self.device_worker.devices_updated.connect(self.update_devices)

        # start monitoring usb
        # usb-monitor uses different formats for the VID depending on the operating system, see:
        # - https://github.com/Eric-Canas/USBMonitor/issues/10
        # - https://github.com/Eric-Canas/USBMonitor/issues/12
        nk_vid = f"{_VID_NITROKEY:04x}"
        device_filter = (
            {ID_VENDOR_ID: nk_vid.upper()},
            {ID_VENDOR_ID: nk_vid.lower()},
            {ID_VENDOR_ID: f"0x{nk_vid.upper()}"},
            {ID_VENDOR_ID: f"0x{nk_vid.lower()}"},
            {ID_VENDOR_ID: str(_VID_NITROKEY)},
        )
        self.usb_monitor = USBMonitor(filter_devices=device_filter)
        self.usb_monitor.start_monitoring(
            on_connect=self.on_device_connect, on_disconnect=self.on_device_disconnect
        )

        self.devices: list[DeviceData] = []
        self.device_buttons: list[Nk3Button] = []
        self.selected_device: DeviceData | None = None

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
        self.fido2_tab = Fido2Tab(self)
        self.settings_tab = SettingsTab(self)

        self.views: list[DeviceView] = [
            self.overview_tab,
            self.secrets_tab,
            self.fido2_tab,
            self.settings_tab,
        ]

        self.settings_tab._worker.reset_passwords.connect(self.secrets_tab.invalidate)
        self.busy_count = 0
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

        # On Windows without admin rights, CTAPHID is unavailable so the
        # passkeys tab cannot list/delete credentials — keep it disabled and
        # surface the reason via tooltip on hover.
        self.passkeys_admin_required = should_use_ccid()
        if self.passkeys_admin_required:
            self.tabs.setTabToolTip(PASSKEYS_TAB_INDEX, PASSKEYS_ADMIN_REQUIRED_MESSAGE)

        # set some spacing between Nitrokey buttons
        self.ui.nitrokeyButtonsLayout.setSpacing(8)

        self.help_btn.clicked.connect(
            lambda: webbrowser.open("https://docs.nitrokey.com/nitrokeys/nitrokey3/")
        )
        self.home_button.clicked.connect(self.home_button_pressed)

        self.init_gui()
        self.show()

        self.setup_signal_handling()

        check_ccid_config(self)

    def setup_signal_handling(self) -> None:
        """Install a custom SIGINT handler for a clean shutdown.

        Python cannot run signal handlers while the Qt event loop is
        blocking, so a timer regularly hands control back to the interpreter
        to let pending signals be delivered.
        """
        signal.signal(signal.SIGINT, self.handle_sigint)

        self.signal_wakeup_timer = QTimer(self)
        self.signal_wakeup_timer.timeout.connect(lambda: None)
        self.signal_wakeup_timer.start(SIGNAL_WAKEUP_INTERVAL_MS)

    def is_update_running(self) -> bool:
        """Whether a firmware update is currently being executed.

        Interrupting an update may brick the device, so this is used to block
        both signal-triggered and regular application exits.
        """
        return any(device.updating for device in self.device_manager)

    def handle_sigint(self, sig: int, frame: FrameType | None) -> None:
        if self.is_update_running():
            logger.warning("Ignoring SIGINT: a firmware update is in progress")
            self.info_box.set_error_status(UPDATE_IN_PROGRESS_MESSAGE)
            return

        logger.info("Received SIGINT, closing application")
        self.close()

    def toggle_update_btn(self) -> None:
        device_count = len(self.devices)
        if device_count == 0:
            self.l_insert_nitrokey.show()
        self.overview_tab.set_update_enabled(device_count <= 1)

    def on_device_connect(
        self, device_id: str | None = None, device_info: dict[str, str] | None = None
    ) -> None:
        interfaces = device_info.get(ID_USB_INTERFACES, ()) if device_info else ()
        ccid_classes = ("0b0000", "class_0b", "0x0b", "IOUSBHostFamily.kext")
        hid_classes = ("030000", "class_03", "0x03", "IOUSBHostFamily.kext")

        filter_success = False
        filter_class = ccid_classes if should_use_ccid() else hid_classes

        for interface in interfaces:
            if filter_success:
                break
            for f in filter_class:
                if f in interface.lower():
                    filter_success = True
                    break

        if not filter_success and interfaces:
            return

        self.trigger_add_devices.emit()

    def on_device_disconnect(
        self, device_id: str | None = None, device_info: dict[str, str] | None = None
    ) -> None:
        self.trigger_remove_devices.emit()

    @Slot()
    def refresh_devices(self) -> None:
        self.hide_device()
        self.trigger_refresh_devices.emit()

    @Slot(list)
    def update_devices(self, devices: list[DeviceData]) -> None:
        self.devices = devices

        self.hide_device()
        self.selected_device = None

        for widget in self.device_buttons:
            widget.setParent(None)  # type: ignore [call-overload]
            widget.destroy()
        self.device_buttons.clear()

        for device_data in self.devices:
            btn = Nk3Button(device_data, self.show_device)
            self.device_buttons.append(btn)
            self.ui.nitrokeyButtonsLayout.addWidget(btn)

            if not self.selected_device:
                self.selected_device = device_data

        if len(self.devices) > 0:
            self.l_insert_nitrokey.hide()
            self.hide_navigation()
            if self.selected_device:
                self.show_device(self.selected_device)
            self.toggle_update_btn()
        else:
            self.l_insert_nitrokey.show()

    def init_gui(self) -> None:
        self.hide_device()
        self.trigger_add_devices.emit()

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
            self.tabs.setTabVisible(1, True)
            self.tabs.setTabEnabled(1, False)
            self.tabs.setTabVisible(2, True)
            self.tabs.setTabEnabled(2, False)
            self.tabs.setTabEnabled(3, False)
        else:
            is_nk3 = self.selected_device.model == Model.NK3
            has_fido2 = self.selected_device.model in (Model.NK3, Model.NKPK)
            self.tabs.setTabVisible(1, is_nk3)
            self.tabs.setTabEnabled(1, is_nk3)
            self.tabs.setTabVisible(2, has_fido2)
            self.tabs.setTabEnabled(2, has_fido2 and not self.passkeys_admin_required)
            self.tabs.setTabEnabled(3, True)

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
        if self.selected_device is not None:
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

    @Slot()
    def set_busy_after_delay(self) -> None:
        if self.busy_count == 0:
            return

        self.setCursor(QCursor(Qt.CursorShape.WaitCursor))
        self.home_button.setEnabled(False)
        self.tabs.setEnabled(False)

    @Slot(bool)
    def set_busy(self, busy: bool) -> None:
        if busy:
            self.busy_count = self.busy_count + 1
            QTimer.singleShot(100, self.set_busy_after_delay)
        else:
            self.busy_count = self.busy_count - 1

        if self.busy_count == 0:
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
        self, ty: type[BaseException], e: BaseException, tb: TracebackType | None
    ) -> None:
        logger.error("Unhandled exception", exc_info=(ty, e, tb))

        dialog = ErrorDialog(self.log_file, self)
        dialog.set_exception(ty, e, tb)

    def closeEvent(self, event: QEvent) -> None:
        if self.is_update_running():
            logger.warning("Ignoring close request: a firmware update is in progress")
            self.info_box.set_error_status(UPDATE_IN_PROGRESS_MESSAGE)
            event.ignore()
            return

        self.usb_monitor.stop_monitoring()
        self.device_worker_thread.quit()
        self.device_worker_thread.wait(3000)
        self.overview_tab.worker_thread.quit()
        self.settings_tab.worker_thread.quit()
        self.secrets_tab.worker_thread.quit()
        self.fido2_tab.worker_thread.quit()
        event.accept()
