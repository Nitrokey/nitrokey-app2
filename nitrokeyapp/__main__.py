import sys

from PyQt5 import QtWidgets

import nitrokeyapp.ui.resources_rc  # noqa: F401
from nitrokeyapp.gui import GUI
from nitrokeyapp.logger import init_logging


def main() -> None:
    app = QtWidgets.QApplication(sys.argv)
    init_logging()
    window = GUI(app)  # noqa: F841
    app.exec()


main()
