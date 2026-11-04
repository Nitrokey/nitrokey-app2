import logging
import shutil

from fido2.client import DefaultClientDataCollector, Fido2Client
from nitrokey.trussed import Transport, TrussedDevice, recommended_transport
from nitrokey.trussed._connection.ctaphid import CtapHidConnection
from nitrokey.trussed.admin_app import InitStatus
from PySide6.QtCore import QThread, Signal, Slot
from PySide6.QtWidgets import QFileDialog, QWidget

from nitrokeyapp.common_ui import CommonUi
from nitrokeyapp.device_data import DeviceData
from nitrokeyapp.qt_utils_mix_in import QtUtilsMixIn
from nitrokeyapp.update import UpdateResult, UpdateStatus
from nitrokeyapp.utils import get_transport, instantiate_device_on_new_channel_hid
from nitrokeyapp.worker import Worker

from .worker import OverviewWorker

logger = logging.getLogger(__name__)


class OverviewTab(QtUtilsMixIn, QWidget):
    # standard UI
    busy_state_changed = Signal(bool)

    # worker triggers
    trigger_update = Signal(DeviceData, bool)
    trigger_update_file = Signal(DeviceData, str, bool)
    trigger_check_genuine = Signal(DeviceData)

    def __init__(self, parent: QWidget | None = None) -> None:
        QWidget.__init__(self, parent)
        QtUtilsMixIn.__init__(self)

        self.data: DeviceData | None = None
        self.common_ui = CommonUi()

        self.worker_thread = QThread()
        self._worker = OverviewWorker(self.common_ui)
        self._worker.moveToThread(self.worker_thread)
        self.worker_thread.start()

        self.trigger_update.connect(self._worker.update_device)
        self.trigger_update_file.connect(self._worker.update_device_file)
        self.trigger_check_genuine.connect(self._worker.check_genuine)

        self._worker.device_updated.connect(self.device_updated)
        self._worker.genuine_device.connect(self.genuine_result)

        # self.ui === self -> this tricks mypy due to monkey-patching self
        self.ui = self.load_ui("overview_tab.ui", self)

        self.is_qubesos = shutil.which("qubesdb-read") is not None

        self.ui.btn_update_with_file.clicked.connect(self.update_with_file)
        self.ui.btn_update.clicked.connect(self.run_update)
        self.ui.btn_check_genuine.clicked.connect(self.check_genuine)

        self.using_ccid = get_transport() == Transport.CCID

        self.reset()

    @property
    def title(self) -> str:
        return "Overview"

    @property
    def widget(self) -> QWidget:
        return self

    @property
    def worker(self) -> Worker | None:
        return self._worker

    def reset(self) -> None:
        self.data = None
        self.set_device_data("?", "?", "?", "?", "?")

    def refresh(self, data: DeviceData, force: bool = False) -> None:
        if data == self.data and not force:
            return
        self.reset()
        self.data = data
        self.ui.btn_check_genuine.setStyleSheet("")
        self.ui.btn_check_genuine.setText("Check for Authenticity")
        self.ui.btn_check_genuine.setToolTip(
            "Verify the authenticity of the device with attestation certificates"
        )

        # catch too old firmware
        if data.is_too_old:
            self.set_device_data(
                str(data.path), "n/a", "n/a", "Update Your Nitrokey 3 for full functionality", "n/a"
            )
            self.ui.status_label.hide()
            self.ui.nk3_status.hide()
            self.ui.more_info.hide()
            self.ui.nk3_label.setText("Nitrokey 3 (old firmware)")
            self.status_error(InitStatus(0))
            return

        if data.is_bootloader:
            self.set_device_data(str(data.path), "n/a", "n/a", "n/a", "n/a")
            self.ui.status_label.hide()
            self.ui.nk3_status.hide()
            self.ui.more_info.hide()
            self.ui.nk3_label.setText(f"{data.model} Bootloader")
            self.status_error(InitStatus(0))

        else:
            assert data.status.variant
            self.set_device_data(
                str(data.path),
                str(data.uuid),
                str(data.version),
                str(data.status.variant.name),
                str(data.status.init_status),
            )
            self.ui.nk3_label.setText(str(data.model))
            if data.status.init_status is None:
                self.ui.status_label.hide()
                self.ui.nk3_status.hide()
            else:
                self.status_error(InitStatus(data.status.init_status))
                self.ui.status_label.show()
                self.ui.nk3_status.show()

        transport = get_transport()
        if transport == Transport.CTAPHID:
            self.data = instantiate_device_on_new_channel_hid(self.data)
            assert isinstance(self.data._device, TrussedDevice)
            assert isinstance(self.data._device.connection, CtapHidConnection)
            fido2_client = Fido2Client(
                device=self.data._device.connection.device,
                client_data_collector=DefaultClientDataCollector(origin="https://example.com"),
            )
            if not (fido2_client._backend.info.options.get("makeCredUvNotRqd", False)):
                self.ui.btn_check_genuine().setEnabled(False)
                self.ui.btn_check_genuine.setToolTip("Please update firmware to continue")

        if (
            transport == Transport.CCID and recommended_transport() != Transport.CCID
        ):  # recommended_transport() checks whether its CCID because its on unpriviledged Windows. Checking for not CCID here means checking whether CCID is forced on other OS
            self.ui.btn_check_genuine().setEnabled(False)
            self.ui.btn_check_genuine.setToolTip("Unable to communicate for FIDO commands")

    def set_device_data(
        self, path: str, uuid: str, version: str, variant: str, init_status: str
    ) -> None:
        self.ui.nk3_path.setText(path.replace("{", "\n{"))
        self.ui.nk3_uuid.setText(uuid)
        self.ui.nk3_version.setText(version)
        self.ui.nk3_variant.setText(variant)
        self.ui.nk3_status.setText(init_status)

    def status_error(self, init: InitStatus) -> None:
        if init.is_error():
            self.ui.icon_warn_notice.show()
            self.ui.more_info.show()
        else:
            self.ui.icon_warn_notice.hide()
            self.ui.more_info.hide()

    def set_update_enabled(self, enabled: bool) -> None:
        tooltip = ""
        btn_really_enabled = enabled and not self.using_ccid
        if enabled and self.using_ccid:
            self.common_ui.info.info.emit(
                "Please restart the application as an administrator to be able to update"
            )
            tooltip = "Please restart the application as an administrator to be able to update"

        if not enabled:
            self.common_ui.info.info.emit(
                "Please remove all Nitrokey devices except the one you want to update."
            )
            tooltip = "Please remove all Nitrokey devices except the one you want to update."

        for btn in [self.ui.btn_update, self.ui.btn_update_with_file]:
            btn.setEnabled(btn_really_enabled)
            btn.setToolTip(tooltip)

    def update_btns_during_update(self, enabled: bool) -> None:
        tooltip = "" if enabled else "Update is already running. Please wait."
        self.busy_state_changed.emit(not enabled)
        for btn in [self.ui.btn_update, self.ui.btn_update_with_file]:
            btn.setEnabled(enabled)
            btn.setToolTip(tooltip)

    @Slot()
    def run_update(self) -> None:
        assert self.data
        # self.data.update(self, self.info_box)
        self.update_btns_during_update(False)

        self.trigger_update.emit(self.data, self.is_qubesos)

    @Slot(UpdateResult)
    def device_updated(self, result: UpdateResult) -> None:
        self.update_btns_during_update(True)

        msg = ""
        if result.message is not None:
            msg = ": " + result.message

        if result.status == UpdateStatus.SUCCESS:
            self.common_ui.info.info.emit(f"{result.model} successfully updated{msg}")
        elif result.status == UpdateStatus.ERROR:
            self.common_ui.info.error.emit(f"{result.model} update failed{msg}")
        elif result.status == UpdateStatus.ABORTED:
            self.common_ui.info.error.emit(f"{result.model} update aborted{msg}")
        else:
            self.common_ui.info.error.emit(f"Unexpected update result: {result.status}{msg}")

        self.common_ui.gui.refresh_devices.emit()

    @Slot()
    def update_with_file(self) -> None:
        assert self.data
        fdialog = QFileDialog()
        fdialog.setFileMode(QFileDialog.FileMode.AnyFile)

        if fdialog.exec_():
            filenames = fdialog.selectedFiles()
            file = filenames[0]

            self.trigger_update_file.emit(self.data, file, self.is_qubesos)

    @Slot()
    def check_genuine(self) -> None:
        assert self.data
        self.trigger_check_genuine.emit(self.data)

    @Slot(bool, str)
    def genuine_result(self, result_val: bool, result_reason: str) -> None:
        result_button = self.ui.btn_check_genuine
        if result_val:
            result_button.setText("Verified Genuine")
            result_button.setStyleSheet(
                "QPushButton {"
                "background-color: rgba(115, 215, 125, 0.18);"
                "border: 1px solid rgba(115, 215, 125, 0.5);"
                "border-radius: 6px; color: rgb(115, 215, 125); font-weight: 600;"
                "}"
            )
            logger.info("Authenticator verified")
        else:
            result_button.setText("Verification Failed")
            result_button.setStyleSheet(
                "QPushButton {"
                "background-color: rgba(192, 57, 43, 0.18);"
                "border: 1px solid rgba(192, 57, 43, 0.5);"
                "border-radius: 6px; color: #ff8070; font-weight: 600;"
                "}"
            )
            logger.warning("Authenticator verification failed")
            logger.warning(result_reason)

        result_button.setToolTip(result_reason)
