import logging
from enum import Enum
from typing import Optional, Dict

from nitrokey.nk3.secrets_app import SelectResponse
from PySide6.QtCore import QThread, Signal, Slot
from PySide6.QtWidgets import QLineEdit, QTreeWidgetItem, QWidget

from nitrokeyapp.common_ui import CommonUi
from nitrokeyapp.device_data import DeviceData
from nitrokeyapp.qt_utils_mix_in import QtUtilsMixIn
from nitrokeyapp.worker import Worker

from .worker import SettingsWorker

logger = logging.getLogger(__name__)


class SettingsTabState(Enum):
    Initial = 0
    Fido = 1
    FidoPw = 2
    FidoRst = 3
    passwords = 4
    passwordsPw = 5
    passwordsRst = 6

    NotAvailable = 99


PIN_ICON = QtUtilsMixIn.get_qicon("dialpad.svg")
RESET_ICON = QtUtilsMixIn.get_qicon("refresh.svg")
SHOW_ICON = QtUtilsMixIn.get_qicon("visibility.svg")
HIDE_ICON = QtUtilsMixIn.get_qicon("visibility_off.svg")

SETTINGS: Dict[SettingsTabState, Dict] = {
    SettingsTabState.Fido: {
        "parent": None,
        "icon": None,
        "name": "FIDO2",
        "desc": "FIDO2 is an authentication standard that enables secure "
        + "and passwordless access to online services. It uses public "
        + "key cryptography to provide strong authentication and "
        + "protect against phishing and other security threats.",
    },
    SettingsTabState.FidoPw: {
        "parent": SettingsTabState.Fido,
        "icon": PIN_ICON,
        "name": "Pin Change",
    },
    SettingsTabState.FidoRst: {
        "parent": SettingsTabState.Fido,
        "icon": RESET_ICON,
        "name": "Factory Reset",
        "desc": "During a FIDO reset, the password is not set. All "
        + "previously set credentials are removed. This means that "
        + "any existing authentication data, such as passwords, or other "
        + "authentication factors are deleted. After the reset, the user "
        + "will need to re-register or re-enroll their authentication "
        + "credentials to access the system or service again.",
    },
    SettingsTabState.passwords: {
        "parent": None,
        "icon": None,
        "name": "Passwords",
        "desc": "---- insert generic passwords text here ----",
    },
    SettingsTabState.passwordsPw: {
        "parent": SettingsTabState.passwords,
        "icon": PIN_ICON,
        "name": "Pin Change",
    },
    SettingsTabState.passwordsRst: {
        "parent": SettingsTabState.passwords,
        "icon": RESET_ICON,
        "name": "Factory Reset",
        "desc": "---- insert passwords reset text here ----",
    },
}


