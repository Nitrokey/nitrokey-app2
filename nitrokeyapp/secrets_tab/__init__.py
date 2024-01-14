from datetime import datetime
from typing import Optional
import binascii
from base64 import b32decode
from enum import Enum

from PySide6.QtCore import Qt, QThread, QTimer, Signal, Slot
from PySide6.QtGui import QGuiApplication, QIcon, QAction
from PySide6.QtWidgets import QDialog, QListWidgetItem, QWidget, QLineEdit

from nitrokeyapp.add_secret_dialog import AddSecretDialog
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

        self._worker.credential_added.connect(self.credential_added)
        self._worker.credential_deleted.connect(self.credential_deleted)
        self._worker.credentials_listed.connect(self.credentials_listed)
        self._worker.device_checked.connect(self.device_checked)
        self._worker.otp_generated.connect(self.otp_generated)
        self._worker.uncheck_checkbox.connect(self.uncheck_checkbox)
        self._worker.received_credential.connect(self.show_credential)

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

        cp_username = self.ui.username.addAction(QIcon("nitrokeyapp/ui/icons/content_copy_FILL0_wght400_GRAD0_opsz24.svg"), QLineEdit.ActionPosition.TrailingPosition)
        cp_username.triggered.connect(self.copy_username)

        cp_password = self.ui.password.addAction(QIcon("nitrokeyapp/ui/icons/content_copy_FILL0_wght400_GRAD0_opsz24.svg"), QLineEdit.ActionPosition.TrailingPosition)
        cp_password.triggered.connect(self.copy_password)

        show_password = self.ui.password.addAction(QIcon("nitrokeyapp/ui/icons/visibility_FILL0_wght400_GRAD0_opsz24.svg"), QLineEdit.ActionPosition.TrailingPosition)
        show_password.triggered.connect(self.passwords_show)

        cp_comment = self.ui.comment.addAction(QIcon("nitrokeyapp/ui/icons/content_copy_FILL0_wght400_GRAD0_opsz24.svg"), QLineEdit.ActionPosition.TrailingPosition)
        cp_comment.triggered.connect(self.copy_comment)

        cp_otp = self.ui.otp.addAction(QIcon("nitrokeyapp/ui/icons/content_copy_FILL0_wght400_GRAD0_opsz24.svg"), QLineEdit.ActionPosition.TrailingPosition)
        cp_otp.triggered.connect(self.copy_otp)

        gen_otp = self.ui.otp.addAction(QIcon("nitrokeyapp/ui/icons/refresh_FILL0_wght400_GRAD0_opsz24.svg"), QLineEdit.ActionPosition.TrailingPosition)
        gen_otp.triggered.connect(self.generate_otp)


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

        self.ui.credential_name.textChanged.connect(self.check_credential)
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
        self.refresh_credential_list()

    @Slot(list)
    def credentials_listed(self, credentials: list[Credential]) -> None:
        self.reset_ui()
        self.show_secrets(True)

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

#        self.ui.pushButtonOtpGenerate.setVisible(data.validity is None)
        self.ui.otp_timeout_progress.setVisible(data.validity is not None)
        self.ui.otp.show()

    def copy_otp(self) -> None:
        self.clipboard.setText(self.data_otp)

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

    @Slot(Credential)
    def show_credential(self, credential: Credential) -> None:
        # cache loaded credential into original credential in ListView
        item = self.ui.secrets_list.currentItem()
        item.setData(Qt.ItemDataRole.UserRole, credential)

        self.ui.credential_empty.hide()
        self.ui.credential_show.show()

        self.ui.btn_abort.hide()
        self.ui.btn_save.hide()
        self.ui.btn_delete.hide()
        self.ui.btn_edit.show()

        self.ui.credential_name.setText(credential.name)
        self.ui.username.setText(credential.login)
        self.ui.password.setText(credential.password)
        self.ui.comment.setText(credential.comment)

        self.ui.credential_name.setReadOnly(True)
        self.ui.username.setReadOnly(True)
        self.ui.password.setReadOnly(True)
        self.ui.comment.setReadOnly(True)

        self.ui.is_pin_protected.setChecked(credential.protected)
        self.ui.is_touch_protected.setChecked(credential.touch_required)

        self.c_username = credential.login
        self.c_password = credential.password
        self.c_comment = credential.comment

        self.hide_otp()
        if credential.otp:
            self.ui.otp.show()
            self.ui.algorithm.show()
            self.ui.algorithm.setCurrentText(str(credential.otp))
            self.ui.algorithm.setEnabled(False)
        else:
            self.ui.algorithm.hide()
            self.ui.otp.hide()
        self.update_otp_generation(credential)

    def copy_username(self) -> None:
        self.clipboard.setText(self.c_username)

    def copy_password(self) -> None:
        self.clipboard.setText(self.c_password)

    def copy_comment(self) -> None:
        self.clipboard.setText(self.c_comment)

    def passwords_show(self) -> None:
