
from PyQt5 import QtWidgets
from PyQt5.Qt import QIcon
class TrayNotification(QtWidgets.QSystemTrayIcon):
    def __init__(self, tool_tip, message, message2):
        ## os notification
        self.tray = QtWidgets.QSystemTrayIcon()  
        self.tray.setIcon(QIcon(":/images/new/down_arrow.png"))
        self.tray.show() 
        self.tray.setToolTip(str(tool_tip))
        self.tray.showMessage(str(message),str(message2), msecs=2000)
