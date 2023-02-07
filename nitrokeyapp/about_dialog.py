from PyQt5 import QtWidgets

from nitrokeyapp.qt_utils_mix_in import QtUtilsMixIn


class AboutDialog(QtUtilsMixIn, QtWidgets.QDialog):
    def __init__(self, qt_app: QtWidgets.QApplication):
        QtWidgets.QDialog.__init__(self)
        QtUtilsMixIn.__init__(self)

        self.app = qt_app
