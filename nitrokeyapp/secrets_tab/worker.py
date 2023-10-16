from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from pynitrokey.nk3.secrets_app import SecretsApp, SecretsAppException
from pynitrokey.nk3.utils import Uuid
from PyQt5.QtCore import pyqtSignal, pyqtSlot
from PyQt5.QtWidgets import QWidget

from nitrokeyapp.device_data import DeviceData
from nitrokeyapp.worker import Job, Worker

from .data import Credential, OtpData, OtpKind
from .ui import PinUi


@dataclass
class PinCache:
    uuid: Optional[Uuid] = None
    pin: Optional[str] = None

    def clear(self) -> None:
        self.uuid = None
        self.pin = None

    def get(self, data: DeviceData) -> Optional[str]:
        if data.uuid and self.uuid == data.uuid:
            return self.pin
        else:
            return None

    def update(self, data: DeviceData, pin: str) -> None:
        if not data.uuid:
            return
        self.uuid = data.uuid
        self.pin = pin


class CheckDeviceJob(Job):
    device_checked = pyqtSignal(bool)

    def __init__(self, data: DeviceData) -> None:
        super().__init__()

        self.data = data

        self.device_checked.connect(lambda _: self.finished.emit())

    def run(self) -> None:
        compatible = False
        with self.data.open() as device:
            secrets = SecretsApp(device)
            try:
                compatible = secrets._semver_equal_or_newer("4.11.0")
            except Exception:
                # TODO: catch a more specific exception
                pass

        self.device_checked.emit(compatible)


class VerifyPinJob(Job):
    pin_verified = pyqtSignal(bool)

    # internal signals
    query_pin = pyqtSignal(int)
    choose_pin = pyqtSignal()

    def __init__(
        self,
        pin_cache: PinCache,
        pin_ui: PinUi,
        data: DeviceData,
        set_pin: bool = False,
    ) -> None:
        super().__init__()

        self.pin_cache = pin_cache
        self.data = data
        self.set_pin = set_pin

        self.pin_verified.connect(lambda _: self.finished.emit())

        self.query_pin.connect(pin_ui.query)
        self.choose_pin.connect(pin_ui.choose)

        self.pin_ui = pin_ui.connect(
            self.pin_queried,
            self.pin_chosen,
            lambda: self.pin_verified.emit(False),
        )

    def cleanup(self) -> None:
        self.pin_ui.disconnect()

    def run(self) -> None:
        with self.data.open() as device:
            secrets = SecretsApp(device)
            select = secrets.select()

        if select.pin_attempt_counter:
            pin = self.pin_cache.get(self.data)
            if pin:
                self.pin_queried(pin)
            else:
                self.query_pin.emit(select.pin_attempt_counter)
        elif self.set_pin:
            self.choose_pin.emit()
        else:
            self.pin_verified.emit(False)

    @pyqtSlot(str)
    def pin_queried(self, pin: str) -> None:
        with self.data.open() as device:
            secrets = SecretsApp(device)
            try:
                with self.touch_prompt():
                    secrets.verify_pin_raw(pin)
                self.pin_cache.update(self.data, pin)
                self.pin_verified.emit(True)
            except SecretsAppException as e:
                self.pin_cache.clear()
                # TODO: repeat on failure
                # TODO: check error code
                # TODO: improve error message
                self.trigger_error(f"PIN validation failed: {e}")

    @pyqtSlot(str)
    def pin_chosen(self, pin: str) -> None:
        with self.data.open() as device:
            secrets = SecretsApp(device)
            with self.touch_prompt():
                secrets.set_pin_raw(pin)
            select = secrets.select()

        if select.pin_attempt_counter:
            self.pin_queried(pin)
        else:
            self.trigger_error("Failed to set Secrets PIN")

    @pyqtSlot(str)
    def trigger_error(self, msg: str) -> None:
        self.error.emit(msg)
        self.pin_verified.emit(False)


class AddCredentialJob(Job):
    credential_added = pyqtSignal(Credential)

    def __init__(
        self,
        pin_cache: PinCache,
        pin_ui: PinUi,
        data: DeviceData,
        credential: Credential,
        secret: bytes,
    ) -> None:
        super().__init__()

        self.pin_cache = pin_cache
        self.pin_ui = pin_ui
        self.data = data
        self.credential = credential
        self.secret = secret

        self.credential_added.connect(lambda _: self.finished.emit())

    def run(self) -> None:
        list_credentials_job = ListCredentialsJob(
            self.pin_cache,
            self.pin_ui,
            self.data,
            pin_protected=True,
        )
        list_credentials_job.credentials_listed.connect(self.check_credential)
        self.spawn(list_credentials_job)

    @pyqtSlot(list)
    def check_credential(self, credentials: list[Credential]) -> None:
        ids = set([credential.id for credential in credentials])
        if self.credential.id in ids:
            self.trigger_error(
                f"A credential with the name {self.credential.name} already exists."
            )
        elif self.credential.protected:
            verify_pin_job = VerifyPinJob(
                self.pin_cache,
                self.pin_ui,
                self.data,
                set_pin=self.credential.protected,
            )
            verify_pin_job.pin_verified.connect(self.add_credential)
            self.spawn(verify_pin_job)
        else:
            self.add_credential()

    @pyqtSlot(bool)
    def add_credential(self, successful: bool = True) -> None:
        if not successful:
            self.finished.emit()
            return

        assert self.credential.otp
        with self.data.open() as device:
            secrets = SecretsApp(device)
            with self.touch_prompt():
                secrets.register(
                    credid=self.credential.id,
                    secret=self.secret,
                    kind=self.credential.otp.raw_kind(),
                    touch_button_required=self.credential.touch_required,
                    pin_based_encryption=self.credential.protected,
                )

            self.credential_added.emit(self.credential)