class SettingsTab(QtUtilsMixIn, QWidget):
    # standard UI
    busy_state_changed = Signal(bool)
    error = Signal(str, Exception)
    start_touch = Signal()
    stop_touch = Signal()

    # worker triggers
    trigger_fido_status = Signal(DeviceData)
    trigger_passwords_status = Signal(DeviceData)

    trigger_passwords_change_pw = Signal(DeviceData, str, str)
    trigger_fido_change_pw = Signal(DeviceData, str, str)

    trigger_fido_reset = Signal(DeviceData)
    trigger_passwords_reset = Signal(DeviceData)

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        QWidget.__init__(self, parent)
        QtUtilsMixIn.__init__(self)

        self.data: Optional[DeviceData] = None
        self.common_ui = CommonUi()

        self.worker_thread = QThread()
        self._worker = SettingsWorker(self.common_ui)
        self._worker.moveToThread(self.worker_thread)
        self.worker_thread.start()

        self.trigger_fido_status.connect(self._worker.fido_status)
        self.trigger_passwords_status.connect(self._worker.passwords_status)
        self.trigger_passwords_change_pw.connect(
            self._worker.passwords_change_pw
        )
        self.trigger_fido_change_pw.connect(self._worker.fido_change_pw)
        self.trigger_fido_reset.connect(self._worker.fido_reset)
        self.trigger_passwords_reset.connect(self._worker.passwords_reset)

        self._worker.status_fido.connect(self.handle_status_fido)
        self._worker.info_passwords.connect(self.handle_info_passwords)

        self.ui = self.load_ui("settings_tab.ui", self)

        self.ui.btn_abort.pressed.connect(self.abort)
        self.ui.btn_save.pressed.connect(self.save_pin)

        self.items = {}

        # top-lvl items
        for state, data in SETTINGS.items():
            if data.get("parent") is None:
                item = QTreeWidgetItem(self.ui.settings_tree)
                item.setText(0, data["name"])
                item.setData(1, 0, state)
                self.items[state] = item

        # sub-items
        for state, data in SETTINGS.items():
            if data.get("parent") is not None:
                item = QTreeWidgetItem(self.items[data["parent"]])
                item.setText(0, data["name"])
                item.setData(1, 0, state)
                self.items[state] = item

        # # Tree
        # pin_icon = self.get_qicon("dialpad.svg")
        # rst_icon = self.get_qicon("refresh.svg")

        # fido = QTreeWidgetItem(self.ui.settings_tree)
        # pintype = SettingsTabState.Fido
        # fido.setExpanded(False)
        # name = "FIDO2"
        # desc = "FIDO2 is an authentication standard that enables secure and passwordless access to online services. It uses public key cryptography to provide strong authentication and protect against phishing and other security threats."

        # fido.setText(0, name)
        # fido.setData(1, 0, pintype)
        # fido.setData(2, 0, name)
        # fido.setData(3, 0, desc)

        # fido_pin = QTreeWidgetItem()
        # pintype = SettingsTabState.FidoPw
        # name = "Pin Settings"

        # fido_pin.setIcon(0, pin_icon)
        # fido.addChild(fido_pin)

        # fido_pin.setText(0, name)
        # fido_pin.setData(1, 0, pintype)
        # fido_pin.setData(2, 0, name)

        # fido_rst = QTreeWidgetItem()
        # pintype = SettingsTabState.FidoRst
        # name = "Reset"
        # desc = "During a FIDO reset, the password is not set. All previously set credentials are removed. This means that any existing authentication data, such as passwords, or other authentication factors are deleted. After the reset, the user will need to re-register or re-enroll their authentication credentials to access the system or service again."

        # fido_rst.setIcon(0, rst_icon)
        # fido.addChild(fido_rst)

        # fido_rst.setText(0, name)
        # fido_rst.setData(1, 0, pintype)
        # fido_rst.setData(2, 0, name)
        # fido_rst.setData(3, 0, desc)

        # passwords = QTreeWidgetItem(self.ui.settings_tree)
        # pintype = SettingsTabState.passwords
        # passwords.setExpanded(False)
        # name = "Passwords"
        # desc = "One-Time Password (OTP) is a security mechanism that generates a unique password for each login session. This password is typically valid for only one login attempt or for a short period of time, adding an extra layer of security to the authentication process. OTPs are commonly used in two-factor authentication systems to verify the identity of users."

        # passwords.setText(0, name)
        # passwords.setData(1, 0, pintype)
        # passwords.setData(2, 0, name)
        # passwords.setData(3, 0, desc)

        # passwords_pin = QTreeWidgetItem()
        # pintype = SettingsTabState.passwordsPw
        # name = "Pin Settings"

        # passwords_pin.setText(0, name)
        # passwords_pin.setData(1, 0, pintype)
        # passwords_pin.setData(2, 0, name)

        # passwords_pin.setIcon(0, pin_icon)
        # passwords.addChild(passwords_pin)

        # passwords_rst = QTreeWidgetItem()
        # pintype = SettingsTabState.passwordsRst
        # name = "Reset"
        # desc = "During a password reset, the password is no longer set. All passwords (TOTP/HTOTP/HMAC) secrets are removed. This means that any existing credentials in the password store will be deleted."

        # passwords_rst.setIcon(0, rst_icon)
        # passwords.addChild(passwords_rst)

        # passwords_rst.setText(0, name)
        # passwords_rst.setData(1, 0, pintype)
        # passwords_rst.setData(2, 0, name)
        # passwords_rst.setData(3, 0, desc)

        self.ui.settings_tree.itemClicked.connect(self.show_widget)

        self.ui.current_password.textChanged.connect(self.check_credential)
        self.ui.new_password.textChanged.connect(self.check_credential)
        self.ui.repeat_password.textChanged.connect(self.check_credential)

        self.active_item: Optional[QTreeWidgetItem] = None

        self.reset()

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
        self.view_settings_empty()
        self.ui.btn_abort.hide()
        self.ui.btn_reset.hide()
        self.ui.btn_save.hide()

    def refresh(self, data: DeviceData, force: bool = False) -> None:
        if data == self.data and not force:
            return
        self.reset()
        self.data = data

    def field_btn(self) -> None:
        icon_visibility = self.get_qicon("visibility_off.svg")
        icon_check = self.get_qicon("done.svg")
        icon_false = self.get_qicon("close.svg")

        loc = QLineEdit.ActionPosition.TrailingPosition
        self.action_current_password_show = self.ui.current_password.addAction(
            icon_visibility, loc
        )
        self.action_current_password_show.triggered.connect(
            self.act_current_password_show
        )

        self.action_new_password_show = self.ui.new_password.addAction(
            icon_visibility, loc
        )
        self.action_new_password_show.triggered.connect(
            self.act_new_password_show
        )

        self.action_repeat_password_show = self.ui.repeat_password.addAction(
            icon_visibility, loc
        )
        self.action_repeat_password_show.triggered.connect(
            self.act_repeat_password_show
        )

        self.show_current_password_check = self.ui.current_password.addAction(
            icon_check, loc
        )
        self.show_current_password_false = self.ui.current_password.addAction(
            icon_false, loc
        )

        self.show_repeat_password_check = self.ui.repeat_password.addAction(
            icon_check, loc
        )
        self.show_repeat_password_false = self.ui.repeat_password.addAction(
            icon_false, loc
        )

        self.action_current_password_show.setVisible(False)
        self.action_new_password_show.setVisible(False)
        self.action_repeat_password_show.setVisible(False)
        self.show_current_password_check.setVisible(False)
        self.show_current_password_false.setVisible(False)
        self.show_repeat_password_check.setVisible(False)
        self.show_repeat_password_false.setVisible(False)

    def show_widget(self, item: QTreeWidgetItem) -> None:
        self.active_item = item
        sta = item.data(1, 0) if item else None
        if sta in [SettingsTabState.Fido, SettingsTabState.passwords]:
            self.view_show_pin(item)
            self.collapse_all_except(item)
            item.setExpanded(True)
        elif sta in [SettingsTabState.FidoPw, SettingsTabState.passwordsPw]:
            self.view_edit_pin(item)
        elif sta in [SettingsTabState.FidoRst, SettingsTabState.passwordsRst]:
            self.view_reset(item)
        else:
            self.view_settings_empty()

    def collapse_all_except(self, item: QTreeWidgetItem) -> None:
        top_level_items = (
            self.ui.settings_tree.invisibleRootItem().takeChildren()
        )
        for top_level_item in top_level_items:
            if top_level_item is not item.parent():
                top_level_item.setExpanded(False)
        self.ui.settings_tree.invisibleRootItem().addChildren(top_level_items)

    def view_show_pin(self, item: QTreeWidgetItem) -> None:
        self.show_passwords_status(False)
        self.show_current_password(False)

        self.ui.settings_frame.show()
        self.show_current_password(False)
        self.ui.new_password_label.hide()
        self.ui.new_password.hide()
        self.ui.repeat_password_label.hide()
        self.ui.repeat_password.hide()

        self.ui.status_label.show()
        self.ui.info_label.show()
        self.ui.warning_label.hide()

        self.ui.btn_abort.hide()
        self.ui.btn_reset.hide()
        self.ui.btn_save.hide()

        # pintype = item.data(1, 0)
        # name = item.data(2, 0)
        # desc = item.data(3, 0)

        state = item.data(1, 0)
        tmpl = SETTINGS[state]

        name = tmpl.get("name")
        desc = tmpl.get("desc")

        self.ui.password_label.setText(name)
        self.ui.info_label.setText(desc)
        if state == SettingsTabState.Fido:
            self.trigger_fido_status.emit(self.data)
        elif state == SettingsTabState.passwords:
            self.trigger_passwords_status.emit(self.data)
            self.show_passwords_status(True)
        self.show_current_password(False)

    def view_edit_pin(self, item: QTreeWidgetItem) -> None:
        state = item.data(1, 0)
        tmpl = SETTINGS[state]

        self.show_passwords_status(False)
        self.show_current_password(False)

        self.ui.settings_frame.show()
        self.ui.current_password_label.show()
        self.ui.current_password.show()
        self.ui.new_password_label.show()
        self.ui.new_password.show()
        self.ui.repeat_password_label.show()
        self.ui.repeat_password.show()

        self.ui.status_label.hide()
        self.ui.info_label.hide()
        self.ui.warning_label.hide()

        self.common_ui.info.info.emit("")

        self.field_clear()

        if state == SettingsTabState.FidoPw:
            self.trigger_fido_status.emit(self.data)
        elif state == SettingsTabState.passwordsPw:
            self.trigger_passwords_status.emit(self.data)

        self.ui.btn_abort.show()
        self.ui.btn_reset.hide()
        self.ui.btn_save.show()
        self.ui.btn_save.setEnabled(False)
        self.ui.btn_save.setToolTip("Cannot save")

        self.ui.password_label.setText(tmpl.get("name"))

        self.field_btn()

    def view_reset(self, item: QTreeWidgetItem) -> None:
        state = item.data(1, 0)
        tmpl = SETTINGS[state]
        name = tmpl.get("name")
        desc = tmpl.get("desc")

        self.show_passwords_status(False)
        self.show_current_password(False)

        self.ui.settings_frame.show()
        self.show_current_password(False)
        self.ui.new_password_label.hide()
        self.ui.new_password.hide()
        self.ui.repeat_password_label.hide()
        self.ui.repeat_password.hide()

        self.ui.status_label.show()
        self.ui.info_label.show()

        self.ui.btn_abort.show()
        self.ui.btn_reset.show()
        self.ui.btn_save.hide()

        self.ui.warning_label.setText(
            "**Reset for FIDO2 is only possible 10secs "
            + "after plugging in the device.**"
        )

        if state == SettingsTabState.FidoRst:
            self.trigger_fido_status.emit(self.data)
            self.ui.warning_label.show()
        elif state == SettingsTabState.passwordsRst:
            self.trigger_passwords_status.emit(self.data)
            self.show_passwords_status(True)
        self.show_current_password(False)

        self.ui.password_label.setText(name)
        self.ui.info_label.setText(desc)

        self.ui.btn_abort.pressed.connect(self.abort)
        self.ui.btn_reset.pressed.connect(self.reset_pin)

    def view_settings_empty(self) -> None:
        self.ui.settings_frame.hide()
        self.show_passwords_status(False)

        self.show_current_password(False)
        self.ui.new_password_label.hide()
        self.ui.new_password.hide()
        self.ui.repeat_password_label.hide()
        self.ui.repeat_password.hide()

        self.ui.status_label.hide()
        self.ui.info_label.hide()

        self.ui.btn_abort.hide()
        self.ui.btn_reset.hide()
        self.ui.btn_save.hide()

    def abort(self) -> None:
        p_item = None
        if isinstance(self.active_item, QTreeWidgetItem):
            p_item = self.active_item.parent()
        self.active_item = None
        self.show_widget(p_item)

    def save_pin(self) -> None:
        assert isinstance(self.active_item, QTreeWidgetItem)
        pintype = self.active_item.data(1, 0)
        old_pin = self.ui.current_password.text()
        new_pin = self.ui.repeat_password.text()

        if pintype == SettingsTabState.FidoPw:
            self.trigger_fido_change_pw.emit(self.data, old_pin, new_pin)
            self.field_clear()
            self.abort()
            self.common_ui.info.info.emit(
                "done - please use new pin to verify key"
            )
        else:
            self.trigger_passwords_change_pw.emit(self.data, old_pin, new_pin)
            self.abort()
            self.field_clear()

    def reset_pin(self, item: QTreeWidgetItem) -> None:
        pintype = item.data(1, 0)

        if pintype == SettingsTabState.FidoRst:
            self.trigger_fido_reset.emit(self.data)
            self.abort()
            self.field_clear()
        elif pintype == SettingsTabState.passwordsRst:
            self.trigger_passwords_reset.emit(self.data)
            self.abort()
            self.field_clear()

    def act_current_password_show(self) -> None:
        mode = self.ui.current_password.echoMode()
        show = mode == QLineEdit.Password  # type: ignore [attr-defined]
        self.set_current_password_show(show)

    def act_new_password_show(self) -> None:
        mode = self.ui.new_password.echoMode()
        show = mode == QLineEdit.Password  # type: ignore [attr-defined]
        self.set_new_password_show(show)

    def act_repeat_password_show(self) -> None:
        mode = self.ui.repeat_password.echoMode()
        show = mode == QLineEdit.Password  # type: ignore [attr-defined]
        self.set_repeat_password_show(show)

    def set_current_password_show(self, show: bool = True) -> None:
        icon = SHOW_ICON if show else HIDE_ICON
        mode = QLineEdit.Normal if show else QLineEdit.Password  # type: ignore [attr-defined]
        self.ui.current_password.setEchoMode(mode)
        self.action_current_password_show.setIcon(icon)

    def set_new_password_show(self, show: bool = True) -> None:
        icon = SHOW_ICON if show else HIDE_ICON
        mode = QLineEdit.Normal if show else QLineEdit.Password  # type: ignore [attr-defined]
        self.ui.new_password.setEchoMode(mode)
        self.action_new_password_show.setIcon(icon)

    def set_repeat_password_show(self, show: bool = True) -> None:
        icon = SHOW_ICON if show else HIDE_ICON
        mode = QLineEdit.Normal if show else QLineEdit.Password  # type: ignore [attr-defined]
        self.ui.repeat_password.setEchoMode(mode)
        self.action_repeat_password_show.setIcon(icon)

    def set_device_data(
        self,
        path: str,
        uuid: str,
        version: str,
        variant: str,
        init_status: str,
    ) -> None:
        self.ui.nk3_path.setText(path)
        self.ui.nk3_uuid.setText(uuid)
        self.ui.nk3_version.setText(version)
        self.ui.nk3_variant.setText(variant)
        self.ui.nk3_status.setText(init_status)

    def field_clear(self) -> None:
        self.ui.current_password.clear()
        self.ui.new_password.clear()
        self.ui.repeat_password.clear()

    def show_current_password(self, show: bool) -> None:
        if show:
            self.ui.current_password.show()
            self.ui.current_password_label.show()
        else:
            self.ui.current_password.hide()
            self.ui.current_password_label.hide()

    def show_passwords_status(self, show: bool) -> None:
        if show:
            self.ui.version_label.show()
            self.ui.version.show()
            self.ui.counter_label.show()
            self.ui.counter.show()
            self.ui.serial_label.show()
            self.ui.serial.show()
        else:
            self.ui.version_label.hide()
            self.ui.version.hide()
            self.ui.counter_label.hide()
            self.ui.counter.hide()
            self.ui.serial_label.hide()
            self.ui.serial.hide()

    @Slot(bool)
    def handle_status_fido(self, fido_state: bool) -> None:
        self.fido_state = fido_state
        if self.fido_state:
            pin = "Fido2-Pin is set!"
            if self.ui.status_label.isVisible():
                self.show_current_password(False)
            else:
                self.show_current_password(True)
        else:
            pin = "Fido2-Pin is not set!"
            self.show_current_password(False)
        self.ui.status_label.setText(pin)

    @Slot(SelectResponse)
    def handle_info_passwords(
        self, passwords_state: bool, status: SelectResponse
    ) -> None:
        self.passwords_state = passwords_state
        self.passwords_counter = str(status.pin_attempt_counter)
        self.passwords_version = str(status.version_str())
        if status.serial_number is not None:
            self.passwords_serial_nr = str(status.serial_number.hex())
        if self.passwords_state:
            pin = "Password-Pin is set!"
            if self.ui.status_label.isVisible():
                self.show_current_password(False)
            else:
                self.show_current_password(True)
        else:
            pin = "Password-Pin is not set!"
            self.show_current_password(False)
        self.ui.status_label.setText(pin)
        self.ui.version.setText(self.passwords_version)
        self.ui.counter.setText(self.passwords_counter)
        self.ui.serial.setText(self.passwords_serial_nr)

    @Slot()
    def check_credential(self, new: bool) -> None:
        self.common_ui.info.info.emit("")

        tool_Tip = "Credeantial cannot be saved:"
        can_save = True

        new_password = self.ui.new_password.text()
        repeat_password = self.ui.repeat_password.text()
        current_password_len = len(self.ui.current_password.text())
        new_password_len = len(new_password)
        repeat_password_len = len(repeat_password)

        self.action_current_password_show.setVisible(False)
        self.action_new_password_show.setVisible(False)
        self.action_repeat_password_show.setVisible(False)
        self.show_repeat_password_check.setVisible(False)
        self.show_repeat_password_false.setVisible(False)

        if self.ui.current_password.isHidden():
            pass
        else:
            if current_password_len <= 3:
                can_save = False
            if current_password_len == 0:
                tool_Tip = tool_Tip + "\n- Enter your Current Password"
            if current_password_len >= 1:
                self.action_current_password_show.setVisible(True)
            if current_password_len >= 1 and current_password_len <= 3:
                self.common_ui.info.info.emit("Current Password is too short")
                tool_Tip = tool_Tip + "\n- Current Password is too short"

        if new_password_len <= 3:
            can_save = False
        if new_password_len == 0:
            tool_Tip = tool_Tip + "\n- Enter your New Password"
        if new_password_len == 0 and current_password_len >= 4:
            self.common_ui.info.info.emit("Enter your New Password")
        if new_password_len >= 1:
            self.action_new_password_show.setVisible(True)
        if new_password_len >= 1 and new_password_len <= 3:
            can_save = False
            self.common_ui.info.info.emit("New Password is too short")
            tool_Tip = tool_Tip + "\n- New Password is too short"

        if repeat_password_len == 0:
            can_save = False
            tool_Tip = tool_Tip + "\n- Repeat your New Password"
        if repeat_password_len >= 1:
            self.action_repeat_password_show.setVisible(True)
        if repeat_password_len >= 1 and repeat_password != new_password:
            can_save = False
            self.common_ui.info.info.emit("Repeat Password are not equal")
            tool_Tip = tool_Tip + "\n- Repeat Password are not equal"
            self.show_repeat_password_check.setVisible(False)
            self.show_repeat_password_false.setVisible(True)
        if repeat_password_len >= 4 and new_password == repeat_password:
            self.show_repeat_password_check.setVisible(True)
            self.show_repeat_password_false.setVisible(False)

        self.ui.btn_save.setEnabled(can_save)
        if can_save:
            tool_Tip = "Credential Save"

        self.ui.btn_save.setToolTip(tool_Tip)
