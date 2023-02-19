import sys

from PyQt5 import QtWidgets

import nitrokeyapp.resources_rc  # noqa: F401
from nitrokeyapp.gui import GUI, BackendThread
from nitrokeyapp.qt_utils_mix_in import QtUtilsMixIn

def main():
    # backend thread init
    QtUtilsMixIn.backend_thread = BackendThread()

    app = QtWidgets.QApplication(sys.argv)

    # set stylesheet
    # file = QFile(":/light.qss")
    # file.open(QFile.ReadOnly | QFile.Text)
    # stream = QTextStream(file)
    # app.setStyleSheet(stream.readAll())
    window = GUI(app)
    app.exec()


main()
