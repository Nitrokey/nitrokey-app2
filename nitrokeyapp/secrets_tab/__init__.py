from datetime import datetime
from typing import Optional
import binascii
from base64 import b32decode
from enum import Enum
import logging

from PySide6.QtCore import Qt, QThread, QTimer, Signal, Slot
from PySide6.QtGui import QGuiApplication, QIcon, QAction
from PySide6.QtWidgets import QDialog, QListWidgetItem, QWidget, QLineEdit

from nitrokeyapp.device_data import DeviceData
from nitrokeyapp.qt_utils_mix_in import QtUtilsMixIn

# from nitrokeyapp.ui.secrets_tab import Ui_SecretsTab
from nitrokeyapp.worker import Worker

from .data import Credential, OtpData, OtpKind
from .worker import SecretsWorker

# TODO:
# - logging
# - handle expired OTP
# - add OTP copy to clipboard
# - investigate layout during OTP display
# - disable UI during operations
# - confirm new PIN


logger = logging.getLogger(__name__)


def parse_base32(s: str) -> bytes:
    n = len(s) % 8
    if n:
        s += (8 - n) * "="
    return b32decode(s, casefold=True)


def is_base32(s: str) -> bool:
    try:
        parse_base32(s)
        return True
    except binascii.Error:
        return False


class SecretsTabState(Enum):
    Initial = 0
    ShowCred = 1
    AddCred = 2
    EditCred = 3

    NotAvailable = 99

class SecretsTab(QtUtilsMixIn, QWidget):
    # standard UI
    busy_state_changed = Signal(bool)
    error = Signal(str)
    start_touch = Signal()
    stop_touch = Signal()

    # worker triggers
    trigger_add_credential = Signal(DeviceData, Credential, bytes)
    trigger_check_device = Signal(DeviceData)
    trigger_delete_credential = Signal(DeviceData, Credential)
    trigger_generate_otp = Signal(DeviceData, Credential)
    trigger_refresh_credentials = Signal(DeviceData, bool)
    trigger_get_credential = Signal(DeviceData, Credential)
    trigger_edit_credential = Signal(DeviceData, Credential, bytes, bytes)

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        QWidget.__init__(self, parent)
        QtUtilsMixIn.__init__(self)

        self.worker_thread = QThread()
        self._worker = SecretsWorker(self)
        self._worker.moveToThread(self.worker_thread)
        self.worker_thread.start()

        self.trigger_add_credential.connect(self._worker.add_credential)
        self.trigger_check_device.connect(self._worker.check_device)
        self.trigger_delete_credential.connect(self._worker.delete_credential)
        self.trigger_generate_otp.connect(self._worker.generate_otp)
        self.trigger_refresh_credentials.connect(self._worker.refresh_credentials)
        self.trigger_get_credential.connect(self._worker.get_credential)
        self.trigger_edit_credential.connect(self._worker.edit_credential)

        self._worker.credential_added.connect(self.credential_added)
        self._worker.credential_deleted.connect(self.credential_deleted)
        self._worker.credentials_listed.connect(self.credentials_listed)
        self._worker.credential_edited.connect(self.credential_edited)
        self._worker.device_checked.connect(self.device_checked)
        self._worker.otp_generated.connect(self.otp_generated)
        self._worker.uncheck_checkbox.connect(self.uncheck_checkbox)

        self._worker.received_credential.connect(self.handle_receive_credential)
        self.next_credential_receiver: Optional[Callable[[Credential], None]] = None

        self.data: Optional[DeviceData] = None
        self.pin: Optional[str] = None
        self.active_credential: Optional[Credential] = None

        self.otp_timeout: Optional[datetime] = None
        self.otp_timer = QTimer()
        self.otp_timer.timeout.connect(self.update_otp_timeout)
        self.otp_timer.setInterval(1000)

        self.clipboard = QGuiApplication.clipboard()
        self.originalText = self.clipboard.text()

        # self.ui === self -> this tricks mypy due to monkey-patching self
        self.ui = self.load_ui("secrets_tab.ui", self)


        icon_copy = self.get_qicon("content_copy_FILL0_wght400_GRAD0_opsz24.svg")
        icon_refresh = self.get_qicon("refresh_FILL0_wght400_GRAD0_opsz24.svg")
        icon_edit = self.get_qicon("edit_FILL0_wght400_GRAD0_opsz24.png")
        icon_visibility = self.get_qicon("visibility_off_FILL0_wght400_GRAD0_opsz24.svg")

        loc = QLineEdit.ActionPosition.TrailingPosition
        self.action_username_copy = self.ui.username.addAction(icon_copy, loc)
        self.action_username_copy.triggered.connect(lambda: self.act_copy_line_edit(self.ui.username))

        self.action_password_copy = self.ui.password.addAction(icon_copy, loc)
        self.action_password_copy.triggered.connect(lambda: self.act_copy_line_edit(self.ui.password))

        self.action_password_show = self.ui.password.addAction(icon_visibility, loc)
        self.action_password_show.triggered.connect(self.act_password_show)

        self.action_comment_copy = self.ui.comment.addAction(icon_copy, loc)
        self.action_comment_copy.triggered.connect(lambda: self.act_copy_line_edit(self.ui.comment))

        self.action_otp_copy = self.ui.otp.addAction(icon_copy, loc)
        self.action_otp_copy.triggered.connect(lambda: self.act_copy_line_edit(self.ui.otp))

        self.action_otp_gen = self.ui.otp.addAction(icon_refresh, loc)
        self.action_otp_gen.triggered.connect(self.generate_otp)

        self.action_otp_edit = self.ui.otp.addAction(icon_edit, loc)
        self.action_otp_edit.triggered.connect(self.act_enable_otp_edit)

        self.line_actions = [
            self.action_username_copy,
            self.action_password_copy, self.action_password_show,
            self.action_comment_copy,
            self.action_otp_copy, self.action_otp_edit, self.action_otp_gen
        ]


