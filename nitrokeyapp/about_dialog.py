from PyQt5 import QtWidgets

from nitrokeyapp import __version__
from nitrokeyapp.qt_utils_mix_in import QtUtilsMixIn
from nitrokeyapp.ui.aboutdialog_ui import Ui_AboutDialog


class AboutDialog(QtUtilsMixIn, QtWidgets.QDialog):
    def __init__(self, qt_app: QtWidgets.QApplication):
        QtWidgets.QDialog.__init__(self)
        QtUtilsMixIn.__init__(self)

        self.app = qt_app
        self.ui = Ui_AboutDialog()
        self.ui.setupUi(self)
        self.ui.ButtonOK.clicked.connect(self.close)
        self.ui.VersionLabel.setText(__version__)
