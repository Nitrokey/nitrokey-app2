from PyQt5 import QtWidgets
from PyQt5.QtCore import pyqtSlot

from nitrokeyapp.edit_button_widget import EditButtonsWidget


# pws not in use for now (was working for pro/storage)
@pyqtSlot()
def table_pws_function(self):
    index = self.table_pws.currentIndex()
    item = self.table_pws.item(index.row(), index.column() + 1)
    item2 = self.table_pws.item(index.row(), index.column() + 2)
    item3 = self.table_pws.item(index.row(), index.column() + 3)
    item4 = self.table_pws.item(index.row(), index.column() + 4)
    item5 = self.table_pws.item(index.row(), index.column() + 5)

    self.scrollArea.show()
    self.information_label.show()
    self.pws_editslotname.setText(item.text())
    self.pws_editloginname.setText(item2.text())
    self.pws_editpassword.setText(item3.text())
    self.pws_editOTP.setText(item4.text())
    self.pws_editnotes.setText(item5.text())
    self.PWS_ButtonSaveSlot.setVisible(False)
    self.ButtonChangeSlot.setVisible(True)
    self.PWS_ButtonDelete.setVisible(True)
    # hides the otp creation stuff
    self.copy_current_otp.show()
    self.qr_code.hide()
    self.random_otp.hide()
    self.copy_otp.hide()
    self.pws_editOTP.setEchoMode(QtWidgets.QLineEdit.Password)
    self.show_hide_btn_2.hide()


def add_table_pws(self):

    row = self.table_pws.rowCount()
    self.table_pws.insertRow(row)
    qline = self.pws_editslotname.text()
    qline2 = self.pws_editloginname.text()
    qline3 = self.pws_editpassword.text()
    qline4 = self.pws_editOTP.text()
    qline5 = self.pws_editnotes.toPlainText()
    res = "{} {} {}".format(qline, "\n", qline2)

    # creates otp on key

    if not self.device.is_auth_admin:
        self.ask_pin("admin")
        return

    name = qline
    if len(name) == 0:
        self.user_err("need non-empty name")
        return

    idx = row
    who = "totp"
    # @fixme: what are the secret allowed lengths/chars
    # if len(secret)

    ret = self.device.TOTP.write(idx, name, qline4)
    if not ret.ok:
        self.msg(f"failed writing to {who.upper()} slot #{idx+1} err: {ret.name}")
    else:
        self.msg(f"wrote {who.upper()} slot #{idx+1}")
        self.otp_secret.clear()
        self.slot_select_otp(idx)

    self.table_pws.setCellWidget(
        row, 0, (EditButtonsWidget(self.table_pws, self.pop_up_copy, res))
    )
    self.table_pws.setItem(row, 1, (QtWidgets.QTableWidgetItem(qline)))
    self.table_pws.setItem(row, 2, (QtWidgets.QTableWidgetItem(qline2)))
    self.table_pws.setItem(row, 3, (QtWidgets.QTableWidgetItem(qline3)))
    self.table_pws.setItem(row, 4, (QtWidgets.QTableWidgetItem(qline4)))
    self.table_pws.setItem(row, 5, (QtWidgets.QTableWidgetItem(qline5)))
    self.pws_editslotname.setText("")
    self.pws_editloginname.setText("")
    self.pws_editpassword.setText("")
    self.pws_editOTP.setText("")
    self.pws_editnotes.setText("")