#        labels = [
#            self.ui.labelName,
#            self.ui.labelAlgorithm,
#            self.ui.labelOtp,
#        ]
#        max_width = max([label.width() for label in labels])
#        for label in labels:
#            label.setMinimumWidth(max_width)

        self.ui.btn_add.pressed.connect(self.add_new_credential)
        self.ui.btn_abort.pressed.connect(lambda: self.show_secrets(True))
        self.ui.btn_save.pressed.connect(self.save_credential)
        self.ui.btn_edit.pressed.connect(self.prepare_edit_credential)

        self.ui.name.textChanged.connect(self.check_credential)
        self.ui.otp.textChanged.connect(self.check_credential)

        self.ui.btn_refresh.pressed.connect(self.refresh_credential_list)
        self.ui.is_protected.stateChanged.connect(self.refresh_credential_list)
        self.ui.secrets_list.currentItemChanged.connect(self.credential_changed)

        self.ui.btn_delete.pressed.connect(self.delete_credential)



#        self.ui.pushButtonOtpCopyToClipboard.pressed.connect(self.copy_to_clipboard)
#        self.ui.buttonDelete.pressed.connect(self.delete_credential)
#        self.ui.pushButtonOtpGenerate.pressed.connect(self.generate_otp)

        self.reset()

    @property
    def title(self) -> str:
        return "Passwords"

    @property
    def widget(self) -> QWidget:
        return self.ui

    @property
    def worker(self) -> Optional[Worker]:
        return self._worker

    def reset(self) -> None:
        self.data = None
        self.pin = None

        self.reset_ui()

    def reset_ui(self) -> None:
        self.ui.page_empty.show()
        self.ui.page_compatible.hide()
        self.ui.page_incompatible.hide()

        self.ui.credential_empty.show()
        self.ui.credential_show.hide()

        self.ui.secrets_list.clear()

        self.ui.btn_abort.hide()
        self.ui.btn_delete.hide()
        self.ui.btn_edit.hide()
        self.ui.btn_save.hide()

        self.show_secrets(True)

    def show_secrets(self, show: bool) -> None:
        if show:
            self.ui.page_empty.hide()
            self.ui.page_compatible.show()
            self.ui.page_incompatible.hide()
            self.hide_credential()
        else:
            self.ui.page_empty.hide()
            self.ui.page_compatible.hide()
            self.ui.page_incompatible.show()
            self.hide_credential()

    def refresh(self, data: DeviceData) -> None:
        if data == self.data:
            return
        self.data = data
        self.pin = None

        self.reset_ui()
        self.trigger_check_device.emit(data)

    @Slot(bool)
    def device_checked(self, compatible: bool) -> None:
        self.show_secrets(compatible)
        if compatible:
            self.refresh_credential_list()

    @Slot()
    def refresh_credential_list(self) -> None:
        assert self.data

        if not self.active_credential:
            current = self.get_current_credential()
            if current:
                self.active_credential = current

        pin_protected = self.ui.is_protected.isChecked()

        self.trigger_refresh_credentials.emit(self.data, pin_protected)


    @Slot(Credential)
    def credential_added(self, credential: Credential) -> None:
        self.active_credential = credential
        if credential.protected:
            self.ui.is_protected.setChecked(True)

        self.refresh_credential_list()

    @Slot(Credential)
    def credential_deleted(self, credential: Credential) -> None:
        self.active_credential = None
        self.refresh_credential_list()

    @Slot(Credential)
    def credential_edited(self, credential: Credential) -> None:
        self.active_credential = credential
        self.refresh_credential_list()

    @Slot(list)
    def credentials_listed(self, credentials: list[Credential]) -> None:
        self.reset_ui()

        active_item = None
        for credential in credentials:
            item = self.add_credential(credential)
            if self.active_credential and credential.id == self.active_credential.id:
                active_item = item
        self.ui.secrets_list.sortItems()
        if active_item:
            self.ui.secrets_list.setCurrentItem(active_item)

    @Slot(OtpData)
    def otp_generated(self, data: OtpData) -> None:
        self.ui.otp.setText(data.otp)
        self.data_otp = data.otp

        if data.validity:
            start, end = data.validity
            period = int((end - start).total_seconds())
            self.ui.otp_timeout_progress.setMaximum(period + period)

            self.otp_timeout = end + (end - start)
            self.otp_timer.start()
            self.update_otp_timeout()

        self.ui.otp_timeout_progress.setVisible(data.validity is not None)
        self.ui.otp.show()

    def add_credential(self, credential: Credential) -> QListWidgetItem:
        icon = (
            "lock_FILL0_wght500_GRAD0_opsz40"
            if credential.protected
            else "lock_open_FILL0_wght500_GRAD0_opsz40"
        )
        item = QListWidgetItem(credential.name)
        item.setIcon(self.get_qicon(f"{icon}.svg"))
        item.setData(Qt.ItemDataRole.UserRole, credential)
        self.ui.secrets_list.addItem(item)
        return item

    def get_credential(self, item: QListWidgetItem) -> Credential:
        data = item.data(Qt.ItemDataRole.UserRole)
        assert isinstance(data, Credential)
        return data

    def get_current_credential(self) -> Optional[Credential]:
        item = self.ui.secrets_list.currentItem()
        if not item:
            return None
        return self.get_credential(item)

    @Slot()
    def prepare_edit_credential(self) -> None:
        self.next_credential_receiver = self.edit_credential
        credential = self.active_credential
        self.trigger_get_credential.emit(self.data, credential)

    @Slot(Credential)
    def handle_receive_credential(self, credential: Credential) -> None:
        if self.next_credential_receiver:
            self.next_credential_receiver(credential)
            self.next_credential_receiver = None

    @Slot(Credential)
    def show_credential(self, credential: Credential) -> None:
        self.active_credential = credential

        # cache loaded credential into original credential in ListView
        item = self.ui.secrets_list.currentItem()
        if item is None:
            self.ui.credential_empty.show()
            self.ui.credential_show.hide()
            self.ui.btn_abort.hide()
            self.ui.btn_save.hide()
            self.ui.btn_delete.hide()
            self.ui.btn_edit.hide()
            return

        item.setData(Qt.ItemDataRole.UserRole, credential)


        ####self.act_password_show(show=False)
        for action in self.line_actions:
            action.setVisible(True)

        self.ui.credential_empty.hide()
        self.ui.credential_show.show()

        self.ui.btn_abort.hide()
        self.ui.btn_save.hide()
        self.ui.btn_delete.hide()
        self.ui.btn_edit.show()

        self.ui.name.hide()
        self.ui.name_label.show()
        self.ui.name_label.setText(credential.name)

        if credential.login:
            self.ui.username.setText(credential.login.decode(errors="replace"))
            self.action_username_copy.setEnabled(True)
        else:
            self.ui.username.setText("")
            self.action_username_copy.setEnabled(False)

        if credential.password:
            self.ui.password.setText(credential.password.decode(errors="replace"))
            self.action_password_copy.setEnabled(True)
            self.action_password_show.setEnabled(True)
        else:
            self.ui.password.setText("")
            self.action_password_copy.setEnabled(False)
            self.action_password_show.setEnabled(False)

        if credential.comment:
            self.ui.comment.setText(credential.comment.decode(errors="replace"))
            self.action_comment_copy.setEnabled(True)
        else:
            self.ui.comment.setText("")
            self.action_comment_copy.setEnabled(False)

        self.ui.name.setReadOnly(True)
        self.ui.username.setReadOnly(True)
        self.ui.password.setReadOnly(True)
        self.ui.comment.setReadOnly(True)

        self.ui.is_pin_protected.setChecked(credential.protected)
        self.ui.is_touch_protected.setChecked(credential.touch_required)

        self.hide_otp()
        if credential.otp:
            self.ui.otp.show()
            self.ui.otp.setReadOnly(True)
            self.ui.algorithm.show()
            self.ui.algorithm.setCurrentText(str(credential.otp))
            self.ui.algorithm.setEnabled(False)
            self.ui.otp.setPlaceholderText("<hidden>")

            self.action_otp_copy.setVisible(True)
            self.action_otp_edit.setVisible(False)
            self.action_otp_gen.setVisible(True)
        else:
            self.ui.algorithm.hide()
            self.ui.otp.hide()

    @Slot(Credential)
    def edit_credential(self, credential: Credential) -> None:
        item = self.ui.secrets_list.currentItem()
        item.setData(Qt.ItemDataRole.UserRole, credential)
        self.active_credential = credential

        self.ui.credential_empty.hide()
        self.ui.credential_show.show()

        self.ui.btn_abort.show()
        self.ui.btn_save.show()
        self.ui.btn_delete.show()
        self.ui.btn_edit.hide()

        ####self.act_password_show(show=False)
        for action in self.line_actions:
            action.setVisible(False)

        self.action_password_show.setEnabled(True)

        self.ui.name.show()
        self.ui.name_label.hide()
        self.ui.name.setText(credential.name)

        if credential.login:
            self.ui.username.setText(credential.login.decode(errors="replace"))
        else:
            self.ui.username.setText("")

        if credential.password:
            self.ui.password.setText(credential.password.decode(errors="replace"))
        else:
            self.ui.password.setText("")

        if credential.comment:
            self.ui.comment.setText(credential.comment.decode(errors="replace"))
        else:
            self.ui.comment.setText("")

        self.ui.name.setReadOnly(False)
        self.ui.username.setReadOnly(False)
        self.ui.password.setReadOnly(False)
        self.ui.comment.setReadOnly(False)

        self.ui.is_pin_protected.setChecked(credential.protected)
        self.ui.is_touch_protected.setChecked(credential.touch_required)

        self.ui.is_pin_protected.setEnabled(False)
        self.ui.is_touch_protected.setEnabled(True)

        self.hide_otp()
        self.ui.otp.show()
        self.ui.algorithm.show()

        # already existing otp requires confirmation to change
        if credential.otp:
            self.ui.otp.setReadOnly(True)
            self.ui.otp.setPlaceholderText("<hidden - click to edit>")
            self.ui.algorithm.setCurrentText(str(credential.otp))
            self.ui.algorithm.setEnabled(False)

            self.action_otp_copy.setVisible(False)
            self.action_otp_edit.setVisible(True)
            self.action_otp_gen.setVisible(False)
        # no otp there, just offer it as in add
        else:
            self.ui.otp.setText("")
            self.ui.otp.setReadOnly(False)
            self.ui.otp.setPlaceholderText("<empty>")
            self.ui.algorithm.setCurrentText(str(credential.otp))
            self.ui.algorithm.setEnabled(True)

    def act_enable_otp_edit(self) -> None:
        self.ui.otp.setReadOnly(False)
        self.ui.algorithm.setEnabled(True)
        self.ui.otp.setPlaceholderText("<empty>")
        self.ui.otp.setText("")
        self.active_credential.new_secret = True

    @Slot()
    def add_new_credential(self) -> None:
        if not self.data:
            return

        self.active_credential = None

        self.ui.credential_empty.hide()
        self.ui.credential_show.show()

        ###self.act_password_show(show=False)
        for action in self.line_actions:
            action.setVisible(False)
        self.action_password_show.setVisible(True)
        self.action_password_show.setEnabled(True)

        self.ui.name.show()
        self.ui.name_label.hide()
        self.ui.name.setText("")

        self.ui.otp.setText("")
        self.ui.username.setText("")
        self.ui.password.setText("")
        self.ui.comment.setText("")

        self.ui.name.setReadOnly(False)
        self.ui.otp.setReadOnly(False)
        self.ui.username.setReadOnly(False)
        self.ui.password.setReadOnly(False)
        self.ui.comment.setReadOnly(False)

        self.ui.algorithm.setCurrentText("None")
        self.ui.algorithm.setEnabled(True)

        self.ui.is_pin_protected.setChecked(False)
        self.ui.is_touch_protected.setChecked(False)

        self.ui.is_pin_protected.setEnabled(True)
        self.ui.is_touch_protected.setEnabled(True)

        self.ui.algorithm.show()
        self.ui.algorithm.setCurrentText("None")
        self.ui.algorithm.setEnabled(True)

        self.hide_otp()
        self.ui.otp.show()
        self.ui.otp.setReadOnly(False)

        self.ui.btn_abort.show()
        self.ui.btn_delete.hide()
        self.ui.btn_edit.hide()
        self.ui.btn_save.show()

        self.check_credential()

    @Slot()
    def check_credential(self) -> None:
        can_save = True

        otp_secret = self.ui.otp.text()

        algo = self.ui.algorithm.currentText()
        if algo != "None" and not is_base32(otp_secret):
            can_save = False

        if len(self.ui.name.text()) < 3:
            can_save = False

        self.ui.btn_save.setEnabled(can_save)

    def act_copy_line_edit(self, obj: QLineEdit):
        self.clipboard.setText(obj.text())

    def act_password_show(self) -> None:
        icon_show = self.get_qicon("visibility_FILL0_wght400_GRAD0_opsz24.svg")
        icon_hide = self.get_qicon("visibility_off_FILL0_wght400_GRAD0_opsz24.svg")

        if self.ui.password.echoMode() == QLineEdit.Normal:
            mode = QLineEdit.Password
            icon = icon_hide
        else:
            mode = QLineEdit.Normal
            icon = icon_show
        self.ui.password.setEchoMode(mode)
        self.action_password_show.setIcon(icon)

    def hide_credential(self) -> None:
        self.ui.credential_empty.show()
        self.ui.credential_show.hide()

    @Slot()
    def hide_otp(self) -> None:
        self.otp_timeout = None
        self.otp_timer.stop()
        self.ui.otp_timeout_progress.hide()
        self.ui.otp.clear()

    @Slot()
    def update_otp_timeout(self) -> None:
        self.ui.otp_timeout_progress.show()
        if not self.otp_timeout:
            return
        timeout = int((self.otp_timeout - datetime.now()).total_seconds())
        if timeout >= 0:
            self.ui.otp_timeout_progress.setValue(timeout)
        else:
            self.hide_otp()

    @Slot(QListWidgetItem, QListWidgetItem)
    def credential_changed(
        self, current: Optional[QListWidgetItem], old: Optional[QListWidgetItem]
    ) -> None:
        if current:
            credential = self.get_credential(current)

            # if credential was already loaded, don't do it again
            if not credential.loaded:
                self.next_credential_receiver = self.show_credential
                self.trigger_get_credential.emit(self.data, credential)
            else:
                self.show_credential(credential)

