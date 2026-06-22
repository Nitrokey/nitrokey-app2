import logging
from typing import Optional

from nitrokey.trussed import Model
from PySide6.QtCore import Qt, QThread, Signal, Slot
from PySide6.QtWidgets import QLineEdit, QListWidgetItem, QMessageBox, QWidget

from nitrokeyapp.common_ui import CommonUi
from nitrokeyapp.device_data import DeviceData
from nitrokeyapp.qt_utils_mix_in import QtUtilsMixIn
from nitrokeyapp.worker import Worker

from .data import Fido2Credential
from .worker import Fido2Worker

logger = logging.getLogger(__name__)


class Fido2Tab(QtUtilsMixIn, QWidget):
    busy_state_changed = Signal(bool)

    trigger_check_device = Signal(DeviceData)
    trigger_refresh_credentials = Signal(DeviceData)
    trigger_delete_credential = Signal(DeviceData, object)

    def __init__(self, parent: QWidget) -> None:
        QWidget.__init__(self, parent)
        QtUtilsMixIn.__init__(self)

        self.common_ui = CommonUi()

        self.worker_thread = QThread()
        self._worker = Fido2Worker(self.common_ui, parent)
        self._worker.moveToThread(self.worker_thread)
        self.worker_thread.start()

        self.trigger_check_device.connect(self._worker.check_device)
        self.trigger_refresh_credentials.connect(self._worker.refresh_credentials)
        self.trigger_delete_credential.connect(self._worker.delete_credential)

        self._worker.device_checked.connect(self.device_checked)
        self._worker.credentials_listed.connect(self.credentials_listed)
        self._worker.credential_deleted.connect(self.credential_deleted)

        self.data: Optional[DeviceData] = None
        self.active_credential: Optional[Fido2Credential] = None

        self.ui = self.load_ui("secrets_tab.ui", self)
        self._adapt_ui()
        self.refresh_icons()

        self.ui.btn_refresh.pressed.connect(self.refresh_credential_list)
        self.ui.secrets_list.currentItemChanged.connect(self.credential_changed)
        self.ui.secrets_list.itemClicked.connect(self.credential_clicked)
        self.ui.btn_delete.pressed.connect(self.delete_credential)

        self.reset()

    def refresh_icons(self) -> None:
        """re-resolve all themed icons, e.g. after a light/dark mode switch"""
        self.ui.btn_delete.setIcon(self.get_qicon("delete.svg"))
        self.ui.btn_refresh.setIcon(self.get_qicon("refresh.svg"))

    def _adapt_ui(self) -> None:
        # hide everything not used by the FIDO2 view
        self.ui.btn_add.hide()
        self.ui.btn_save.hide()
        self.ui.btn_edit.hide()
        self.ui.btn_abort.hide()
        self.ui.is_protected.hide()

        self.ui.name.hide()
        self.ui.algorithm_tab.hide()
        self.ui.otp.hide()
        self.ui.otp_timeout_progress.hide()
        self.ui.is_pin_protection_label.hide()
        self.ui.is_pin_protected.hide()
        self.ui.is_touch_protection_label.hide()
        self.ui.is_touch_protected.hide()

        # repurpose the username/password/comment fields for FIDO2 details (read-only)
        self.ui.username_label.setText("User:")
        self.ui.username.setReadOnly(True)
        self.ui.password_label.setText("E-Mail:")
        self.ui.password.setReadOnly(True)
        self.ui.password.setEchoMode(QLineEdit.EchoMode.Normal)
        self.ui.comment_label.setText("ID:")
        self.ui.comment.setReadOnly(True)

    @property
    def title(self) -> str:
        return "Passkeys"

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
        self.show_compatible(True)
        self.hide_credential()

    def show_compatible(self, compatible: bool) -> None:
        if compatible:
            self.ui.page_empty.hide()
            self.ui.page_compatible.show()
            self.ui.page_incompatible.hide()
        else:
            self.ui.page_empty.hide()
            self.ui.page_compatible.hide()
            self.ui.page_incompatible.show()

    def refresh(self, data: Optional[DeviceData], force: bool = False) -> None:
        if data is None:
            return
        if data.model not in (Model.NK3, Model.NKPK):
            self.show_compatible(False)
            return
        if data == self.data and not force:
            return
        self.data = data
        self._worker.pin_cache.clear()
        self.reset_ui()
        self.trigger_check_device.emit(self.data)

    @Slot(bool)
    def device_checked(self, compatible: bool) -> None:
        self.show_compatible(compatible)
        if compatible:
            self.refresh_credential_list()

    @Slot()
    def refresh_credential_list(self) -> None:
        if not self.data:
            return
        self.trigger_refresh_credentials.emit(self.data)

    @Slot(list)
    def credentials_listed(self, credentials: list) -> None:
        self.ui.secrets_list.clear()
        self.hide_credential()
        for credential in credentials:
            self.add_credential(credential)
        self.ui.secrets_list.sortItems()

    def add_credential(self, credential: Fido2Credential) -> QListWidgetItem:
        item = QListWidgetItem(credential.display)
        item.setIcon(self.get_qicon("lock.svg"))
        item.setData(Qt.ItemDataRole.UserRole, credential)
        self.ui.secrets_list.addItem(item)
        return item

    def get_credential(self, item: QListWidgetItem) -> Fido2Credential:
        data = item.data(Qt.ItemDataRole.UserRole)
        assert isinstance(data, Fido2Credential)
        return data

    def get_current_credential(self) -> Optional[Fido2Credential]:
        item = self.ui.secrets_list.currentItem()
        if not item:
            return None
        return self.get_credential(item)

    @Slot(QListWidgetItem)
    def credential_clicked(self, item: Optional[QListWidgetItem]) -> None:
        if not item:
            return
        self.show_credential(self.get_credential(item))

    @Slot(QListWidgetItem, QListWidgetItem)
    def credential_changed(
        self, current: Optional[QListWidgetItem], old: Optional[QListWidgetItem]
    ) -> None:
        if current:
            self.show_credential(self.get_credential(current))
        else:
            self.hide_credential()

    def show_credential(self, credential: Fido2Credential) -> None:
        self.active_credential = credential

        self.ui.credential_empty.hide()
        self.ui.credential_show.show()

        self.ui.name.hide()
        self.ui.name_label.show()
        self.ui.name_label.setText(credential.rp_label)

        self.ui.username.setText(credential.user_display_name or credential.user_name or "")
        self.ui.password.setText(credential.user_name or "")
        self.ui.comment.setText(credential.credential_id.hex())

        self.ui.btn_delete.show()

    def hide_credential(self) -> None:
        self.active_credential = None
        self.ui.credential_empty.show()
        self.ui.credential_show.hide()
        self.ui.btn_delete.hide()
        self.ui.secrets_list.clearSelection()

    @Slot()
    def delete_credential(self) -> None:
        if not self.data:
            return
        credential = self.get_current_credential()
        if not credential:
            return

        confirm = QMessageBox.question(
            self,
            "Delete Passkey",
            f"Permanently delete the passkey '{credential.display}' from this device?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return

        self.trigger_delete_credential.emit(self.data, credential)

    @Slot(object)
    def credential_deleted(self, credential: object) -> None:
        self.active_credential = None
        self.refresh_credential_list()
