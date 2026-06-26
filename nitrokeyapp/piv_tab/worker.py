# Copyright 2026 Nitrokey Developers
#
# Licensed under the Apache License, Version 2.0, <LICENSE-APACHE or
# http://apache.org/licenses/LICENSE-2.0> or the MIT license <LICENSE-MIT or
# http://opensource.org/licenses/MIT>, at your option. This file may not be
# copied, modified, or distributed except according to those terms.

import logging
from dataclasses import dataclass
from typing import Optional

from nitrokey.trussed import Uuid
from PySide6.QtCore import QObject, Signal, Slot
from PySide6.QtWidgets import QWidget

from nitrokeyapp.common_ui import CommonUi
from nitrokeyapp.device_data import DeviceData
from nitrokeyapp.worker import Job, Worker

from .data import DEFAULT_ADMIN_KEY, PivApp, PivError, PivSlotInfo
from .ui import PivPinUi, PivPinUiConnection

logger = logging.getLogger(__name__)


@dataclass
class PinCache(QObject):
    uuid: Optional[Uuid] = None
    pin: Optional[str] = None

    pin_cached = Signal()
    pin_cleared = Signal()

    def __init__(self) -> None:
        super().__init__()

    @Slot()
    def clear(self) -> None:
        self.uuid = None
        self.pin = None
        self.pin_cleared.emit()

    def get(self, data: DeviceData) -> Optional[str]:
        if data.uuid and self.uuid == data.uuid:
            return self.pin
        return None

    def update(self, data: DeviceData, pin: str) -> None:
        if not data.uuid:
            return
        self.uuid = data.uuid
        self.pin = pin
        self.pin_cached.emit()


# ─── Jobs ─────────────────────────────────────────────────────────────────────

class CheckDeviceJob(Job):
    device_checked = Signal(bool)

    def __init__(self, common_ui: CommonUi, data: DeviceData) -> None:
        super().__init__(common_ui)
        self.data = data
        self.device_checked.connect(lambda _: self.finished.emit())

    def run(self) -> None:
        compatible = False
        try:
            with PivApp.open() as piv:
                _ = piv.list_slots()
                compatible = True
        except Exception as e:
            logger.info(f"PIV check failed: {e}")
            compatible = False
        self.device_checked.emit(compatible)


class GetSlotsJob(Job):
    slots_listed = Signal(list)

    def __init__(self, common_ui: CommonUi, data: DeviceData) -> None:
        super().__init__(common_ui)
        self.data = data
        self.slots_listed.connect(lambda _: self.finished.emit())

    def run(self) -> None:
        try:
            with PivApp.open() as piv:
                slots = piv.list_slots()
            self.slots_listed.emit(slots)
        except PivError as e:
            self.trigger_error(f"Failed to list PIV slots: {e}")
        except Exception as e:
            self.trigger_error(f"Failed to list PIV slots: {e}")


class ChangePinJob(Job):
    pin_changed = Signal()

    def __init__(self, common_ui: CommonUi, data: DeviceData, old_pin: str, new_pin: str) -> None:
        super().__init__(common_ui)
        self.data = data
        self.old_pin = old_pin
        self.new_pin = new_pin
        self.pin_changed.connect(lambda: self.finished.emit())

    def run(self) -> None:
        try:
            with PivApp.open() as piv:
                piv.change_pin(self.old_pin, self.new_pin)
            self.common_ui.info.info.emit("PIV PIN changed successfully")
            self.pin_changed.emit()
        except PivError as e:
            if e.is_wrong_pin:
                self.trigger_error(f"Wrong PIN — {e.pin_retries} retries remaining")
            else:
                self.trigger_error(f"Failed to change PIV PIN: {e}")
        except Exception as e:
            self.trigger_error(f"Failed to change PIV PIN: {e}")


class ChangePukJob(Job):
    puk_changed = Signal()

    def __init__(self, common_ui: CommonUi, data: DeviceData, old_puk: str, new_puk: str) -> None:
        super().__init__(common_ui)
        self.data = data
        self.old_puk = old_puk
        self.new_puk = new_puk
        self.puk_changed.connect(lambda: self.finished.emit())

    def run(self) -> None:
        try:
            with PivApp.open() as piv:
                piv.change_puk(self.old_puk, self.new_puk)
            self.common_ui.info.info.emit("PIV PUK changed successfully")
            self.puk_changed.emit()
        except PivError as e:
            if e.is_wrong_pin:
                self.trigger_error(f"Wrong PUK — {e.pin_retries} retries remaining")
            else:
                self.trigger_error(f"Failed to change PIV PUK: {e}")
        except Exception as e:
            self.trigger_error(f"Failed to change PIV PUK: {e}")


class ResetPivJob(Job):
    piv_reset = Signal()

    def __init__(self, common_ui: CommonUi, data: DeviceData) -> None:
        super().__init__(common_ui)
        self.data = data
        self.piv_reset.connect(lambda: self.finished.emit())

    def run(self) -> None:
        try:
            with PivApp.open() as piv:
                piv.factory_reset()
            self.common_ui.info.info.emit("PIV application reset successfully")
            self.piv_reset.emit()
        except PivError as e:
            self.trigger_error(
                f"PIV reset failed: {e}. "
                "Note: PIN and PUK must be fully blocked (0 retries) before resetting."
            )
        except Exception as e:
            self.trigger_error(f"PIV reset failed: {e}")


