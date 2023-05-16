from typing import Optional

from PyQt5.QtWidgets import QWidget

from nitrokeyapp.ui.overview_tab import Ui_OverviewTab


class OverviewTab(QWidget):
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)

        self.ui = Ui_OverviewTab()
        self.ui.setupUi(self)

        self.ui.Nitrokey3.hide()
        self.ui.progressBar_Update.hide()
        self.ui.progressBar_Download.hide()
        self.ui.progressBar_Finalization.hide()
