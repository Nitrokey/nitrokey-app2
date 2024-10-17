import logging
import shutil
from typing import Optional

from nitrokey.trussed.admin_app import InitStatus
from PySide6.QtCore import QThread, Signal, Slot
from PySide6.QtWidgets import QFileDialog, QWidget

from nitrokeyapp.common_ui import CommonUi
from nitrokeyapp.device_data import DeviceData
from nitrokeyapp.qt_utils_mix_in import QtUtilsMixIn
from nitrokeyapp.worker import Worker

from .worker import OverviewWorker

logger = logging.getLogger(__name__)


class OverviewTab(QtUtilsMixIn, QWidget):
    # standard UI
    busy_state_changed = Signal(bool)

    # worker triggers
    trigger_update = Signal(DeviceData, bool)
    trigger_update_file = Signal(DeviceData, str, bool)

    def __init__(
        self,
        parent: Optional[QWidget] = None,
    ) -> None:
        QWidget.__init__(self, parent)
        QtUtilsMixIn.__init__(self)

        self.data: Optional[DeviceData] = None
        self.common_ui = CommonUi()

        self.worker_thread = QThread()
        self._worker = OverviewWorker(self.common_ui)
        self._worker.moveToThread(self.worker_thread)
        self.worker_thread.start()

        self.trigger_update.connect(self._worker.update_device)
        self.trigger_update_file.connect(self._worker.update_device_file)

        self._worker.device_updated.connect(self.device_updated)

        # self.ui === self -> this tricks mypy due to monkey-patching self
        self.ui = self.load_ui("overview_tab.ui", self)

        self.is_qubesos = shutil.which("qubesdb-read") is not None

        self.ui.btn_update_with_file.clicked.connect(self.update_with_file)
        self.ui.btn_more_options.clicked.connect(self.more_options)
        self.ui.btn_update.clicked.connect(self.run_update)

        self.reset()

    @property
    def title(self) -> str:
        return "Overview"

    @property
    def widget(self) -> QWidget:
        return self

    @property
    def worker(self) -> Optional[Worker]:
        return self._worker

    def reset(self) -> None:
        self.data = None
        self.set_device_data("?", "?", "?", "?", "?")

    def refresh(self, data: DeviceData, force: bool = False) -> None:
        if data == self.data and not force:
            return
        self.reset()
        self.data = data
        self.hide_more_options()

        # catch too old firmware
        if data.is_too_old:
            self.set_device_data(
                str(data.path),
                "n/a",
                "n/a",
                "Update Your Nitrokey 3 for full functionality",
                "n/a",
            )
            self.ui.status_label.hide()
            self.ui.nk3_status.hide()
            self.ui.more_info.hide()
            self.ui.nk3_label.setText("Nitrokey 3 (old firmware)")
            self.status_error(InitStatus(0))
            return

        if data.is_bootloader:
            self.set_device_data(
                str(data.path),
                "n/a",
                "n/a",
                "n/a",
                "n/a",
            )
            self.ui.status_label.hide()
            self.ui.nk3_status.hide()
            self.ui.more_info.hide()
            self.ui.nk3_label.setText("Nitrokey 3 Bootloader")
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
            self.ui.nk3_label.setText("Nitrokey 3")
            if data.status.init_status is None:
                self.ui.status_label.hide()
                self.ui.nk3_status.hide()
            else:
                self.status_error(InitStatus(data.status.init_status))
                self.ui.status_label.show()
                self.ui.nk3_status.show()

    def set_device_data(
        self,
        path: str,
        uuid: str,
        version: str,
        variant: str,
        init_status: str,
    ) -> None:
        self.ui.nk3_path.setText(path)
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
        if enabled:
            ...
        else:
            self.hide_more_options()
            self.common_ui.info.info.emit(
                "Please remove all Nitrokey 3 devices except the one you want to update."
            )
            tooltip = "Please remove all Nitrokey 3 devices except the one you want to update."

        self.ui.btn_update.setEnabled(enabled)
        self.ui.btn_update.setToolTip(tooltip)
        self.ui.btn_more_options.setEnabled(enabled)
        self.ui.btn_more_options.setToolTip(tooltip)

    def update_btns_during_update(self, enabled: bool) -> None:
        tooltip = ""
        if enabled:
            self.busy_state_changed.emit(False)
            self.ui.btn_update.setEnabled(enabled)
            self.ui.btn_update.setToolTip(tooltip)
            self.ui.btn_more_options.setEnabled(enabled)
            self.ui.btn_more_options.setToolTip(tooltip)
            self.ui.btn_update_with_file.setEnabled(enabled)
            self.ui.btn_update_with_file.setToolTip(tooltip)
        else:
            tooltip = "Update is already running. Please wait."
            self.busy_state_changed.emit(True)
            self.ui.btn_update.setEnabled(enabled)
            self.ui.btn_update.setToolTip(tooltip)
            self.ui.btn_more_options.setEnabled(enabled)
            self.ui.btn_more_options.setToolTip(tooltip)
            self.ui.btn_update_with_file.setEnabled(enabled)
            self.ui.btn_update_with_file.setToolTip(tooltip)

    def more_options(self) -> None:
        state = self.ui.btn_more_options.isChecked()
        if state:
            self.show_more_options()
        else:
            self.hide_more_options()

    def show_more_options(self) -> None:
        self.ui.btn_more_options.setIcon(QtUtilsMixIn.get_qicon("down_arrow.svg"))
        oSize = self.ui.frame_more_options.sizeHint()
        self.ui.frame_more_options.setFixedHeight(oSize.height())

    def hide_more_options(self) -> None:
        self.ui.btn_more_options.setIcon(QtUtilsMixIn.get_qicon("right_arrow.svg"))
        self.ui.frame_more_options.setFixedHeight(0)

    @Slot(bool)
    def run_update(self) -> None:
        assert self.data
        # self.data.update(self, self.info_box)
        self.update_btns_during_update(False)

        self.trigger_update.emit(self.data, self.is_qubesos)

    @Slot(bool)
    def device_updated(self, success: bool) -> None:
        self.update_btns_during_update(True)
        if success:
            self.common_ui.info.info.emit("Nitrokey 3 successfully updated")
        else:
            self.common_ui.info.error.emit("Nitrokey 3 update failed")

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
