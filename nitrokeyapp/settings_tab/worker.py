import logging

from fido2.ctap2.base import Ctap2, Info
from fido2.ctap2.pin import ClientPin
from nitrokey.nk3.secrets_app import (
    SecretsApp,
    SecretsAppException,
    SelectResponse,
)
from PySide6.QtCore import Signal, Slot

from nitrokeyapp.common_ui import CommonUi
from nitrokeyapp.device_data import DeviceData
from nitrokeyapp.worker import Job, Worker

logger = logging.getLogger(__name__)


class CheckFidoPinStatus(Job):
    status_fido = Signal(Info, int)

    def __init__(
        self,
        common_ui: CommonUi,
        data: DeviceData,
    ) -> None:
        super().__init__(common_ui)

        self.data = data

        self.status_fido.connect(lambda _a, _b: self.finished.emit())

    def run(self) -> None:
        # pin_status: bool = False
        with self.data.open() as device:
            ctap2 = Ctap2(device.device)
            # pin_status = ctap2.info.options["clientPin"]

            c_pin = ClientPin(ctap2)
            try:
                pin_retries = c_pin.get_pin_retries()[0]
            except Exception:
                pin_retries = -1

            self.status_fido.emit(ctap2.info, pin_retries)


class CheckPasswordsInfo(Job):
    info_passwords = Signal(bool, SelectResponse)

    def __init__(
        self,
        common_ui: CommonUi,
        data: DeviceData,
    ) -> None:
        super().__init__(common_ui)

        self.data = data

        self.info_passwords.connect(lambda _: self.finished.emit())

    def run(self) -> None:
        pin_status: bool = False
        with self.data.open() as device:
            secrets = SecretsApp(device)
            status = secrets.select()
            if status.pin_attempt_counter is not None:
                pin_status = True
            else:
                pin_status = False
            self.info_passwords.emit(pin_status, status)
        return


class SaveFidoPinJob(Job):
    change_pw_fido = Signal()

    def __init__(
        self,
        common_ui: CommonUi,
        data: DeviceData,
        old_pin: str,
        new_pin: str,
    ) -> None:
        super().__init__(common_ui)

        self.data = data
        self.old_pin = old_pin
        self.new_pin = new_pin

        self.change_pw_fido.connect(lambda: self.finished.emit())

    def check(self) -> bool:
        pin_status: bool = False
        with self.data.open() as device:
            ctap2 = Ctap2(device.device)
            pin_status = ctap2.info.options["clientPin"]
        return pin_status

    def run(self) -> None:
        fido_state = self.check()
        with self.data.open() as device:
            ctap2 = Ctap2(device.device)
            client_pin = ClientPin(ctap2)

            try:
                if fido_state:
                    client_pin.change_pin(self.old_pin, self.new_pin)
                else:
                    client_pin.set_pin(self.new_pin)
                    self.common_ui.info.info.emit("FIDO2 PIN changed!")
            except Exception as e:
                self.trigger_error(f"fido2 change_pin failed: {e}")
        self.change_pw_fido.emit()


class SavePasswordsPinJob(Job):
    change_pw_passwords = Signal()

    def __init__(
        self,
        common_ui: CommonUi,
        data: DeviceData,
        old_pin: str,
        new_pin: str,
    ) -> None:
        super().__init__(common_ui)

        self.data = data
        self.old_pin = old_pin
        self.new_pin = new_pin

        self.change_pw_passwords.connect(lambda: self.finished.emit())

    def check(self) -> bool:
        pin_status: bool = False
        with self.data.open() as device:
            secrets = SecretsApp(device)
            status = secrets.select()
            if status.pin_attempt_counter is not None:
                pin_status = True
            else:
                pin_status = False
        return pin_status

    def run(self) -> None:
        passwords_state = self.check()
        with self.touch_prompt():
            with self.data.open() as device:
                secrets = SecretsApp(device)
                try:
                    if passwords_state:
                        secrets.change_pin_raw(self.old_pin, self.new_pin)
                    else:
                        secrets.set_pin_raw(self.new_pin)
                    self.common_ui.info.info.emit("Passwords PIN changed!")
                except SecretsAppException as e:
                    self.trigger_error(f"PIN validation failed: {e}")

        self.change_pw_passwords.emit()

    @Slot(str)
    def trigger_error(self, msg: str) -> None:
        self.common_ui.info.error.emit(msg)