class DeleteCredentialJob(Job):
    credential_deleted = pyqtSignal(Credential)

    def __init__(
        self,
        pin_cache: PinCache,
        pin_ui: PinUi,
        data: DeviceData,
        credential: Credential,
    ) -> None:
        super().__init__()

        self.pin_cache = pin_cache
        self.pin_ui = pin_ui
        self.data = data
        self.credential = credential

        self.credential_deleted.connect(lambda _: self.finished.emit())

    def run(self) -> None:
        with self.touch_prompt():
            if self.credential.protected:
                verify_pin_job = VerifyPinJob(self.pin_cache, self.pin_ui, self.data)
                verify_pin_job.pin_verified.connect(self.delete_credential)
                self.spawn(verify_pin_job)
            else:
                self.delete_credential()

    @pyqtSlot()
    def delete_credential(self) -> None:
        with self.data.open() as device:
            secrets = SecretsApp(device)

            secrets.delete(self.credential.id)
            self.credential_deleted.emit(self.credential)


class GenerateOtpJob(Job):
    # TODO: make period and digits configurable

    otp_generated = pyqtSignal(OtpData)

    def __init__(
        self,
        pin_cache: PinCache,
        pin_ui: PinUi,
        data: DeviceData,
        credential: Credential,
    ) -> None:
        super().__init__()

        self.pin_cache = pin_cache
        self.pin_ui = pin_ui
        self.data = data
        self.credential = credential

        self.otp_generated.connect(lambda _: self.finished.emit())

    def run(self) -> None:
        if self.credential.protected:
            verify_pin_job = VerifyPinJob(self.pin_cache, self.pin_ui, self.data)
            verify_pin_job.pin_verified.connect(self.generate_otp)
            self.spawn(verify_pin_job)
        else:
            self.generate_otp()

    @pyqtSlot()
    def generate_otp(self) -> None:
        with self.data.open() as device:
            secrets = SecretsApp(device)

            challenge = None
            validity = None
            if self.credential.otp == OtpKind.HOTP:
                pass
            elif self.credential.otp == OtpKind.TOTP:
                period = 30
                now = int(datetime.now().timestamp())
                challenge = now // period
                valid_from = datetime.fromtimestamp(challenge * period)
                valid_until = datetime.fromtimestamp((challenge + 1) * period)
                validity = (valid_from, valid_until)
            else:
                raise RuntimeError(f"Unexpected OTP kind: {self.credential.otp}")

            with self.touch_prompt():
                otp = secrets.calculate(self.credential.id, challenge).decode()

            self.otp_generated.emit(OtpData(otp, validity))


class ListCredentialsJob(Job):
    credentials_listed = pyqtSignal(list)

    def __init__(
        self, pin_cache: PinCache, pin_ui: PinUi, data: DeviceData, pin_protected: bool
    ) -> None:
        super().__init__()

        self.pin_cache = pin_cache
        self.pin_ui = pin_ui
        self.data = data
        self.pin_protected = pin_protected

        self.credentials_listed.connect(lambda _: self.finished.emit())

    def run(self) -> None:
        if self.pin_protected:
            verify_pin_job = VerifyPinJob(self.pin_cache, self.pin_ui, self.data)
            verify_pin_job.pin_verified.connect(self.list_protected_credentials)
            self.spawn(verify_pin_job)
        else:
            with self.data.open() as device:
                secrets = SecretsApp(device)
                credentials = Credential.list(secrets)
            self.credentials_listed.emit(credentials)

    @pyqtSlot(bool)
    def list_protected_credentials(self, successful: bool) -> None:
        credentials = []
        if not successful:
            # TODO: un-check PIN protection check box
            pass

        with self.data.open() as device:
            secrets = SecretsApp(device)
            for credential in Credential.list(secrets):
                credentials.append(credential)

        self.credentials_listed.emit(credentials)


class SecretsWorker(Worker):
    # TODO: remove DeviceData from signatures

    credential_added = pyqtSignal(Credential)
    credential_deleted = pyqtSignal(Credential)
    credentials_listed = pyqtSignal(list)
    device_checked = pyqtSignal(bool)
    otp_generated = pyqtSignal(OtpData)

    def __init__(self, widget: QWidget) -> None:
        super().__init__()

        self.pin_cache = PinCache()
        self.pin_ui = PinUi(widget)

    @pyqtSlot(DeviceData)
    def check_device(self, data: DeviceData) -> None:
        job = CheckDeviceJob(data)
        job.device_checked.connect(self.device_checked)
        self.run(job)

    @pyqtSlot(DeviceData, Credential, bytes)
    def add_credential(
        self, data: DeviceData, credential: Credential, secret: bytes
    ) -> None:
        job = AddCredentialJob(self.pin_cache, self.pin_ui, data, credential, secret)
        job.credential_added.connect(self.credential_added)
        self.run(job)

    @pyqtSlot(DeviceData, Credential)
    def delete_credential(self, data: DeviceData, credential: Credential) -> None:
        job = DeleteCredentialJob(self.pin_cache, self.pin_ui, data, credential)
        job.credential_deleted.connect(self.credential_deleted)
        self.run(job)

    @pyqtSlot(DeviceData, Credential)
    def generate_otp(self, data: DeviceData, credential: Credential) -> None:
        job = GenerateOtpJob(self.pin_cache, self.pin_ui, data, credential)
        job.otp_generated.connect(self.otp_generated)
        self.run(job)

    @pyqtSlot(DeviceData, bool)
    def refresh_credentials(self, data: DeviceData, pin_protected: bool) -> None:
        job = ListCredentialsJob(self.pin_cache, self.pin_ui, data, pin_protected)
        job.credentials_listed.connect(self.credentials_listed)
        self.run(job)