#        if eye:
            self.ui.password.setEchoMode(QLineEdit.Normal)
            self.ui.password.findChildren(QAction)[1].setIcon(QIcon("nitrokeyapp/ui/icons/visibility_off_FILL0_wght400_GRAD0_opsz24.svg"))
#        else:
#            self.ui.password.setEchoMode(QLineEdit.Passwords)
#            self.ui.password.findChildren(QAction)[1].setIcon(QIcon("nitrokeyapp/ui/icons/visibility_FILL0_wght400_GRAD0_opsz24.svg"))

    def hide_credential(self) -> None:
        self.ui.credential_empty.show()
        self.ui.credential_show.hide()

    @Slot()
    def hide_otp(self) -> None:
        self.otp_timeout = None
        self.otp_timer.stop()
        self.ui.otp_timeout_progress.hide()
        self.ui.otp.clear()

        credential = self.get_current_credential()
        self.update_otp_generation(credential)

    def update_otp_generation(self, credential: Optional[Credential]) -> None:
        visible = credential is not None and credential.otp is not None

    @Slot()
    def update_otp_timeout(self) -> None:
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
    def add_new_credential(self) -> None:
        if not self.data:
            return

        #dialog = AddSecretDialog(self)
        #if dialog.exec() == QDialog.DialogCode.Accepted:
        #    credential = dialog.credential()
        #    secret = dialog.secret()
        #    self.trigger_add_credential.emit(self.data, credential, secret)

        ui = self.ui

        ui.credential_empty.hide()
        ui.credential_show.show()

        ui.credential_name.setText("")
        ui.otp.setText("")
        ui.username.setText("")
        ui.password.setText("")
        ui.comment.setText("")

        ui.credential_name.setReadOnly(False)
        ui.otp.setReadOnly(False)
        ui.username.setReadOnly(False)
        ui.password.setReadOnly(False)
        ui.comment.setReadOnly(False)

        ui.algorithm.setCurrentText("None")
        ui.algorithm.setEnabled(True)

        ui.is_pin_protected.setChecked(False)
        ui.is_touch_protected.setChecked(False)

        ui.is_pin_protected.setEnabled(True)
        ui.is_touch_protected.setEnabled(True)

        ui.algorithm.show()
        ui.algorithm.setCurrentText("None")
        ui.algorithm.setEnabled(True)

        self.hide_otp()
        ui.otp.show()
        ui.otp.setReadOnly(False)

        ui.btn_abort.show()
        ui.btn_delete.hide()
        ui.btn_edit.hide()
        ui.btn_save.show()

        self.check_credential()

    @Slot()
    def check_credential(self) -> None:
        can_save = True

        otp_secret = self.ui.otp.text()

        algo = self.ui.algorithm.currentText()
        if algo != "None" and not is_base32(otp_secret):
            can_save = False

        if len(self.ui.credential_name.text()) < 3:
            can_save = False

        self.ui.btn_save.setEnabled(can_save)

    @Slot()
    def save_credential(self) -> None:
        name = self.ui.credential_name.text()
        username = self.ui.username.text()
        password = self.ui.password.text()
        comment = self.ui.comment.text()
        user_presence = self.ui.is_pin_protected.isChecked()
        pin_protected = self.ui.is_touch_protected.isChecked()
        kind_str = self.algorithm.currentText()

        if len(name) < 3:
            print("INSERT ERROR MESSAGE HERE - status bar?")
            return

        kind, otp_secret, secret = None, None, None
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
        )

        self.trigger_add_credential.emit(self.data, cred, secret)



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
