import logging
from enum import Enum
from typing import Dict, List, Optional, Tuple

from fido2.ctap2.base import Info
from nitrokey.nk3.secrets_app import SelectResponse
from PySide6.QtCore import QThread, Signal, Slot
from PySide6.QtWidgets import QLineEdit, QTreeWidgetItem, QWidget

from nitrokeyapp.common_ui import CommonUi
from nitrokeyapp.device_data import DeviceData
from nitrokeyapp.qt_utils_mix_in import QtUtilsMixIn
from nitrokeyapp.worker import Worker

from .worker import SettingsWorker

logger = logging.getLogger(__name__)


class State(Enum):
    Initial = 0
    Fido = 1
    FidoPin = 2
    FidoReset = 3

    Passwords = 4
    PasswordsPin = 5
    PasswordsReset = 6

    NotAvailable = 99


PIN_ICON = QtUtilsMixIn.get_qicon("dialpad.svg")
RESET_ICON = QtUtilsMixIn.get_qicon("refresh.svg")
SHOW_ICON = QtUtilsMixIn.get_qicon("visibility.svg")
HIDE_ICON = QtUtilsMixIn.get_qicon("visibility_off.svg")

SETTINGS: Dict[State, Dict] = {
    State.Fido: {
        "parent": None,
        "icon": None,
        "name": "FIDO2",
        "desc": "FIDO2 is an authentication standard that enables secure "
        + "and passwordless access to online services. It uses public "
        + "key cryptography to provide strong authentication and "
        + "protect against phishing and other security threats.",
    },
    State.FidoPin: {
        "parent": State.Fido,
        "icon": PIN_ICON,
        "name": "Pin Change",
    },
    State.FidoReset: {
        "parent": State.Fido,
        "icon": RESET_ICON,
        "name": "Factory Reset",
        "desc": "During a FIDO reset, the password is not set. All "
        + "previously set credentials are removed. "
        + "Any existing authentication data, such as U2F, Passkeys and FIDO2 "
        + "authentication factors are deleted. After the reset, the user "
        + "will need to re-register or re-enroll their authentication "
        + "credentials to access the system or service again.",
    },
    State.Passwords: {
        "parent": None,
        "icon": None,
        "name": "Passwords",
        "desc": "Within Passwords various credentials and 2FAs like OTPs can "
        + "be stored and managed. Supported are: Plain usernames using a "
        + "password, HOTPs, TOTPs, ReverseHOTPs and HMAC.",
    },
    State.PasswordsPin: {
        "parent": State.Passwords,
        "icon": PIN_ICON,
        "name": "Pin Change",
    },
    State.PasswordsReset: {
        "parent": State.Passwords,
        "icon": RESET_ICON,
        "name": "Factory Reset",
        "desc": "This operation will unevitably remove all your credentials "
        + "in Passwords!",
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

        # outgoing signals
        self.trigger_fido_status.connect(self._worker.fido_status)
        self.trigger_passwords_status.connect(self._worker.passwords_status)
        self.trigger_passwords_change_pw.connect(self._worker.passwords_change_pw)
        self.trigger_fido_change_pw.connect(self._worker.fido_change_pw)
        self.trigger_fido_reset.connect(self._worker.fido_reset)
        self.trigger_passwords_reset.connect(self._worker.passwords_reset)

        # incoming signals
        self._worker.status_fido.connect(self.handle_status_fido)
        self._worker.info_passwords.connect(self.handle_info_passwords)

        self._worker.change_pw_fido.connect(self.handle_pin_change)
        self._worker.change_pw_passwords.connect(self.handle_pin_change)

        self._worker.reset_fido.connect(self.handle_reset)
        self._worker.reset_passwords.connect(self.handle_reset)

        self.ui = self.load_ui("settings_tab.ui", self)

        self.ui.btn_abort.pressed.connect(self.abort)
        self.ui.btn_save.pressed.connect(self.save_action)
        self.ui.btn_reset.pressed.connect(self.reset_action)

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

        self.ui.settings_tree.itemClicked.connect(self.show_widget)

        self.ui.current_password.textChanged.connect(self.check_credential)
        self.ui.new_password.textChanged.connect(self.check_credential)
        self.ui.repeat_password.textChanged.connect(self.check_credential)

        self.active_item: Optional[QTreeWidgetItem] = None

        self.reset()
        self.field_btn()

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
        self.action_new_password_show.triggered.connect(self.act_new_password_show)

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

    def show_widget(self, item: Optional[QTreeWidgetItem]) -> None:
        self.active_item = item
        if item is None:
            self.view_settings_empty()
            return

        sta = item.data(1, 0)
        if sta in [State.Fido, State.Passwords]:
            self.view_overview(item)
            self.collapse_all_except(item)
            item.setExpanded(True)
        elif sta in [State.FidoPin, State.PasswordsPin]:
            self.view_edit_pin(item)
        elif sta in [State.FidoReset, State.PasswordsReset]:
            self.view_reset(item)

    def collapse_all_except(self, item: QTreeWidgetItem) -> None:
        top_level_items = self.ui.settings_tree.invisibleRootItem().takeChildren()
        for top_level_item in top_level_items:
            if top_level_item is not item.parent():
                top_level_item.setExpanded(False)
        self.ui.settings_tree.invisibleRootItem().addChildren(top_level_items)

    def update_status_form(self, data: Optional[List[Tuple[str, str]]] = None) -> None:
        if data is not None:
            self.ui.status_form.show()
        else:
            self.ui.status_form.hide()

        for idx in range(6):
            l_obj = getattr(self.ui, f"label_{idx}")
            d_obj = getattr(self.ui, f"value_{idx}")

            if data is not None and len(data) > idx:
                l_obj.setText(f"{data[idx][0]}: ")
                d_obj.setText(data[idx][1])
                l_obj.show()
                d_obj.show()
            else:
                l_obj.hide()
                d_obj.hide()

    def view_overview(self, item: QTreeWidgetItem) -> None:
        self.ui.settings_frame.show()

        self.ui.status_form.show()
        self.ui.pin_form.hide()

        self.ui.info_label.show()
        self.ui.warning_label.hide()

        self.ui.btn_abort.hide()
        self.ui.btn_reset.hide()
        self.ui.btn_save.hide()

        state = item.data(1, 0)
        tmpl = SETTINGS[state]
        name = tmpl.get("name")
        desc = tmpl.get("desc")

        self.ui.headline_label.setText(name)
        self.ui.info_label.setText(desc)

        if state == State.Fido:
            self.trigger_fido_status.emit(self.data)
        elif state == State.Passwords:
            self.trigger_passwords_status.emit(self.data)

    def view_edit_pin(self, item: QTreeWidgetItem) -> None:
        state = item.data(1, 0)
        tmpl = SETTINGS[state]

        self.show_current_password(False)

        self.ui.settings_frame.show()
        self.ui.pin_form.show()
        self.ui.status_form.hide()

        self.ui.warning_label.hide()
        self.ui.info_label.hide()

        self.field_clear()

        if state == State.FidoPin:
            self.trigger_fido_status.emit(self.data)
        elif state == State.PasswordsPin:
            self.trigger_passwords_status.emit(self.data)

        self.ui.btn_abort.show()
        self.ui.btn_reset.hide()
        self.ui.btn_save.show()

        self.ui.btn_save.setEnabled(False)
        self.ui.btn_save.setToolTip("Cannot save")

        name = SETTINGS[SETTINGS[state]["parent"]]["name"]
        name += " | " + tmpl["name"]
        self.ui.headline_label.setText(name)

    def view_reset(self, item: QTreeWidgetItem) -> None:
        state = item.data(1, 0)
        tmpl = SETTINGS[state]

        name = SETTINGS[SETTINGS[state]["parent"]]["name"]
        name += " | " + tmpl["name"]
        desc = tmpl.get("desc")

        self.ui.settings_frame.show()
        self.ui.pin_form.hide()
        self.ui.status_form.show()

        self.ui.info_label.show()

        self.ui.btn_abort.show()
        self.ui.btn_reset.show()
        self.ui.btn_save.hide()

        self.ui.warning_label.setText(
            "**Reset for FIDO2 is only possible 10secs "
            + "after plugging in the device.**"
        )

        if state == State.FidoReset:
            self.trigger_fido_status.emit(self.data)
            self.ui.warning_label.show()
        elif state == State.PasswordsReset:
            self.trigger_passwords_status.emit(self.data)

        self.ui.headline_label.setText(name)
        self.ui.info_label.setText(desc)

    def view_settings_empty(self) -> None:
        self.ui.settings_frame.hide()

        self.ui.btn_abort.hide()
        self.ui.btn_reset.hide()
        self.ui.btn_save.hide()

    def abort(self) -> None:
        p_item = None
        if isinstance(self.active_item, QTreeWidgetItem):
            p_item = self.active_item.parent()
        self.active_item = None
        self.show_widget(p_item)

    def save_action(self) -> None:
        assert isinstance(self.active_item, QTreeWidgetItem)
        state = self.active_item.data(1, 0)
        old_pin = self.ui.current_password.text()
        new_pin = self.ui.repeat_password.text()

        if state == State.FidoPin:
            self.trigger_fido_change_pw.emit(self.data, old_pin, new_pin)
            self.field_clear()
            self.common_ui.info.info.emit("done - please use new pin to verify key")
        elif state == State.PasswordsPin:
            self.trigger_passwords_change_pw.emit(self.data, old_pin, new_pin)
            self.field_clear()

    def reset_action(self) -> None:
        assert isinstance(self.active_item, QTreeWidgetItem)
        state = self.active_item.data(1, 0)

        if state == State.FidoReset:
            self.trigger_fido_reset.emit(self.data)
            self.abort()
        elif state == State.PasswordsReset:
            self.trigger_passwords_reset.emit(self.data)
            self.abort()

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
        self.ui.current_password.show()
        self.ui.current_password_label.show()

        if show:
            self.ui.current_password.setEnabled(True)
            self.ui.current_password.setPlaceholderText("<insert old PIN>")
        else:
            self.ui.current_password.setEnabled(False)
            self.ui.current_password.setPlaceholderText("<No PIN Set>")

    @Slot(Info, int)
    def handle_status_fido(self, fido_state: Info, pin_retries: int) -> None:
        if self.active_item is None:
            return

        state = self.active_item.data(1, 0)
        has_pin = fido_state.options["clientPin"]

        if state in [State.Fido, State.FidoReset]:

            self.update_status_form(
                [
                    ("PIN set", "yes" if has_pin else "no"),
                    (
                        "PIN retries",
                        str(pin_retries) if has_pin else "n/a",
                    ),
                    ("Versions", ", ".join(fido_state.versions)),
                    ("Extensions", ", ".join(fido_state.extensions)),
                ]
            )
        elif state == State.FidoPin:
            self.show_current_password(has_pin)
            self.ui.status_form.hide()

    @Slot(SelectResponse)
    def handle_info_passwords(self, pin_set: bool, status: SelectResponse) -> None:

        if self.active_item is None:
            return

        state = self.active_item.data(1, 0)
        if state in [
            State.Passwords,
            State.PasswordsReset,
        ]:

            data = [
                ("PIN set", "yes" if pin_set else "no"),
                ("PIN retries", str(status.pin_attempt_counter)),
                ("Version", status.version_str()),
            ]
            if status.serial_number is not None:
                data += [("Serial", str(status.serial_number.hex()).upper())]

            self.update_status_form(data)
            self.show_current_password(pin_set)

        elif state == State.PasswordsReset:
            self.show_current_password(pin_set)
            self.ui.status_form.hide()

    @Slot()
    def handle_reset(self) -> None:
        if self.active_item is None:
            return
        state = self.active_item.data(1, 0)
        if state == State.FidoReset:
            self.trigger_fido_status.emit(self.data)
        elif state == State.PasswordsReset:
            self.trigger_passwords_status.emit(self.data)

    @Slot()
    def handle_pin_change(self) -> None:
        if self.active_item is None:
            return
        state = self.active_item.data(1, 0)
        if state == State.FidoPin:
            self.trigger_fido_status.emit(self.data)
        elif state == State.PasswordsPin:
            self.trigger_passwords_status.emit(self.data)

    @Slot(bool)
    def check_credential(self) -> None:
        self.common_ui.info.info.emit("")

        tool_Tip = "Credential cannot be saved:"
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

        if not self.ui.current_password.isEnabled():
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