class ImportP12Job(Job):
    import_done = Signal()

    def __init__(
        self,
        common_ui: CommonUi,
        data: DeviceData,
        slot_id: str,
        p12_data: bytes,
        password: Optional[bytes],
        admin_key: bytes,
    ) -> None:
        super().__init__(common_ui)
        self.data = data
        self.slot_id = slot_id
        self.p12_data = p12_data
        self.password = password
        self.admin_key = admin_key
        self.import_done.connect(lambda: self.finished.emit())

    def run(self) -> None:
        try:
            with PivApp.open() as piv:
                piv.import_p12(self.slot_id, self.p12_data, self.password, self.admin_key)
            self.common_ui.info.info.emit(f"P12 imported into slot {self.slot_id} successfully")
            self.import_done.emit()
        except ValueError as e:
            self.trigger_error(str(e))
        except PivError as e:
            self.trigger_error(f"PIV import failed: {e}")
        except Exception as e:
            self.trigger_error(f"P12 import failed: {e}")


class GenerateKeyJob(Job):
    generate_done = Signal(str)  # emits slot_id

    def __init__(
        self,
        common_ui: CommonUi,
        pin_cache: PinCache,
        pin_ui: PivPinUi,
        data: DeviceData,
        slot_id: str,
        algo_id: bytes,
    ) -> None:
        super().__init__(common_ui)
        self.pin_cache = pin_cache
        self.pin_ui = pin_ui
        self.data = data
        self.slot_id = slot_id
        self.algo_id = algo_id
        self._pin_ui_conn: Optional[PivPinUiConnection] = None
        self.generate_done.connect(lambda _: self.finished.emit())

    def cleanup(self) -> None:
        if self._pin_ui_conn is not None:
            self._pin_ui_conn.disconnect()
            self._pin_ui_conn = None

    def run(self) -> None:
        cached = self.pin_cache.get(self.data)
        if cached:
            self._do_generate(cached)
            return

        retries = self._get_retries()
        self._pin_ui_conn = self.pin_ui.connect_actions(self._on_pin, lambda: self.finished.emit())
        self.pin_ui.query.emit(retries)

    def _get_retries(self) -> int:
        try:
            with PivApp.open() as piv:
                return piv.get_pin_retries()
        except Exception:
            return -1

    @Slot(str)
    def _on_pin(self, pin: str) -> None:
        self._do_generate(pin, pin_was_queried=True)

    def _do_generate(self, pin: str, pin_was_queried: bool = False) -> None:
        try:
            with PivApp.open() as piv:
                piv.authenticate_admin(DEFAULT_ADMIN_KEY)
                piv.login(pin)
                key_ref = int(self.slot_id.upper(), 16)
                piv.generate_key_and_cert(key_ref, self.algo_id, pin)
            if pin_was_queried:
                self.pin_cache.update(self.data, pin)
            self.common_ui.info.info.emit(f"Key generated in slot {self.slot_id}")
            self.generate_done.emit(self.slot_id)
        except PivError as e:
            if e.is_wrong_pin:
                self.pin_cache.clear()
                self.trigger_error(f"Wrong PIN — {e.pin_retries} retries remaining")
            else:
                self.trigger_error(f"Key generation failed: {e}")
        except Exception as e:
            self.trigger_error(f"Key generation failed: {e}")


# ─── Worker ───────────────────────────────────────────────────────────────────

class PivWorker(Worker):
    device_checked = Signal(bool)
    slots_listed = Signal(list)
    pin_changed = Signal()
    puk_changed = Signal()
    piv_reset = Signal()
    import_done = Signal()
    generate_done = Signal(str)

    def __init__(self, common_ui: CommonUi, app_widget: QWidget) -> None:
        super().__init__(common_ui)
        self.pin_cache = PinCache()
        self.pin_ui = PivPinUi(app_widget)

    @Slot(DeviceData)
    def check_device(self, data: DeviceData) -> None:
        job = CheckDeviceJob(self.common_ui, data)
        job.device_checked.connect(self.device_checked)
        self.run(job)

    @Slot(DeviceData)
    def get_slots(self, data: DeviceData) -> None:
        job = GetSlotsJob(self.common_ui, data)
        job.slots_listed.connect(self.slots_listed)
        self.run(job)

    @Slot(DeviceData, str, str)
    def change_pin(self, data: DeviceData, old_pin: str, new_pin: str) -> None:
        job = ChangePinJob(self.common_ui, data, old_pin, new_pin)
        job.pin_changed.connect(self.pin_changed)
        self.run(job)

    @Slot(DeviceData, str, str)
    def change_puk(self, data: DeviceData, old_puk: str, new_puk: str) -> None:
        job = ChangePukJob(self.common_ui, data, old_puk, new_puk)
        job.puk_changed.connect(self.puk_changed)
        self.run(job)

    @Slot(DeviceData)
    def reset_piv(self, data: DeviceData) -> None:
        job = ResetPivJob(self.common_ui, data)
        job.piv_reset.connect(self.piv_reset)
        self.run(job)

    @Slot(DeviceData, str, bytes, object, bytes)
    def import_p12(
        self,
        data: DeviceData,
        slot_id: str,
        p12_data: bytes,
        password: Optional[bytes],
        admin_key: bytes,
    ) -> None:
        job = ImportP12Job(self.common_ui, data, slot_id, p12_data, password, admin_key)
        job.import_done.connect(self.import_done)
        self.run(job)

    @Slot(DeviceData, str, bytes)
    def generate_key(self, data: DeviceData, slot_id: str, algo_id: bytes) -> None:
        job = GenerateKeyJob(self.common_ui, self.pin_cache, self.pin_ui, data, slot_id, algo_id)
        job.generate_done.connect(self.generate_done)
        self.run(job)