#            self.ui.buttonDelete.setEnabled(True)
        else:
            self.hide_credential()
#            self.ui.buttonDelete.setEnabled(False)

    @Slot()
    def delete_credential(self) -> None:
        assert self.data
        credential = self.get_current_credential()
        assert credential

        # TODO: ask for confirmation?

        self.trigger_delete_credential.emit(self.data, credential)

    @Slot()
    def save_credential(self) -> None:
        name = self.ui.name.text()
        username = self.ui.username.text()
        password = self.ui.password.text()
        comment = self.ui.comment.text()
        user_presence = self.ui.is_touch_protected.isChecked()
        pin_protected = self.ui.is_pin_protected.isChecked()
        kind_str = self.algorithm.currentText()

        if len(name) < 3:
            print("INSERT ERROR MESSAGE HERE - status bar?")
            return

        kind, otp_secret, secret = None, None, None
        # only save otp, if enabled
        if self.ui.algorithm.isEnabled():
            try:
                kind = OtpKind.from_str(kind_str)
                otp_secret = self.ui.otp.text()
                secret = parse_base32(otp_secret)
            except RuntimeError as e:
                pass

        cred = Credential(
            id=name.encode(),
            otp=kind,
            login=username.encode(),
            password=password.encode(),
            comment=comment.encode(),
            protected=pin_protected,
            touch_required=user_presence,
            new_secret=self.ui.algorithm.isEnabled() and self.ui.algorithm.currentText() != "None"
        )

        if self.active_credential is None:
            self.trigger_add_credential.emit(self.data, cred, secret)
        else:
            self.trigger_edit_credential.emit(self.data, cred, secret, self.active_credential.id)



    @Slot()
    def generate_otp(self) -> None:
        assert self.data
        credential = self.get_current_credential()
        assert credential
        self.trigger_generate_otp.emit(self.data, credential)

    @Slot(bool)
    def uncheck_checkbox(self, uncheck: bool) -> None:
        if uncheck:
            self.ui.is_protected.setChecked(False)
