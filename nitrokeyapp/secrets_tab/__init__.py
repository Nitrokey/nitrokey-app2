from datetime import datetime
from typing import Optional

from PyQt5.QtCore import Qt, QThread, QTimer, pyqtSignal, pyqtSlot
from PyQt5.QtGui import QGuiApplication, QIcon
from PyQt5.QtWidgets import QDialog, QListWidgetItem, QWidget

from nitrokeyapp.add_secret_dialog import AddSecretDialog
from nitrokeyapp.device_data import DeviceData
from nitrokeyapp.ui.secrets_tab import Ui_SecretsTab
from nitrokeyapp.worker import Worker

from .data import Credential, OtpData
from .worker import SecretsWorker

# TODO:
# - logging
# - handle expired OTP
# - add OTP copy to clipboard
# - investigate layout during OTP display
# - disable UI during operations
# - confirm new PIN


class SecretsTab(QWidget):
    # standard UI
    busy_state_changed = pyqtSignal(bool)
    error = pyqtSignal(str)
    start_touch = pyqtSignal()
    stop_touch = pyqtSignal()

    # worker triggers
    trigger_add_credential = pyqtSignal(DeviceData, Credential, bytes)
    trigger_check_device = pyqtSignal(DeviceData)
    trigger_delete_credential = pyqtSignal(DeviceData, Credential)
    trigger_generate_otp = pyqtSignal(DeviceData, Credential)
    trigger_refresh_credentials = pyqtSignal(DeviceData, bool)

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)

        self.worker_thread = QThread()
        self._worker = SecretsWorker(self)
        self._worker.moveToThread(self.worker_thread)
        self.worker_thread.start()

        self.trigger_add_credential.connect(self._worker.add_credential)
        self.trigger_check_device.connect(self._worker.check_device)
        self.trigger_delete_credential.connect(self._worker.delete_credential)
        self.trigger_generate_otp.connect(self._worker.generate_otp)
        self.trigger_refresh_credentials.connect(self._worker.refresh_credentials)

        self._worker.credential_added.connect(self.credential_added)
        self._worker.credential_deleted.connect(self.credential_deleted)
        self._worker.credentials_listed.connect(self.credentials_listed)
        self._worker.device_checked.connect(self.device_checked)
        self._worker.otp_generated.connect(self.otp_generated)

        self.data: Optional[DeviceData] = None
        self.pin: Optional[str] = None
        self.active_credential: Optional[Credential] = None

        self.otp_timeout: Optional[datetime] = None
        self.otp_timer = QTimer()
        self.otp_timer.timeout.connect(self.update_otp_timeout)
        self.otp_timer.setInterval(1000)

        self.clipboard = QGuiApplication.clipboard()
        self.originalText = self.clipboard.text()

        self.ui = Ui_SecretsTab()
        self.ui.setupUi(self)

        labels = [
            self.ui.labelName,
            self.ui.labelAlgorithm,
            self.ui.labelOtp,
        ]
        max_width = max([label.width() for label in labels])
        for label in labels:
            label.setMinimumWidth(max_width)

        self.ui.buttonAdd.pressed.connect(self.add_new_credential)
        self.ui.buttonDelete.pressed.connect(self.delete_credential)
        self.ui.buttonRefresh.pressed.connect(self.refresh_credential_list)
        self.ui.checkBoxProtected.stateChanged.connect(self.refresh_credential_list)
        self.ui.pushButtonOtpCopyToClipbord.pressed.connect(self.copy_to_clipboard)
        self.ui.pushButtonOtpGenerate.pressed.connect(self.generate_otp)
        self.ui.secretsList.currentItemChanged.connect(self.credential_changed)

        self.reset()

    @property
    def title(self) -> str:
        return "Passwords"

    @property
    def widget(self) -> QWidget:
        return self

    @property
    def worker(self) -> Optional[Worker]:
        return self._worker

    def reset(self) -> None:
        self.data = None
        self.pin = None

        self.reset_ui()

    def reset_ui(self) -> None:
        self.ui.stackedWidget.setCurrentWidget(self.ui.pageEmpty)
        self.ui.secretsList.clear()
        self.ui.credentialWidget.hide()
        self.ui.buttonDelete.setEnabled(False)

        self.hide_otp()

    def refresh(self, data: DeviceData) -> None:
        if data == self.data:
            return
        self.data = data
        self.pin = None

        self.reset_ui()
        self.trigger_check_device.emit(data)

    @pyqtSlot(bool)
    def device_checked(self, compatible: bool) -> None:
        self.show_secrets(compatible)
        if compatible:
            self.refresh_credential_list()

    @pyqtSlot()
    def refresh_credential_list(self) -> None:
        assert self.data

        if not self.active_credential:
            current = self.get_current_credential()
            if current:
                self.active_credential = current

        pin_protected = self.ui.checkBoxProtected.isChecked()

        self.trigger_refresh_credentials.emit(self.data, pin_protected)

    @pyqtSlot(Credential)
    def credential_added(self, credential: Credential) -> None:
        self.active_credential = credential
        if credential.protected:
            self.ui.checkBoxProtected.setChecked(True)

        self.refresh_credential_list()

    @pyqtSlot(Credential)
    def credential_deleted(self, credential: Credential) -> None:
        self.refresh_credential_list()

    @pyqtSlot(list)
    def credentials_listed(self, credentials: list[Credential]) -> None:
        self.reset_ui()
        self.show_secrets(True)

        active_item = None
        for credential in credentials:
            item = self.add_credential(credential)
            if self.active_credential and credential.id == self.active_credential.id:
                active_item = item
        self.ui.secretsList.sortItems()
        if active_item:
            self.ui.secretsList.setCurrentItem(active_item)

    @pyqtSlot(OtpData)
    def otp_generated(self, data: OtpData) -> None:
        self.ui.lineEditOtp.setText(data.otp)
        self.data_otp = data.otp

        if data.validity:
            start, end = data.validity
            period = int((end - start).total_seconds())
            self.ui.progressBarOtpTimeout.setMaximum(period)

            self.otp_timeout = end
            self.otp_timer.start()
            self.update_otp_timeout()

        self.ui.pushButtonOtpGenerate.setVisible(data.validity is None)
        self.ui.progressBarOtpTimeout.setVisible(data.validity is not None)
        self.ui.labelOtp.show()
        self.ui.lineEditOtp.show()

    def copy_to_clipboard(self) -> None:
        self.clipboard.setText(self.data_otp)

    def add_credential(self, credential: Credential) -> QListWidgetItem:
        icon = (
            "lock_FILL0_wght500_GRAD0_opsz40"
            if credential.protected
            else "lock_open_FILL0_wght500_GRAD0_opsz40"
        )
        item = QListWidgetItem(credential.name)
        item.setIcon(QIcon(f":/icons/{icon}.svg"))
        item.setData(Qt.ItemDataRole.UserRole, credential)
        self.ui.secretsList.addItem(item)
        return item

    def get_credential(self, item: QListWidgetItem) -> Credential:
        data = item.data(Qt.ItemDataRole.UserRole)
        assert isinstance(data, Credential)
        return data

    def get_current_credential(self) -> Optional[Credential]:
        item = self.ui.secretsList.currentItem()
        if not item:
            return None
        return self.get_credential(item)

    def show_credential(self, credential: Credential) -> None:
        # TODO: show other credential kind if set
        if credential.otp:
            self.hide_otp()
            self.ui.groupBoxOtp.show()
            self.ui.lineEditName.setText(credential.name)
            self.ui.checkBoxPinProtection.setChecked(credential.protected)
            self.ui.lineEditOtpAlgorithm.setText(str(credential.otp))
        else:
            self.ui.groupBoxOtp.hide()
        self.update_otp_generation(credential)
        self.ui.credentialWidget.show()

    def hide_credential(self) -> None:
        self.ui.credentialWidget.hide()

    def show_secrets(self, show: bool) -> None:
        widget = self.ui.pageCompatible if show else self.ui.pageIncompatible
        self.ui.stackedWidget.setCurrentWidget(widget)

    @pyqtSlot()
    def hide_otp(self) -> None:
        self.otp_timeout = None
        self.otp_timer.stop()
        self.ui.progressBarOtpTimeout.hide()
        self.ui.labelOtp.hide()
        self.ui.lineEditOtp.hide()
        self.ui.pushButtonOtpCopyToClipbord.hide()

        credential = self.get_current_credential()
        self.update_otp_generation(credential)

    def update_otp_generation(self, credential: Optional[Credential]) -> None:
        visible = credential is not None and credential.otp is not None
        self.ui.pushButtonOtpGenerate.setVisible(visible)

    @pyqtSlot()
    def update_otp_timeout(self) -> None:
        if not self.otp_timeout:
            return
        timeout = int((self.otp_timeout - datetime.now()).total_seconds())
        if timeout >= 0:
            self.ui.progressBarOtpTimeout.setValue(timeout)
            self.ui.pushButtonOtpCopyToClipbord.show()
        else:
            self.hide_otp()

    @pyqtSlot(QListWidgetItem, QListWidgetItem)
    def credential_changed(
        self, current: Optional[QListWidgetItem], old: Optional[QListWidgetItem]
    ) -> None:
        if current:
            credential = self.get_credential(current)
            self.show_credential(credential)
            self.ui.buttonDelete.setEnabled(True)
        else:
            self.hide_credential()
            self.ui.buttonDelete.setEnabled(False)

    @pyqtSlot()
    def delete_credential(self) -> None:
        assert self.data
        credential = self.get_current_credential()
        assert credential

        # TODO: ask for confirmation?

        self.trigger_delete_credential.emit(self.data, credential)

    @pyqtSlot()
    def add_new_credential(self) -> None:
        if not self.data:
            return

        dialog = AddSecretDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            credential = dialog.credential()
            secret = dialog.secret()
            self.trigger_add_credential.emit(self.data, credential, secret)

    @pyqtSlot()
    def generate_otp(self) -> None:
        assert self.data
        credential = self.get_current_credential()
        assert credential

        self.trigger_generate_otp.emit(self.data, credential)
