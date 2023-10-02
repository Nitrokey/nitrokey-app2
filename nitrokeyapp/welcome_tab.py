from typing import Optional

from PyQt5.QtWidgets import QWidget

from nitrokeyapp import __version__
from nitrokeyapp.qt_utils_mix_in import QtUtilsMixIn
from nitrokeyapp.ui.welcome_tab import Ui_WelcomeTab


class WelcomeTab(QtUtilsMixIn, QWidget):
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        QWidget.__init__(self, parent)
        QtUtilsMixIn.__init__(self)

        self.ui = Ui_WelcomeTab()
        self.ui.setupUi(self)
        self.ui.VersionNr.setText(__version__)
