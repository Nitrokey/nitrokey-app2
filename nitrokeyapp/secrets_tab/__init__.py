import binascii
import logging
from base64 import b32decode
from datetime import datetime
from enum import Enum
from typing import Callable, Optional

from PySide6.QtCore import Qt, QThread, QTimer, Signal, Slot
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import QLineEdit, QListWidgetItem, QWidget

from nitrokeyapp.device_data import DeviceData
from nitrokeyapp.information_box import InfoBox
from nitrokeyapp.qt_utils_mix_in import QtUtilsMixIn
from nitrokeyapp.worker import Worker

from .data import Credential, OtpData, OtpKind
from .worker import SecretsWorker

# TODO:
# - handle expired OTP
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
    error = Signal(str, Exception)
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

    def __init__(self, info_box: InfoBox, parent: Optional[QWidget] = None) -> None:
        QWidget.__init__(self, parent)
        QtUtilsMixIn.__init__(self)

        self.info_box = info_box

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

        self._worker.pin_cache.pin_cleared.connect(
            lambda: (
                self.info_box.set_pin_icon(pin_cached=False),
                self.uncheck_checkbox(True),
            )
        )
        self._worker.pin_cache.pin_cached.connect(
            lambda: self.info_box.set_pin_icon(pin_cached=True)
        )
        self.info_box.pin_icon.pressed.connect(self._worker.pin_cache.clear)

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
        self.active_credential: Optional[Credential] = None

        self.otp_timeout: Optional[datetime] = None
        self.otp_timer = QTimer()
        self.otp_timer.timeout.connect(self.update_otp_timeout)
        self.otp_timer.setInterval(1000)

        self.clipboard = QGuiApplication.clipboard()
        self.originalText = self.clipboard.text()

        # self.ui === self -> this tricks mypy due to monkey-patching self
        self.ui = self.load_ui("secrets_tab.ui", self)

        icon_copy = self.get_qicon("content_copy.svg")
        icon_refresh = self.get_qicon("OTP_generate.svg")
        icon_edit = self.get_qicon("edit.svg")
        icon_visibility = self.get_qicon("visibility_off.svg")

        loc = QLineEdit.ActionPosition.TrailingPosition
        self.action_username_copy = self.ui.username.addAction(icon_copy, loc)
        self.action_username_copy.triggered.connect(
            lambda: self.act_copy_line_edit(self.ui.username)
        )

        self.action_password_copy = self.ui.password.addAction(icon_copy, loc)
        self.action_password_copy.triggered.connect(
            lambda: self.act_copy_line_edit(self.ui.password)
        )

        self.action_password_show = self.ui.password.addAction(icon_visibility, loc)
        self.action_password_show.triggered.connect(self.act_password_show)

        self.action_comment_copy = self.ui.comment.addAction(icon_copy, loc)
        self.action_comment_copy.triggered.connect(
            lambda: self.act_copy_line_edit(self.ui.comment)
        )

        self.action_otp_copy = self.ui.otp.addAction(icon_copy, loc)
        self.action_otp_copy.triggered.connect(
            lambda: self.act_copy_line_edit(self.ui.otp)
        )

        self.action_otp_gen = self.ui.otp.addAction(icon_refresh, loc)
        self.action_otp_gen.triggered.connect(self.generate_otp)

        self.action_otp_edit = self.ui.otp.addAction(icon_edit, loc)
        self.action_otp_edit.triggered.connect(self.act_enable_otp_edit)

        self.line_actions = [
            self.action_username_copy,
            self.action_password_copy,
            self.action_password_show,
            self.action_comment_copy,
            self.action_otp_copy,
            self.action_otp_edit,
            self.action_otp_gen,
        ]
        self.line2copy_action = {
            self.ui.username: self.action_username_copy,
            self.ui.password: self.action_password_copy,
            self.ui.comment: self.action_comment_copy,
            self.ui.otp: self.action_otp_copy,
        }

        self.ui.btn_add.pressed.connect(self.add_new_credential)
        self.ui.btn_abort.pressed.connect(lambda: self.show_secrets(True))
        self.ui.btn_save.pressed.connect(self.save_credential)
        self.ui.btn_edit.pressed.connect(self.prepare_edit_credential)

        self.ui.name.textChanged.connect(self.check_credential)
        self.ui.otp.textChanged.connect(self.check_credential)
        self.ui.select_algorithm.currentIndexChanged.connect(self.check_credential)

        self.ui.btn_refresh.pressed.connect(self.refresh_credential_list)
        self.ui.is_protected.stateChanged.connect(self.refresh_credential_list)
        self.ui.secrets_list.currentItemChanged.connect(self.credential_changed)
        self.ui.secrets_list.itemClicked.connect(self.credential_clicked)

        self.ui.btn_delete.pressed.connect(self.delete_credential)

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
        self.active_credential = None

        self.reset_ui()

    def reset_ui(self) -> None:
        self.ui.secrets_list.clear()

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
        icon = "lock" if credential.protected else "lock_open"
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

        self.set_password_show(show=False)
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
        self.ui.algorithm_tab.setCurrentIndex(1)

        if credential.otp or credential.other:
            self.ui.algorithm_tab.show()
            self.ui.algorithm_edit.hide()
            self.ui.algorithm_show.show()

            self.ui.otp.show()
            self.ui.otp.setReadOnly(True)
            self.ui.algorithm.setText(str(credential.otp or credential.other) + ":")
            self.ui.otp.setPlaceholderText("<hidden>")

            if credential.otp:
                self.action_otp_copy.setVisible(True)
                self.action_otp_gen.setVisible(True)
            else:
                self.action_otp_copy.setVisible(False)
                self.action_otp_gen.setVisible(False)

            self.action_otp_edit.setVisible(False)
        else:
            self.ui.algorithm_tab.hide()
            self.ui.algorithm_show.hide()
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

        self.set_password_show(show=False)
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

        self.ui.algorithm_tab.show()
        self.ui.algorithm_tab.setCurrentIndex(0)
        self.ui.algorithm_show.hide()
        self.ui.algorithm_edit.show()
        self.ui.select_algorithm.show()
        self.ui.otp.show()

        # already existing otp requires confirmation to change
        if credential.otp or credential.other:
            self.ui.otp.setReadOnly(True)

            self.ui.select_algorithm.setCurrentText(
                str(credential.otp or credential.other)
            )
            self.ui.select_algorithm.setEnabled(False)

            self.action_otp_copy.setVisible(False)
            self.action_otp_gen.setVisible(False)
            if credential.otp:
                self.action_otp_edit.setVisible(True)
                self.ui.otp.setPlaceholderText("<hidden - click to edit>")
            else:
                self.ui.algorithm_show.show()
                self.ui.algorithm_edit.hide()
                self.ui.algorithm.setText(str(credential.otp or credential.other) + ":")
                self.action_otp_edit.setVisible(False)
                self.ui.otp.setPlaceholderText("<cannot edit>")

        # no otp there, just offer it as in add
        else:
            self.ui.otp.setText("")
            self.ui.otp.setReadOnly(False)
            self.ui.otp.setPlaceholderText("<empty>")
            self.ui.select_algorithm.setCurrentText(str(credential.otp))
            self.ui.select_algorithm.setEnabled(True)

        self.check_credential()

    def act_enable_otp_edit(self) -> None:
        assert self.active_credential
        self.active_credential.new_secret = True

        self.ui.otp.setReadOnly(False)
        self.ui.select_algorithm.setEnabled(True)
        self.ui.otp.setPlaceholderText("<empty>")
        self.ui.otp.setText("")

        self.check_credential()

    @Slot()
    def add_new_credential(self) -> None:
        if not self.data:
            return

        self.active_credential = None

        self.ui.credential_empty.hide()
        self.ui.credential_show.show()

        self.set_password_show(show=False)
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

        self.ui.is_pin_protected.setChecked(False)
        self.ui.is_touch_protected.setChecked(False)

        self.ui.is_pin_protected.setEnabled(True)
        self.ui.is_touch_protected.setEnabled(True)

        self.hide_otp()
        self.ui.otp.show()
        self.ui.otp.setReadOnly(False)

        self.ui.algorithm_tab.show()
        self.ui.algorithm_tab.setCurrentIndex(0)
        self.ui.algorithm_edit.show()
        self.ui.algorithm_show.hide()

        self.ui.select_algorithm.show()
        self.ui.select_algorithm.setCurrentText("None")
        self.ui.select_algorithm.setEnabled(True)

        self.ui.btn_abort.show()
        self.ui.btn_delete.hide()
        self.ui.btn_edit.hide()
        self.ui.btn_save.show()

        self.check_credential()

    @Slot()
    def check_credential(self) -> None:
        can_save = True

        otp_secret = self.ui.otp.text()

        algo = self.ui.select_algorithm.currentText()
        if self.ui.select_algorithm.isEnabled():
            if algo != "None" and not is_base32(otp_secret):
                can_save = False

            if algo != "None" and len(otp_secret) < 1:
                can_save = False

        if len(self.ui.name.text()) < 3:
            can_save = False

        self.ui.btn_save.setEnabled(can_save)

    def act_copy_line_edit(self, obj: QLineEdit) -> None:
        self.clipboard.setText(obj.text())
        self.info_box.set_status("contents copied to clipboard")
        self.line2copy_action[obj].setIcon(self.get_qicon("done.svg"))
        QTimer.singleShot(
            5000,
            lambda: self.line2copy_action[obj].setIcon(
                self.get_qicon("content_copy.svg")
            ),
        )

    def act_password_show(self) -> None:
        self.set_password_show(self.ui.password.echoMode() == QLineEdit.Password)  # type: ignore [attr-defined]

    def set_password_show(self, show: bool = True) -> None:
        icon_show = self.get_qicon("visibility.svg")
        icon_hide = self.get_qicon("visibility_off.svg")
        icon = icon_show if show else icon_hide
        mode = QLineEdit.Normal if show else QLineEdit.Password  # type: ignore [attr-defined]
        self.ui.password.setEchoMode(mode)
        self.action_password_show.setIcon(icon)

    def hide_credential(self) -> None:
        self.ui.credential_empty.show()
        self.ui.credential_show.hide()

        self.ui.btn_abort.hide()
        self.ui.btn_delete.hide()
        self.ui.btn_edit.hide()
        self.ui.btn_save.hide()

        self.ui.secrets_list.clearSelection()
        self.active_credential = None

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

    @Slot(QListWidgetItem)
    def credential_clicked(self, item: Optional[QListWidgetItem]) -> None:
        if self.data:
            assert item
            credential = self.get_credential(item)
            # if credential was already loaded, don't do it again
            if not credential.loaded:
                self.next_credential_receiver = self.show_credential
                self.trigger_get_credential.emit(self.data, credential)
            else:
                self.show_credential(credential)

    @Slot(QListWidgetItem, QListWidgetItem)
    def credential_changed(
        self, current: Optional[QListWidgetItem], old: Optional[QListWidgetItem]
    ) -> None:
        if current and self.data:
            pass
        else:
            self.hide_credential()

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
        kind_str = self.ui.select_algorithm.currentText()

        if len(name) < 3:
            print("INSERT ERROR MESSAGE HERE - status bar?")
            return

        kind, otp_secret, secret = None, None, None
        # only save otp, if enabled
        if self.ui.select_algorithm.isEnabled():
            try:
                kind = OtpKind.from_str(kind_str)
                otp_secret = self.ui.otp.text()
                secret = parse_base32(otp_secret)
            except RuntimeError:
                pass

        cred = Credential(
            id=name.encode(),
            otp=kind,
            login=username.encode(),
            password=password.encode(),
            comment=comment.encode(),
            protected=pin_protected,
            touch_required=user_presence,
            new_secret=self.ui.select_algorithm.isEnabled()
            and self.ui.select_algorithm.currentText() != "None",
        )

        if self.active_credential is None:
            self.trigger_add_credential.emit(self.data, cred, secret)
        else:
            self.trigger_edit_credential.emit(
                self.data, cred, secret, self.active_credential.id
            )

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
