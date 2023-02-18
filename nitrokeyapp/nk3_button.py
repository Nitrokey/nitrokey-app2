from PyQt5 import QtGui, QtWidgets
from PyQt5.QtCore import QSize, pyqtSlot

# from nitrokeyapp.change_pin_dialog import ChangePinDialog
from nitrokeyapp.pynitrokey_for_gui import (
    Nk3Context,
    change_pin,
    nk3_update_helper,
    set_pin,
)


class Nk3Button(QtWidgets.QWidget):
    list_nk3_keys = []

    @classmethod
    def get(cls):
        return Nk3Button.list_nk3_keys

    def __init__(
        self,
        device,
        nitrokeys_window,
        layout_nk_btns,
        nitrokey3_frame,
        nk3_lineedit_uuid,
        nk3_lineedit_path,
        nk3_lineedit_version,
        tabs,
        progressBarUpdate,
        change_pin_open_dialog,
        set_pin_open_dialog,
        change_pin_dialog,
        set_pin_dialog,
        buttonLayout_nk3,
    ):
        super().__init__()
        self.device = device
        self.uuid = self.device.uuid()
        self.path = self.device.path
        self.version = self.device.version()
        self.change_pin_open_dialog = change_pin_open_dialog
        self.set_pin_open_dialog = set_pin_open_dialog
        self.change_pin_dialog = change_pin_dialog
        self.set_pin_dialog = set_pin_dialog
        self.nitrokeys_window = nitrokeys_window
        self.layout_nk_btns = layout_nk_btns
        self.nitrokey3_frame = nitrokey3_frame
        self.buttonlayout_nk3 = buttonLayout_nk3
        self.tabs = tabs
        self.nk3_lineedit_uuid = nk3_lineedit_uuid
        self.nk3_lineedit_path = nk3_lineedit_path
        self.nk3_lineedit_version = nk3_lineedit_version
        self.progressbarupdate = progressBarUpdate
        # needs to create button in the vertical navigation with the nitrokey type and serial number as text
        self.btn_nk3 = QtWidgets.QPushButton(
            QtGui.QIcon(":/images/icon/usb_new.png"),
            "Nitrokey 3:" f"{self.device.uuid().value%10000}",
        )
        self.btn_nk3.setFixedSize(184, 40)
        self.btn_nk3.setIconSize(QSize(20, 20))
        self.btn_nk3.clicked.connect(lambda: self.nk3_btn_pressed())
        self.btn_nk3.setStyleSheet(
            "border :4px solid ;"
            "border-color : #474642;"
            "border-width: 2px;"
            "border-radius: 5px;"
            "font-size: 14pt;"
        )
        # "font-weight: bold;")
        self.layout_nk_btns.addWidget(self.btn_nk3)
        self.widget_nk_btns = QtWidgets.QWidget()
        self.widget_nk_btns.setLayout(self.layout_nk_btns)
        self.nitrokeys_window.setWidget(self.widget_nk_btns)
        self.own_update_btn = QtWidgets.QPushButton("Update", self.nitrokey3_frame)
        self.own_change_pin = QtWidgets.QPushButton("Change PIN", self.nitrokey3_frame)
        self.own_set_pin = QtWidgets.QPushButton("Set PIN", self.nitrokey3_frame)
        self.own_update_btn.setGeometry(12, 134, 413, 27)
        self.own_change_pin.setGeometry(12, 166, 413, 27)
        self.own_set_pin.setGeometry(12, 198, 413, 27)
        self.buttonlayout_nk3.addWidget(self.own_update_btn)
        self.buttonlayout_nk3.addWidget(self.own_change_pin)
        self.buttonlayout_nk3.addWidget(self.own_set_pin)
        self.own_update_btn.hide()
        self.own_change_pin.hide()
        self.own_set_pin.hide()
        self.ctx = Nk3Context(self.device.path)
        self.own_update_btn.clicked.connect(
            lambda: nk3_update_helper(self.ctx, self.progressbarupdate, 0, 0)
        )
        self.own_change_pin.clicked.connect(self.change_pin_open_dialog)
        self.own_set_pin.clicked.connect(self.set_pin_open_dialog)
        self.change_pin_dialog.btn_ok.clicked.connect(
            lambda: change_pin(
                self.ctx,
                self.change_pin_dialog.current_pin.text(),
                self.change_pin_dialog.new_pin.text(),
                self.change_pin_dialog.confirm_new_pin.text(),
            )
        )
        self.set_pin_dialog.btn_ok.clicked.connect(
            lambda: set_pin(
                self.ctx,
                self.set_pin_dialog.new_pin.text(),
                self.set_pin_dialog.confirm_new_pin.text(),
            )
        )
        Nk3Button.list_nk3_keys.append(self)

    @pyqtSlot()
    def nk3_btn_pressed(self):
        self.tabs.show()
        for i in range(1, 6):
            self.tabs.setTabVisible(i, False)
        self.nk3_lineedit_uuid.setText(str(self.uuid))
        self.nk3_lineedit_path.setText(str(self.path))
        self.nk3_lineedit_version.setText(str(self.version))
        self.nitrokey3_frame.show()
        for i in Nk3Button.get():
            i.own_update_btn.hide()
            i.own_change_pin.hide()
            i.own_set_pin.hide()
        self.own_update_btn.show()
        self.own_change_pin.show()
        self.own_set_pin.show()

    def __del__(self):
        self.tabs.hide()
        self.nitrokeys_window.update()
        self.btn_nk3.close()
        self.own_update_btn.close()
        self.own_change_pin.close()
        self.own_set_pin.close()
        Nk3Button.list_nk3_keys.remove(self)

    def update(self, device):
        self.device = device
        self.path = self.device.path
        self.version = self.device.version()
        self.nk3_lineedit_path.setText(str(self.path))
        self.nk3_lineedit_version.setText(str(self.version))
        self.ctx = Nk3Context(self.device.path)
