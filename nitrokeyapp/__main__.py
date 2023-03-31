import sys

from PyQt5 import QtWidgets

import nitrokeyapp.resources_rc  # noqa: F401
from nitrokeyapp.backend_thread import BackendThread
from nitrokeyapp.gui import GUI
from nitrokeyapp.qt_utils_mix_in import QtUtilsMixIn


def main():
    # backend thread init
    QtUtilsMixIn.backend_thread = BackendThread()

    app = QtWidgets.QApplication(sys.argv)
    window = GUI(app)  # noqa: F841
    app.exec()


main()