# adds the data existing of the key to the table
def add_table_pws_from_key(self, x):
    row = self.table_pws.rowCount()
    self.table_pws.insertRow(row)
    # self.table_pws.setItem(row , 0, (QtWidgets.QTableWidgetItem("Name")))
    # self.table_pws.setItem(row , 1, (QtWidgets.QTableWidgetItem("Username")))

    qline = self.device.TOTP.get_name(x)
    qline2 = ""
    qline3 = ""
    qline4 = self.device.TOTP.get_code(x)
    qline5 = ""
    res = "{} {} {}".format(qline, "\n", qline2)

    self.table_pws.setCellWidget(
        row, 0, (EditButtonsWidget(self.table_pws, self.pop_up_copy, res))
    )
    qlines = [qline, qline2, qline3, qline4, qline5]
    for i in range(1, len(qlines) + 1):
        self.table_pws.setItem(row, i, (QtWidgets.QTableWidgetItem(qlines[i - 1])))
    # self.table_pws.setItem(row , 1, (QtWidgets.QTableWidgetItem(qline)))
    # self.table_pws.setItem(row , 2, (QtWidgets.QTableWidgetItem(qline2)))
    # self.table_pws.setItem(row , 3, (QtWidgets.QTableWidgetItem(qline3)))
    # self.table_pws.setItem(row , 4, (QtWidgets.QTableWidgetItem(qline4)))
    # self.table_pws.setItem(row , 5, (QtWidgets.QTableWidgetItem(qline5)))
    pws_list = [
        self.pws_editslotname,
        self.pws_editloginname,
        self.pws_editpassword,
        self.pws_editOTP,
        self.pws_editnotes,
    ]
    for i in pws_list:
        pws_list.setText("")
    # self.pws_editslotname.setText("")
    # self.pws_editloginname.setText("")
    # self.pws_editpassword.setText("")
    # self.pws_editOTP.setText("")
    # self.pws_editnotes.setText("")


def add_pws(self):
    self.scrollArea.show()
    self.information_label.show()
    self.PWS_ButtonSaveSlot.setVisible(True)
    self.ButtonChangeSlot.setVisible(False)
    self.PWS_ButtonDelete.setVisible(False)
    # self.set_visible(QtWidgets.QFrame, ["groupbox_pw"], True)
    # self.set_enabled(QtWidgets.QFrame, ["groupbox_pw"], True)
    # self.set_enabled(QtWidgets.QPushButton, ["PWS_ButtonSaveSlot", "PWS_ButtonClose"], True)
    pws_list = [
        self.pws_editslotname,
        self.pws_editloginname,
        self.pws_editpassword,
        self.pws_editOTP,
        self.pws_editnotes,
    ]
    for i in pws_list:
        pws_list.setText("")
    # self.pws_editslotname.setText("")
    # self.pws_editloginname.setText("")
    # self.pws_editpassword.setText("")
    # self.pws_editOTP.setText("")
    # self.pws_editnotes.setText("")
    # shows the otp creation stuff again
    self.copy_current_otp.hide()
    self.qr_code.show()
    self.random_otp.show()
    self.copy_otp.show()
    self.pws_editOTP.setEchoMode(QtWidgets.QLineEdit.Normal)
    self.show_hide_btn_2.show()


def delete_pws(self):
    index = self.table_pws.currentIndex()
    self.table_pws.removeRow(index.row())
    self.table_pws.setCurrentCell(0, 0)


def change_pws(self):
    row = (self.table_pws.currentIndex()).row()
    self.table_pws.insertRow(row)

    index = self.table_pws.currentIndex()
    qline = self.pws_editslotname.text()
    qline2 = self.pws_editloginname.text()
    qline3 = self.pws_editpassword.text()
    qline4 = self.pws_editOTP.text()
    qline5 = self.pws_editnotes.toPlainText()
    res = "{} {} {}".format(qline, "\n", qline2)

    self.table_pws.setCellWidget(
        row, 0, (EditButtonsWidget(self.table_pws, self.pop_up_copy, res))
    )
    self.table_pws.setItem(row, 1, (QtWidgets.QTableWidgetItem(qline)))
    self.table_pws.setItem(row, 2, (QtWidgets.QTableWidgetItem(qline2)))
    self.table_pws.setItem(row, 3, (QtWidgets.QTableWidgetItem(qline3)))
    self.table_pws.setItem(row, 4, (QtWidgets.QTableWidgetItem(qline4)))
    self.table_pws.setItem(row, 5, (QtWidgets.QTableWidgetItem(qline5)))

    self.table_pws.removeRow(index.row())
    self.table_pws.setCurrentCell(index.row() - 1, 0)


# search function for the table
def filter_the_table(self):
    # searchbox
    for iterator in range(self.table_pws.rowCount()):
        self.table_pws.showRow(iterator)
        if self.searchbox.text() not in self.table_pws.item(iterator, 1).text():
            self.table_pws.hideRow(iterator)