class ResetFido(Job):
    reset_fido = Signal()

    def __init__(
        self,
        common_ui: CommonUi,
        data: DeviceData,
    ) -> None:
        super().__init__(common_ui)

        self.data = data

        self.reset_fido.connect(lambda: self.finished.emit())

    def run(self) -> None:
        with self.data.open() as device:
            ctap2 = Ctap2(device.device)

            try:
                with self.touch_prompt():
                    ctap2.reset()
                    self.common_ui.info.info.emit("FIDO2 function reset successfully!")
            except Exception as e:
                a = str(e)
                if a == "CTAP error: 0x30 - NOT_ALLOWED":
                    self.common_ui.info.error.emit(
                        "Device connected for more than 10 sec. Re-plugging for reset!"
                    )
                else:
                    self.trigger_error(f"fido2 reset failed: {e}")
        self.reset_fido.emit()


class ResetPasswords(Job):
    reset_passwords = Signal()

    def __init__(
        self,
        common_ui: CommonUi,
        data: DeviceData,
    ) -> None:
        super().__init__(common_ui)

        self.data = data

        self.reset_passwords.connect(lambda: self.finished.emit())

    def run(self) -> None:
        with self.data.open() as device:
            secrets = SecretsApp(device)
            try:
                with self.touch_prompt():
                    secrets.reset()
                    self.common_ui.info.info.emit(
                        "PASSWORDS function reset successfully!"
                    )
            except SecretsAppException as e:
                self.trigger_error(f"Passwords reset failed: {e}")
        self.reset_passwords.emit()


class SettingsWorker(Worker):
    change_pw_fido = Signal()
    change_pw_passwords = Signal()
    reset_fido = Signal()
    reset_passwords = Signal()
    status_fido = Signal(Info, int)
    info_passwords = Signal(bool, SelectResponse)

    def __init__(self, common_ui: CommonUi) -> None:
        super().__init__(common_ui)

    @Slot(DeviceData)
    def fido_status(self, data: DeviceData) -> None:
        job = CheckFidoPinStatus(self.common_ui, data)
        job.status_fido.connect(self.status_fido)
        self.run(job)

    @Slot(DeviceData)
    def passwords_status(self, data: DeviceData) -> None:
        job = CheckPasswordsInfo(self.common_ui, data)
        job.info_passwords.connect(self.info_passwords)
        self.run(job)

    @Slot(DeviceData, str, str)
    def fido_change_pw(self, data: DeviceData, old_pin: str, new_pin: str) -> None:
        job = SaveFidoPinJob(self.common_ui, data, old_pin, new_pin)
        job.change_pw_fido.connect(self.change_pw_fido)
        self.run(job)

    @Slot(DeviceData, str, str)
    def passwords_change_pw(self, data: DeviceData, old_pin: str, new_pin: str) -> None:
        job = SavePasswordsPinJob(self.common_ui, data, old_pin, new_pin)
        job.change_pw_passwords.connect(self.change_pw_passwords)
        self.run(job)

    @Slot(DeviceData)
    def fido_reset(self, data: DeviceData) -> None:
        job = ResetFido(self.common_ui, data)
        job.reset_fido.connect(self.reset_fido)
        self.run(job)

    @Slot(DeviceData)
    def passwords_reset(self, data: DeviceData) -> None:
        job = ResetPasswords(self.common_ui, data)
        job.reset_passwords.connect(self.reset_passwords)
        self.run(job)
