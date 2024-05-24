import logging

from fido2.ctap2.base import Ctap2
from fido2.ctap2.pin import ClientPin
from pynitrokey.fido2 import find
from pynitrokey.nk3.secrets_app import (
    SecretsApp,
    SecretsAppException,
    SelectResponse,
)
from PySide6.QtCore import Signal, Slot

from nitrokeyapp.common_ui import CommonUi
from nitrokeyapp.device_data import DeviceData
from nitrokeyapp.worker import Job

logger = logging.getLogger(__name__)


class SettingsWorker(Job):
    busy_state_changed = Signal(bool)
    status_fido = Signal(bool)
    status_otp = Signal(bool)
    info_otp = Signal(SelectResponse)

    def __init__(self, common_ui: CommonUi) -> None:
        super().__init__(common_ui)

    @Slot(DeviceData)
    def fido_status(self, data: DeviceData) -> bool:
        pin_status: bool = False
        with data.open() as device:
            ctaphid_raw_dev = device.device
            fido2_client = find(raw_device=ctaphid_raw_dev)
            pin_status = fido2_client.has_pin()
        self.status_fido.emit(pin_status)
        return pin_status

    @Slot(DeviceData)
    def otp_status(self, data: DeviceData) -> bool:
        pin_status: bool = False
        with data.open() as device:
            secrets = SecretsApp(device)
            status = secrets.select()
            if status.pin_attempt_counter is not None:
                pin_status = True
            else:
                pin_status = False
            self.status_otp.emit(pin_status)
            self.info_otp.emit(status)
        return pin_status

    @Slot(DeviceData, str, str)
    def fido_change_pw(self, data: DeviceData, old_pin: str, new_pin: str) -> None:
        self.busy_state_changed.emit(True)
        fido_state = self.fido_status(data)
        with data.open() as device:
            ctaphid_raw_dev = device.device
            fido2_client = find(raw_device=ctaphid_raw_dev)
            assert isinstance(fido2_client.ctap2, Ctap2)
            client_pin = ClientPin(fido2_client.ctap2)

            try:
                if fido_state:
                    client_pin.change_pin(old_pin, new_pin)
                else:
                    client_pin.set_pin(new_pin)
            except Exception as e:
                self.trigger_error(f"fido2 change_pin failed: {e}")
        self.busy_state_changed.emit(False)

    @Slot(DeviceData, str, str)
    def otp_change_pw(self, data: DeviceData, old_pin: str, new_pin: str) -> None:
        self.busy_state_changed.emit(True)
        otp_state = self.otp_status(data)
        with data.open() as device:
            secrets = SecretsApp(device)
            try:
                with self.touch_prompt():
                    if otp_state:
                        secrets.change_pin_raw(old_pin, new_pin)
                    else:
                        secrets.set_pin_raw(new_pin)
            except SecretsAppException as e:
                self.trigger_error(f"PIN validation failed: {e}")
            self.busy_state_changed.emit(False)

    @Slot(str)
    def trigger_error(self, msg: str) -> None:
        self.common_ui.info.error.emit(msg)
