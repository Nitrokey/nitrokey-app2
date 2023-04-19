import sys

from PyQt5 import QtWidgets

import nitrokeyapp.ui.resources_rc  # noqa: F401
from nitrokeyapp.backend_thread import BackendThread
from nitrokeyapp.gui import GUI
from nitrokeyapp.logger import init_logging
from nitrokeyapp.qt_utils_mix_in import QtUtilsMixIn


def main():
    # backend thread init
    QtUtilsMixIn.backend_thread = BackendThread()

    app = QtWidgets.QApplication(sys.argv)
    init_logging()
    window = GUI(app)  # noqa: F841
    app.exec()


main()
