from PyQt5 import QtWidgets
from PyQt5.QtCore import QTimer, pyqtSlot


class EditButtonsWidget(QtWidgets.QWidget):
    def __init__(self, table, pop_up_copy, res, parent=None):
        super().__init__(parent)
        self.table_pws = table
        self.pop_up_copy = pop_up_copy

        # add your buttons
        layout = QtWidgets.QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        Copy = QtWidgets.QPushButton("Icon")
        Copy.setFixedSize(65, 65)
        Copy.clicked.connect(self.copy_to_clipboard_function)
        layout.addWidget(Copy)
        layout.addWidget(QtWidgets.QLabel(str(res)))

        self.setLayout(layout)

    @pyqtSlot()
    def copy_to_clipboard_function(self):
        buttons_index = self.table_pws.indexAt(self.pos())
        item = self.table_pws.item(buttons_index.row(), buttons_index.column() + 3)
        QtWidgets.QApplication.clipboard().setText(item.text())
        # qtimer popup
        self.time_to_wait = 5
        self.pop_up_copy.setText("Data added to clipboard.")  # {0} for time display
        self.pop_up_copy.setStyleSheet(
            "background-color: #2B5DD1; color: #FFFFFF ; border-style: outset;"
            "padding: 2px ; font: bold 20px ; border-width: 6px ; border-radius: 10px ; border-color: #2752B8;"
        )
        self.pop_up_copy.show()
        self.timer = QTimer(self)
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self.changeContent)
        self.timer.start()

    def changeContent(self):
        self.pop_up_copy.setText("Data added to clipboard.")
        self.time_to_wait -= 1
        if self.time_to_wait <= 0:
            self.pop_up_copy.hide()
            self.timer.stop()

    def closeEvent(self, event):
        self.timer.stop()
        event.accept()
