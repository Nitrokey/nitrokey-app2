from PyQt5 import QtCore    

class InfoBox():
    def __init__(self, information_frame, icon, text_label):
        self.information_frame = information_frame
        self.icon = icon
        self.text_label = text_label
        self.information_frame.setStyleSheet("background-color: #f2f2f2;")
        self.icon.setFixedSize(QtCore.QSize(22, 22))
    def set_text(self, text):
         self.text_label.setText(text)
         self.information_frame.show()
         QtCore.QTimer.singleShot(5000, self.hide)
    def set_text_durable(self, text):
        self.text_label.setText(text)
        self.information_frame.show()
    def hide(self):
        self.text_label.setText("")
        self.information_frame.hide()
