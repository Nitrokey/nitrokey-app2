from PyQt5 import QtGui, QtWidgets

class TrayNotification(QtWidgets.QSystemTrayIcon):
    def __init__(self):
        # os notification
        self.tray = QtWidgets.QSystemTrayIcon()
        self.tray.setIcon(QtGui.QIcon(":/images/new/icon_Logo_App_small.svg.ico"))
        self.tray.show()
        self.tray.setToolTip("Nitrokey App")
    def notify(self, message, message2):
        self.tray.showMessage(str(message), str(message2), msecs=2000)
