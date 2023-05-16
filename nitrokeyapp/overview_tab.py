from typing import Optional

from PyQt5.QtWidgets import QWidget

from nitrokeyapp.device_data import DeviceData
from nitrokeyapp.ui.overview_tab import Ui_OverviewTab


class OverviewTab(QWidget):
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)

        self.ui = Ui_OverviewTab()
        self.ui.setupUi(self)

        self.ui.progressBar_Update.hide()
        self.ui.progressBar_Download.hide()
        self.ui.progressBar_Finalization.hide()

    def refresh(self, data: DeviceData) -> None:
        self.ui.nk3_lineedit_path.setText(str(data.path))
        self.ui.nk3_lineedit_uuid.setText(str(data.uuid))
        self.ui.nk3_lineedit_version.setText(str(data.version))
