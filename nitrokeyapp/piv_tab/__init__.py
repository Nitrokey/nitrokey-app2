# Copyright 2026 Nitrokey Developers
#
# Licensed under the Apache License, Version 2.0, <LICENSE-APACHE or
# http://apache.org/licenses/LICENSE-2.0> or the MIT license <LICENSE-MIT or
# http://opensource.org/licenses/MIT>, at your option. This file may not be
# copied, modified, or distributed except according to those terms.

import logging
from typing import Optional

from PySide6.QtCore import Qt, QThread, Signal, Slot
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QInputDialog,
    QLineEdit,
    QListWidgetItem,
    QMessageBox,
    QComboBox,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from nitrokeyapp.common_ui import CommonUi
from nitrokeyapp.device_data import DeviceData
from nitrokeyapp.qt_utils_mix_in import QtUtilsMixIn
from nitrokeyapp.worker import Worker

from .data import DEFAULT_ADMIN_KEY, PivSlotInfo
from .worker import PivWorker

logger = logging.getLogger(__name__)

ALGO_CHOICES = [
    ("ECC P-256", b"\x11"),
    ("ECC P-384", b"\x14"),
    ("RSA 2048", b"\x07"),
]


class PivTab(QtUtilsMixIn, QWidget):
    trigger_check_device = Signal(DeviceData)
    trigger_get_slots = Signal(DeviceData)
    trigger_change_pin = Signal(DeviceData, str, str)
    trigger_change_puk = Signal(DeviceData, str, str)
    trigger_reset_piv = Signal(DeviceData)
    trigger_import_p12 = Signal(DeviceData, str, bytes, object, bytes)
    trigger_generate_key = Signal(DeviceData, str, bytes)

    def __init__(self, parent: QWidget) -> None:
        QWidget.__init__(self, parent)
        QtUtilsMixIn.__init__(self)

        self.common_ui = CommonUi()
        self.data: Optional[DeviceData] = None
        self.active_slot: Optional[PivSlotInfo] = None

        self.worker_thread = QThread()
        self._worker = PivWorker(self.common_ui, parent)
        self._worker.moveToThread(self.worker_thread)
        self.worker_thread.start()

        # outgoing
        self.trigger_check_device.connect(self._worker.check_device)
        self.trigger_get_slots.connect(self._worker.get_slots)
        self.trigger_change_pin.connect(self._worker.change_pin)
        self.trigger_change_puk.connect(self._worker.change_puk)
        self.trigger_reset_piv.connect(self._worker.reset_piv)
        self.trigger_import_p12.connect(self._worker.import_p12)
        self.trigger_generate_key.connect(self._worker.generate_key)

        # incoming
        self._worker.device_checked.connect(self.device_checked)
        self._worker.slots_listed.connect(self.slots_listed)
        self._worker.pin_changed.connect(self._refresh_after_change)
        self._worker.puk_changed.connect(self._refresh_after_change)
        self._worker.piv_reset.connect(self._refresh_after_change)
        self._worker.import_done.connect(self._refresh_after_change)
        self._worker.generate_done.connect(self._on_generate_done)

        self.ui = self.load_ui("piv_tab.ui", self)

        self.ui.slots_list.currentItemChanged.connect(self._slot_selection_changed)
        self.ui.btn_refresh.pressed.connect(self._do_refresh)
        self.ui.btn_change_pin.pressed.connect(self._prompt_change_pin)
        self.ui.btn_change_puk.pressed.connect(self._prompt_change_puk)
        self.ui.btn_reset.pressed.connect(self._prompt_reset)
        self.ui.btn_generate_key.pressed.connect(self._prompt_generate_key)
        self.ui.btn_import_p12.pressed.connect(self._prompt_import_p12)

        self.reset()

    # ── DeviceView protocol ───────────────────────────────────────────────────

    @property
    def title(self) -> str:
        return "PIV"

    @property
    def widget(self) -> QWidget:
        return self.ui

    @property
    def worker(self) -> Optional[Worker]:
        return self._worker

    def reset(self) -> None:
        self.data = None
        self.active_slot = None
        self._reset_ui()
        self.ui.piv_stack.setCurrentWidget(self.ui.page_incompatible)

    def refresh(self, data: Optional[DeviceData], force: bool = False) -> None:
        if data is None:
            return
        if data == self.data and not force:
            return
        self.data = data
        self._worker.pin_cache.clear()
        self._reset_ui()
        self.trigger_check_device.emit(self.data)

    # ── UI state helpers ──────────────────────────────────────────────────────

    def _reset_ui(self) -> None:
        self.ui.slots_list.clear()
        self.active_slot = None
        self.ui.slot_stack.setCurrentWidget(self.ui.slot_empty)

    def _show_compatible(self, compatible: bool) -> None:
        if compatible:
            self.ui.piv_stack.setCurrentWidget(self.ui.page_compatible)
        else:
            self.ui.piv_stack.setCurrentWidget(self.ui.page_incompatible)

    def _show_slot(self, slot: PivSlotInfo) -> None:
        self.active_slot = slot
        self.ui.slot_headline.setText(slot.display_name)

        if slot.has_cert:
            cert = slot.cert
            assert cert is not None
            self.ui.slot_status_label.setText("Certificate present")
            self.ui.cert_section.show()
            self.ui.subject_value.setText(cert.subject)
            self.ui.issuer_value.setText(cert.issuer)
            self.ui.serial_value.setText(cert.serial)
            self.ui.validity_value.setText(f"{cert.not_before} – {cert.not_after}")
        else:
            self.ui.slot_status_label.setText("Empty")
            self.ui.cert_section.hide()

        self.ui.slot_stack.setCurrentWidget(self.ui.slot_show)

    # ── Slot signals ──────────────────────────────────────────────────────────

    @Slot(bool)
    def device_checked(self, compatible: bool) -> None:
        if self.data is None:
            return
        self._show_compatible(compatible)
        if compatible:
            self._do_refresh()

    @Slot(list)
    def slots_listed(self, slots: list) -> None:
        if self.data is None:
            return
        self.ui.slots_list.clear()
        self.active_slot = None
        self.ui.slot_stack.setCurrentWidget(self.ui.slot_empty)

        for slot in slots:
            icon_name = "lock.svg" if slot.has_cert else "lock_open.svg"
            item = QListWidgetItem(self.get_qicon(icon_name), slot.display_name)
            item.setData(Qt.ItemDataRole.UserRole, slot)
            self.ui.slots_list.addItem(item)

    @Slot()
    def _refresh_after_change(self) -> None:
        if self.data is None:
            return
        self._do_refresh()

    @Slot(str)
    def _on_generate_done(self, slot_id: str) -> None:
        if self.data is None:
            return
        self._do_refresh()

    @Slot()
    def _do_refresh(self) -> None:
        if self.data:
            self.trigger_get_slots.emit(self.data)

    @Slot(QListWidgetItem, QListWidgetItem)
    def _slot_selection_changed(
        self, current: Optional[QListWidgetItem], _previous: Optional[QListWidgetItem]
    ) -> None:
        if current is None:
            self.ui.slot_stack.setCurrentWidget(self.ui.slot_empty)
            return
        slot = current.data(Qt.ItemDataRole.UserRole)
        if isinstance(slot, PivSlotInfo):
            self._show_slot(slot)

    # ── User actions ──────────────────────────────────────────────────────────

    @Slot()
    def _prompt_change_pin(self) -> None:
        if not self.data:
            return
        old_pin, ok = QInputDialog.getText(
            self, "Change PIV PIN", "Current PIN:", QLineEdit.EchoMode.Password
        )
        if not ok or not old_pin:
            return
        new_pin, ok = QInputDialog.getText(
            self, "Change PIV PIN", "New PIN (6–8 digits):", QLineEdit.EchoMode.Password
        )
        if not ok or not new_pin:
            return
        self.trigger_change_pin.emit(self.data, old_pin, new_pin)

    @Slot()
    def _prompt_change_puk(self) -> None:
        if not self.data:
            return
        old_puk, ok = QInputDialog.getText(
            self, "Change PIV PUK", "Current PUK (8 chars):", QLineEdit.EchoMode.Password
        )
        if not ok or not old_puk:
            return
        new_puk, ok = QInputDialog.getText(
            self, "Change PIV PUK", "New PUK (8 chars):", QLineEdit.EchoMode.Password
        )
        if not ok or not new_puk:
            return
        self.trigger_change_puk.emit(self.data, old_puk, new_puk)

    @Slot()
    def _prompt_reset(self) -> None:
        if not self.data:
            return
        confirm = QMessageBox.warning(
            self,
            "Reset PIV Application",
            "This will permanently delete all PIV keys and certificates.\n\n"
            "Note: the PIN and PUK must both be fully blocked (0 retries) before "
            "a factory reset is allowed.\n\n"
            "Proceed?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if confirm == QMessageBox.StandardButton.Yes:
            self.trigger_reset_piv.emit(self.data)

    @Slot()
    def _prompt_generate_key(self) -> None:
        if not self.data or not self.active_slot:
            return

        dialog = _GenerateKeyDialog(self.active_slot.slot_id, self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        algo_id = dialog.selected_algo_id()
        self.trigger_generate_key.emit(self.data, self.active_slot.slot_id, algo_id)

    @Slot()
    def _prompt_import_p12(self) -> None:
        if not self.data or not self.active_slot:
            return

        path, _ = QFileDialog.getOpenFileName(
            self, "Open P12 File", "", "PKCS#12 Files (*.p12 *.pfx)"
        )
        if not path:
            return

        try:
            with open(path, "rb") as f:
                p12_data = f.read()
        except OSError as e:
            QMessageBox.critical(self, "Error", f"Failed to read file: {e}")
            return

        password_str, ok = QInputDialog.getText(
            self,
            "P12 Password",
            "Password for the P12 file (leave empty if none):",
            QLineEdit.EchoMode.Password,
        )
        password: Optional[bytes] = password_str.encode() if (ok and password_str) else None

        admin_key_str, ok = QInputDialog.getText(
            self,
            "Management Key",
            "Management key (hex, leave empty for default):",
        )
        if ok and admin_key_str.strip():
            try:
                admin_key = bytes.fromhex(admin_key_str.strip())
            except ValueError:
                QMessageBox.critical(self, "Error", "Invalid management key (must be hex string)")
                return
        else:
            admin_key = DEFAULT_ADMIN_KEY

        self.trigger_import_p12.emit(
            self.data, self.active_slot.slot_id, p12_data, password, admin_key
        )


# ── Helper dialog ─────────────────────────────────────────────────────────────

class _GenerateKeyDialog(QDialog):
    def __init__(self, slot_id: str, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setWindowTitle(f"Generate Key — Slot {slot_id}")

        self._combo = QComboBox()
        for name, _ in ALGO_CHOICES:
            self._combo.addItem(name)

        layout = QVBoxLayout()
        form = QFormLayout()
        form.addRow(QLabel("Algorithm:"), self._combo)
        layout.addLayout(form)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        self.setLayout(layout)

    def selected_algo_id(self) -> bytes:
        return ALGO_CHOICES[self._combo.currentIndex()][1]
