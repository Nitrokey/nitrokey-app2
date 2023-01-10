from typing import List, Optional, Tuple, Type, TypeVar
from PyQt5 import QtWidgets, uic
from PyQt5.QtCore import Qt, QThread, pyqtSignal, pyqtSlot, QObject, QFile, QTextStream, QTimer, QSortFilterProxyModel, QSize, QRect
from PyQt5.Qt import QApplication, QClipboard, QLabel, QMovie, QIcon, QProgressBar,QProgressDialog, QMessageBox

from nitropyapp.qt_utils_mix_in import QtUtilsMixIn

class AboutDialog(QtUtilsMixIn, QtWidgets.QDialog):
    def __init__(self, qt_app: QtWidgets.QApplication):
        QtWidgets.QDialog.__init__(self)
        QtUtilsMixIn.__init__(self)

        self.app = qt_app
