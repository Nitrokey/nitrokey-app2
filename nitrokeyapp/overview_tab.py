from typing import Optional

from PyQt5.QtCore import pyqtSlot
from PyQt5.QtWidgets import QFileDialog, QWidget

from nitrokeyapp.device_data import DeviceData
from nitrokeyapp.information_box import InfoBox
from nitrokeyapp.qt_utils_mix_in import QtUtilsMixIn
from nitrokeyapp.ui.overview_tab import Ui_OverviewTab
from nitrokeyapp.worker import Worker


class OverviewTab(QtUtilsMixIn, QWidget):
    def __init__(self, info_box: InfoBox, parent: Optional[QWidget] = None) -> None:
        QWidget.__init__(self, parent)
        QtUtilsMixIn.__init__(self)

        self.data: Optional[DeviceData] = None
        self.info_box = info_box
        self.ui = Ui_OverviewTab()
        self.ui.setupUi(self)

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
        self.set_device_data("?", "?", "?")
        self.ui.progressBar_Update.hide()
        self.ui.progressBar_Download.hide()
        self.ui.progressBar_Finalization.hide()

    def refresh(self, data: DeviceData) -> None:
        if data == self.data:
            return
        self.reset()
        self.data = data

        self.set_device_data(str(data.path), str(data.uuid), str(data.version))

    def set_device_data(self, path: str, uuid: str, version: str) -> None:
        self.ui.nk3_lineedit_path.setText(path)
        self.ui.nk3_lineedit_uuid.setText(uuid)
        self.ui.nk3_lineedit_version.setText(version)

    def set_update_enabled(self, enabled: bool) -> None:
        tooltip = ""
        if enabled:
            self.info_box.hide()
        else:
            self.info_box.set_text_durable(
                "Please remove all Nitrokey 3 devices except the one you want to update."
            )
            tooltip = "Please remove all Nitrokey 3 devices except the one you want to update."

        self.ui.pushButtonUpdate.setEnabled(enabled)
        self.ui.pushButtonUpdate.setToolTip(tooltip)

    def show_more_options(self) -> None:
        self.collapse(self.ui.more_options_frame, self.ui.more_options_btn)

    @pyqtSlot()
    def run_update(self) -> None:
        assert self.data
        self.data.update(self, self.info_box)

    @pyqtSlot()
    def update_with_file(self) -> None:
        assert self.data
        fdialog = QFileDialog()
        fdialog.setFileMode(QFileDialog.AnyFile)

        if fdialog.exec_():
            filenames = fdialog.selectedFiles()
            file = filenames[0]
            self.data.update(self, self.info_box, image=file)
