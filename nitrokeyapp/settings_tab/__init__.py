import binascii
import logging
from base64 import b32decode, b32encode
from enum import Enum
from random import randbytes
from typing import Callable, Optional

from PySide6.QtCore import Qt, QThread, QTimer, Signal, Slot
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import QLineEdit, QListWidgetItem, QWidget, QTreeWidgetItem

from nitrokeyapp.common_ui import CommonUi
from nitrokeyapp.device_data import DeviceData
from nitrokeyapp.qt_utils_mix_in import QtUtilsMixIn
from nitrokeyapp.worker import Worker
#from .data import pin_check

from .worker import SettingsWorker

# logger = logging.getLogger(__name__)

class SettingsTabState(Enum):
   Initial = 0
   Fido = 1
   FidoPw = 2
   otp = 3
   otpPw = 4

   NotAvailable = 99


class SettingsTab(QtUtilsMixIn, QWidget):
    # standard UI
    #    busy_state_changed = Signal(bool)
    #    error = Signal(str, Exception)
    #    start_touch = Signal()
    #    stop_touch = Signal()

    # worker triggers
    #    trigger_add_credential = Signal(DeviceData, Credential, bytes)

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        QWidget.__init__(self, parent)
        QtUtilsMixIn.__init__(self)

        self.data: Optional[DeviceData] = None
        self.common_ui = CommonUi()

        self.worker_thread = QThread()
        self._worker = SettingsWorker(self.common_ui)
        self._worker.moveToThread(self.worker_thread)
        self.worker_thread.start()

        self.ui = self.load_ui("settings_tab.ui", self)

        #Tree
        pin_icon = self.get_qicon("dialpad.svg")

        fido = QTreeWidgetItem(self.ui.settings_tree)
        pintype = SettingsTabState.Fido
        fido.setExpanded(False)
        name = "FIDO2"
        desc = "FIDO2 is an authentication standard that enables secure and passwordless access to online services. It uses public key cryptography to provide strong authentication and protect against phishing and other security threats."
        
        fido.setText(0, name)
        fido.setData(1, 0, pintype)
        fido.setData(2, 0, name)
        fido.setData(3, 0, desc)


        fido_pin = QTreeWidgetItem()
        pintype = SettingsTabState.FidoPw
        name = "FIDO2 Pin Settings"

        fido_pin.setIcon(0, pin_icon)
        fido.addChild(fido_pin)

        fido_pin.setText(0, name)
        fido_pin.setData(1, 0, pintype)
        fido_pin.setData(2, 0, name)


        otp = QTreeWidgetItem(self.ui.settings_tree)
        pintype = SettingsTabState.otp
        otp.setExpanded(False)
        name = "OTP"
        desc = "One-Time Password (OTP) is a security mechanism that generates a unique password for each login session. This password is typically valid for only one login attempt or for a short period of time, adding an extra layer of security to the authentication process. OTPs are commonly used in two-factor authentication systems to verify the identity of users."
        
        otp.setText(0, name)
        otp.setData(1, 0, pintype)
        otp.setData(2, 0, name)
        otp.setData(3, 0, desc)

        otp_pin = QTreeWidgetItem()
        pintype = SettingsTabState.otpPw
        name = "OTP Pin Settings"

        otp_pin.setText(0, name)
        otp_pin.setData(1, 0, pintype)
        otp_pin.setData(2, 0, name)

        otp_pin.setIcon(0, pin_icon)
        otp.addChild(otp_pin)

        self.ui.settings_tree.itemClicked.connect(self.show)

        self.ui.current_password.textChanged.connect(self.check_credential)
        self.ui.new_password.textChanged.connect(self.check_credential)
        self.ui.repeat_password.textChanged.connect(self.check_credential)

        self.reset()

    def field_btn(self) -> None:
        icon_visibility = self.get_qicon("visibility_off.svg")
        icon_check = self.get_qicon("done.svg")
        icon_false = self.get_qicon("close.svg")

        loc = QLineEdit.ActionPosition.TrailingPosition
        self.action_current_password_show = self.ui.current_password.addAction(icon_visibility, loc)
        self.action_current_password_show.triggered.connect(self.act_current_password_show)

        self.action_new_password_show = self.ui.new_password.addAction(icon_visibility, loc)
        self.action_new_password_show.triggered.connect(self.act_new_password_show)

        self.action_repeat_password_show = self.ui.repeat_password.addAction(icon_visibility, loc)
        self.action_repeat_password_show.triggered.connect(self.act_repeat_password_show)

        self.show_current_password_check = self.ui.current_password.addAction(icon_check, loc)
        self.show_current_password_false = self.ui.current_password.addAction(icon_false, loc)

        self.show_repeat_password_check = self.ui.repeat_password.addAction(icon_check, loc)
        self.show_repeat_password_false = self.ui.repeat_password.addAction(icon_false, loc)

        self.action_current_password_show.setVisible(False)
        self.action_new_password_show.setVisible(False)
        self.action_repeat_password_show.setVisible(False)
        self.show_current_password_check.setVisible(False)
        self.show_current_password_false.setVisible(False)
        self.show_repeat_password_check.setVisible(False)
        self.show_repeat_password_false.setVisible(False)



    #    self.line_actions = [
    #        self.action_current_password_show,
    #        self.show_current_password_check,
    #        self.show_current_password_false,
    #        self.action_new_password_show,
    #        self.action_repeat_password_show,
    #    ]

    def show(self, item) -> None:
        pintype = item.data(1, 0)
        if pintype == SettingsTabState.Fido or pintype == SettingsTabState.otp:
            self.show_pin(item)
            self.collapse_all_except(item)
            item.setExpanded(True)
        else:
            self.edit_pin(item)

    def collapse_all_except(self, item):
        top_level_items = self.settings_tree.invisibleRootItem().takeChildren()
        for top_level_item in top_level_items:
            if top_level_item is not item.parent():
                top_level_item.setExpanded(False)
        self.settings_tree.invisibleRootItem().addChildren(top_level_items)


    def show_pin(self, item) -> None:
        self.ui.settings_empty.hide()
        self.ui.pinsettings_edit.hide()
        self.ui.pinsettings_desc.show()

        self.ui.btn_abort.hide()
        self.ui.btn_reset.hide()
        self.ui.btn_save.hide()
        
        pintype = item.data(1, 0)
        name = item.data(2, 0)
        desc = item.data(3, 0)

        self.ui.pin_name.setText(name)
        self.ui.pin_description.setText(desc)
        self.ui.pin_description.setReadOnly(True)


    def edit_pin(self, item) -> None:
        self.ui.settings_empty.hide()
        self.ui.pinsettings_desc.hide()
        self.ui.pinsettings_edit.show()

        self.ui.current_password.clear()
        self.ui.new_password.clear()
        self.ui.repeat_password.clear()

        self.ui.btn_abort.show()
        self.ui.btn_reset.show()
        self.ui.btn_save.show()

        self.ui.btn_abort.pressed.connect(lambda: self.abort(item))
        self.ui.btn_save.pressed.connect(lambda: self.save_pin(item))
        self.ui.btn_reset.pressed.connect(lambda: self.reset_pin(item))

        name = item.data(2, 0)

        self.ui.password_label.setText(name)

        self.field_btn()

    def abort(self, item) -> None:
        p_item = item.parent()
        self.show(p_item)

   # def reset(self) -> None:

   # def save(self) -> None:


    def act_current_password_show(self) -> None:
        self.set_current_password_show(self.ui.current_password.echoMode() == QLineEdit.Password, )  # type: ignore [attr-defined]

    def act_new_password_show(self) -> None:
        self.set_new_password_show(self.ui.new_password.echoMode() == QLineEdit.Password)  # type: ignore [attr-defined]

    def act_repeat_password_show(self) -> None:
        self.set_repeat_password_show(self.ui.repeat_password.echoMode() == QLineEdit.Password)  # type: ignore [attr-defined]


    def set_current_password_show(self, show: bool = True) -> None:
        icon_show = self.get_qicon("visibility.svg")
        icon_hide = self.get_qicon("visibility_off.svg")
        icon = icon_show if show else icon_hide
        mode = QLineEdit.Normal if show else QLineEdit.Password  # type: ignore [attr-defined]
        self.ui.current_password.setEchoMode(mode)
        self.action_current_password_show.setIcon(icon)

    def set_new_password_show(self, show: bool = True) -> None:
        icon_show = self.get_qicon("visibility.svg")
        icon_hide = self.get_qicon("visibility_off.svg")
        icon = icon_show if show else icon_hide
        mode = QLineEdit.Normal if show else QLineEdit.Password  # type: ignore [attr-defined]
        self.ui.new_password.setEchoMode(mode)
        self.action_new_password_show.setIcon(icon)

    def set_repeat_password_show(self, show: bool = True) -> None:
        icon_show = self.get_qicon("visibility.svg")
        icon_hide = self.get_qicon("visibility_off.svg")
        icon = icon_show if show else icon_hide
        mode = QLineEdit.Normal if show else QLineEdit.Password  # type: ignore [attr-defined]
        self.ui.repeat_password.setEchoMode(mode)
        self.action_repeat_password_show.setIcon(icon)

    @property
    def title(self) -> str:
        return "Settings"

    @property
    def widget(self) -> QWidget:
        return self.ui

    @property
    def worker(self) -> Optional[Worker]:
        return self._worker

    def reset(self) -> None:
        self.ui.settings_empty.show()
        self.ui.pinsettings_edit.hide()
        self.ui.pinsettings_desc.hide()

        self.ui.btn_abort.hide()
        self.ui.btn_reset.hide()
        self.ui.btn_save.hide()

    def refresh(self, data: DeviceData, force: bool = False) -> None:
        if data == self.data and not force:
            return
        self.reset()
        self.data = data

    def set_device_data(
        self, path: str, uuid: str, version: str, variant: str, init_status: str
    ) -> None:
        self.ui.nk3_path.setText(path)
        self.ui.nk3_uuid.setText(uuid)
        self.ui.nk3_version.setText(version)
        self.ui.nk3_variant.setText(variant)
        self.ui.nk3_status.setText(init_status)

    @Slot()
    def check_credential(self) -> None:
        current_password = self.ui.current_password.text()
        new_password = self.ui.new_password.text()
        repeat_password = self.ui.repeat_password.text()

        if len(current_password) > 0:
            self.action_current_password_show.setVisible(True)
        else:
            self.action_current_password_show.setVisible(False)

        if len(new_password) > 0:
            self.action_new_password_show.setVisible(True)
        else:
            self.action_new_password_show.setVisible(False)

        if len(repeat_password) >0:
            self.action_repeat_password_show.setVisible(True)
        else:
            self.action_repeat_password_show.setVisible(False)

        if len(repeat_password) > 0 and new_password == repeat_password:
            self.show_repeat_password_check.setVisible(True)
            self.show_repeat_password_false.setVisible(False)
        elif len(repeat_password) == 0 and len(new_password) == 0:
            self.show_repeat_password_false.setVisible(False)
            self.show_repeat_password_check.setVisible(False)
        else:
            self.show_repeat_password_false.setVisible(True)
            self.show_repeat_password_check.setVisible(False)
