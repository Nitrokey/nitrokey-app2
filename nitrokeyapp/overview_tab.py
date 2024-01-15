from typing import Optional

from pynitrokey.nk3.admin_app import InitStatus
from PySide6.QtCore import Signal, Slot
from PySide6.QtWidgets import QFileDialog, QWidget

from nitrokeyapp.device_data import DeviceData
from nitrokeyapp.information_box import InfoBox
from nitrokeyapp.qt_utils_mix_in import QtUtilsMixIn
from nitrokeyapp.worker import Worker


class OverviewTab(QtUtilsMixIn, QWidget):
    busy_state_changed = Signal(bool)

    def __init__(self, info_box: InfoBox, parent: Optional[QWidget] = None) -> None:
        QWidget.__init__(self, parent)
        QtUtilsMixIn.__init__(self)

        self.data: Optional[DeviceData] = None
        self.info_box = info_box

        # self.ui === self -> this tricks mypy due to monkey-patching self
        self.ui = self.load_ui("overview_tab.ui", self)

        self.collapse(self.ui.more_options_frame, self.ui.more_options_btn)
        self.ui.update_with_file_btn.clicked.connect(self.update_with_file)
        self.ui.more_options_btn.clicked.connect(self.show_more_options)
        self.ui.pushButtonUpdate.clicked.connect(self.run_update)

        self.reset()

    @property
    def title(self) -> str:
        return "Overview"

    @property
    def widget(self) -> QWidget:
        return self

    @property
    def worker(self) -> Optional[Worker]:
        return None

    def reset(self) -> None:
        self.data = None
        self.set_device_data("?", "?", "?", "?", "?")
        self.ui.progressBar_Update.hide()
        self.ui.progressBar_Download.hide()
        self.ui.progressBar_Finalization.hide()

    def refresh(self, data: DeviceData) -> None:
        if data == self.data:
            return
        self.reset()
        self.data = data
        if data.status.variant is None:
            return

        self.set_device_data(
            str(data.path),
            str(data.uuid),
            str(data.version),
            str(data.status.variant.name),
            str(data.status.init_status),
        )

        if data.status.init_status is None:
            self.ui.label_init_status.hide()
            self.ui.nk3_lineedit_init_status.hide()
        else:
            self.status_error(InitStatus(data.status.init_status))

    def set_device_data(
        self, path: str, uuid: str, version: str, variant: str, init_status: str
    ) -> None:
        self.ui.nk3_lineedit_path.setText(path)
        self.ui.nk3_lineedit_uuid.setText(uuid)
        self.ui.nk3_lineedit_version.setText(version)
        self.ui.nk3_lineedit_variant.setText(variant)
        self.ui.nk3_lineedit_init_status.setText(init_status)

    def status_error(self, init: InitStatus) -> None:
        if init.is_error():
            self.ui.warnNoticeIcon.show()
            self.ui.moreInfo.show()
        else:
            self.ui.warnNoticeIcon.hide()
            self.ui.moreInfo.hide()

    def set_update_enabled(self, enabled: bool) -> None:
        tooltip = ""
        if enabled:
            self.info_box.hide_status()
        else:
            self.info_box.set_status(
                "Please remove all Nitrokey 3 devices except the one you want to update."
            )
            tooltip = "Please remove all Nitrokey 3 devices except the one you want to update."

        self.ui.pushButtonUpdate.setEnabled(enabled)
        self.ui.pushButtonUpdate.setToolTip(tooltip)
        self.ui.more_options_btn.setEnabled(enabled)
        self.ui.more_options_btn.setToolTip(tooltip)

    def update_btns_during_update(self, enabled: bool) -> None:
        tooltip = ""
        if enabled:
            self.busy_state_changed.emit(False)
            self.ui.pushButtonUpdate.setEnabled(enabled)
            self.ui.pushButtonUpdate.setToolTip(tooltip)
            self.ui.more_options_btn.setEnabled(enabled)
            self.ui.more_options_btn.setToolTip(tooltip)
            self.ui.update_with_file_btn.setEnabled(enabled)
            self.ui.update_with_file_btn.setToolTip(tooltip)
        else:
            tooltip = "Update is already running. Please wait."
            self.busy_state_changed.emit(True)
            self.ui.pushButtonUpdate.setEnabled(enabled)
            self.ui.pushButtonUpdate.setToolTip(tooltip)
            self.ui.more_options_btn.setEnabled(enabled)
            self.ui.more_options_btn.setToolTip(tooltip)
            self.ui.update_with_file_btn.setEnabled(enabled)
            self.ui.update_with_file_btn.setToolTip(tooltip)

    def show_more_options(self) -> None:
        self.collapse(self.ui.more_options_frame, self.ui.more_options_btn)

    @Slot()
    def run_update(self) -> None:
        assert self.data
        self.data.update(self, self.info_box)

    @Slot()
    def update_with_file(self) -> None:
        assert self.data
        fdialog = QFileDialog()
        fdialog.setFileMode(QFileDialog.FileMode.AnyFile)

        if fdialog.exec_():
            filenames = fdialog.selectedFiles()
            file = filenames[0]
            self.data.update(self, self.info_box, image=file)
