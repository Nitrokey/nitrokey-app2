from typing import Optional

from PyQt5.QtCore import pyqtSlot
from PyQt5.QtWidgets import QWidget

from nitrokeyapp.device_data import DeviceData
from nitrokeyapp.information_box import InfoBox
from nitrokeyapp.ui.overview_tab import Ui_OverviewTab


class OverviewTab(QWidget):
    def __init__(self, info_box: InfoBox, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)

        self.data: Optional[DeviceData] = None
        self.info_box = info_box

        self.ui = Ui_OverviewTab()
        self.ui.setupUi(self)

        self.ui.progressBar_Update.hide()
        self.ui.progressBar_Download.hide()
        self.ui.progressBar_Finalization.hide()

        self.ui.pushButtonUpdate.clicked.connect(self.run_update)

    def refresh(self, data: DeviceData) -> None:
        self.data = data
        self.ui.nk3_lineedit_path.setText(str(data.path))
        self.ui.nk3_lineedit_uuid.setText(str(data.uuid))
        self.ui.nk3_lineedit_version.setText(str(data.version))

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

    @pyqtSlot()
    def run_update(self) -> None:
        assert self.data
        self.data.update(self, self.info_box)
