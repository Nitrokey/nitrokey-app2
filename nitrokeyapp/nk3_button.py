from pynitrokey.nk3 import Nitrokey3Device
from PyQt5 import QtGui, QtWidgets
from PyQt5.QtCore import QSize, pyqtSlot

from nitrokeyapp.information_box import InfoBox
from nitrokeyapp.secrets_widget import SecretsWidget
from nitrokeyapp.pynitrokey_for_gui import Nk3Context, nk3_update


class Nk3Button(QtWidgets.QWidget):
    list_nk3_keys: list["Nk3Button"] = []

    @classmethod
    def get(cls) -> list["Nk3Button"]:
        return Nk3Button.list_nk3_keys

    def __init__(
        self,
        device: Nitrokey3Device,
        nitrokeys_window: QtWidgets.QScrollArea,
        layout_nk_btns: QtWidgets.QVBoxLayout,
        nitrokey3_frame: QtWidgets.QFrame,
        nk3_lineedit_uuid: QtWidgets.QLineEdit,
        nk3_lineedit_path: QtWidgets.QLineEdit,
        nk3_lineedit_version: QtWidgets.QLineEdit,
        tabs: QtWidgets.QTabWidget,
        progressBarUpdate: QtWidgets.QProgressBar,
        progressBarDownload: QtWidgets.QProgressBar,
        progressBarFinalization: QtWidgets.QProgressBar,
        # change_pin_open_dialog,
        # set_pin_open_dialog,
        # change_pin_dialog,
        # set_pin_dialog,
        buttonLayout_nk3: QtWidgets.QHBoxLayout,
        info_frame: InfoBox,
        secrets: SecretsWidget,
    ) -> None:
        super().__init__()
        self.device = device
        self.uuid = self.device.uuid()
        self.path = self.device.path
        self.version = self.device.version()
        # self.change_pin_open_dialog = change_pin_open_dialog
        # self.set_pin_open_dialog = set_pin_open_dialog
        # self.change_pin_dialog = change_pin_dialog
        # self.set_pin_dialog = set_pin_dialog
        self.nitrokeys_window = nitrokeys_window
        self.layout_nk_btns = layout_nk_btns
        self.nitrokey3_frame = nitrokey3_frame
        self.buttonlayout_nk3 = buttonLayout_nk3
        self.tabs = tabs
        self.nk3_lineedit_uuid = nk3_lineedit_uuid
        self.nk3_lineedit_path = nk3_lineedit_path
        self.nk3_lineedit_version = nk3_lineedit_version
        self.progressbarupdate = progressBarUpdate
        self.progressbardownload = progressBarDownload
        self.progressbarfinalization = progressBarFinalization
        self.info_frame = info_frame
        self.secrets = secrets
        # needs to create button in the vertical navigation with the nitrokey type and serial number as text
        self.btn_nk3 = QtWidgets.QPushButton(
            QtGui.QIcon(":/images/icon/usb_new.png"),
            "Nitrokey 3: " f"{str(self.uuid)[:5]}",
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
        # self.own_change_pin = QtWidgets.QPushButton("Change PIN", self.nitrokey3_frame)
        # self.own_set_pin = QtWidgets.QPushButton("Set PIN", self.nitrokey3_frame)
        self.own_update_btn.setGeometry(12, 134, 413, 27)
        # self.own_change_pin.setGeometry(12, 166, 413, 27)
        # self.own_set_pin.setGeometry(12, 198, 413, 27)
        self.buttonlayout_nk3.addWidget(self.own_update_btn)
        # self.buttonlayout_nk3.addWidget(self.own_change_pin)
        # self.buttonlayout_nk3.addWidget(self.own_set_pin)
        self.own_update_btn.hide()
        # self.own_change_pin.hide()
        # self.own_set_pin.hide()
        self.ctx = Nk3Context(self.device.path)
        self.own_update_btn.clicked.connect(
            lambda: nk3_update(
                self.ctx,
                self.progressbarupdate,
                self.progressbardownload,
                self.progressbarfinalization,
                None,
                None,
                False,
                self.info_frame,
            )
        )
        # self.own_change_pin.clicked.connect(self.change_pin_open_dialog)
        # self.own_set_pin.clicked.connect(self.set_pin_open_dialog)
        # self.change_pin_dialog.btn_ok.clicked.connect(
        #     lambda: change_pin(
        #         self.ctx,
        #         self.change_pin_dialog.current_pin.text(),
        #         self.change_pin_dialog.new_pin.text(),
        #         self.change_pin_dialog.confirm_new_pin.text(),
        #     )
        # )
        # self.change_pin_dialog.btn_ok.clicked.connect(self.clear_pins)
        # self.set_pin_dialog.btn_ok.clicked.connect(
        #     lambda: set_pin(
        #         self.ctx,
        #         self.set_pin_dialog.new_pin.text(),
        #         self.set_pin_dialog.confirm_new_pin.text(),
        #     )
        # )
        # self.set_pin_dialog.btn_ok.clicked.connect(self.clear_pins)
        Nk3Button.list_nk3_keys.append(self)

    @pyqtSlot()
    def nk3_btn_pressed(self) -> None:
        self.tabs.show()
        for i in range(1, 6):
            self.tabs.setTabVisible(i, False)
        # TODO: check version, don’t hardcode index
        self.tabs.setTabEnabled(4, True)
        self.tabs.setTabVisible(4, True)
        self.secrets.device = self.device
        self.nk3_lineedit_uuid.setText(str(self.uuid))
        self.nk3_lineedit_path.setText(str(self.path))
        self.nk3_lineedit_version.setText(str(self.version))
        self.nitrokey3_frame.show()
        for button in Nk3Button.get():
            button.own_update_btn.hide()
            # button.own_change_pin.hide()
            # button.own_set_pin.hide()
        self.own_update_btn.show()
        # self.own_change_pin.show()
        # self.own_set_pin.show()

    def __del__(self) -> None:
        self.secrets.device = None
        self.secrets.reset()
        self.tabs.setCurrentIndex(0)
        self.tabs.hide()
        self.nitrokeys_window.update()
        self.btn_nk3.close()
        self.own_update_btn.close()
        # self.own_change_pin.close()
        # self.own_set_pin.close()
        Nk3Button.list_nk3_keys.remove(self)

    def set_device(self, device: Nitrokey3Device) -> None:
        self.device = device
        self.uuid = self.device.uuid()
        self.path = self.device.path
        self.version = self.device.version()
        self.nk3_lineedit_uuid.setText(str(self.uuid))
        self.nk3_lineedit_path.setText(str(self.path))
        self.nk3_lineedit_version.setText(str(self.version))
        self.ctx = Nk3Context(self.device.path)

    # def clear_pins(self):
    #     self.change_pin_dialog.current_pin.clear()
    #     self.change_pin_dialog.new_pin.clear()
    #     self.change_pin_dialog.confirm_new_pin.clear()
    #     self.set_pin_dialog.new_pin.clear()
    #     self.set_pin_dialog.confirm_new_pin.clear()
