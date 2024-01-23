import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Optional

from pynitrokey.nk3.secrets_app import SecretsApp, SecretsAppException
from pynitrokey.nk3.utils import Uuid
from PySide6.QtCore import QObject, Signal, Slot
from PySide6.QtWidgets import QWidget

from nitrokeyapp.device_data import DeviceData
from nitrokeyapp.worker import Job, Worker

from .data import Credential, OtpData, OtpKind
from .ui import PinUi

logger = logging.getLogger(__name__)


@dataclass
class PinCache(QObject):
    uuid: Optional[Uuid] = None
    pin: Optional[str] = None

    pin_cached = Signal()
    pin_cleared = Signal()

    def __init__(self, *v: tuple, **kw: dict) -> None:
        super().__init__(*v, **kw)  # type: ignore [arg-type]

    @Slot()
    def clear(self) -> None:
        self.uuid = None
        self.pin = None
        self.pin_cleared.emit()

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

        self.pin_cached.emit()


class CheckDeviceJob(Job):
    device_checked = Signal(bool)

    def __init__(self, data: DeviceData) -> None:
        super().__init__()

        self.data = data

        self.device_checked.connect(lambda _: self.finished.emit())

    def run(self) -> None:
        compatible = False
        try:
            with self.data.open() as device:
                secrets = SecretsApp(device)
                try:
                    compatible = secrets._semver_equal_or_newer("4.11.0")
                except Exception:
                    # TODO: catch a more specific exception
                    pass
        except Exception as e:
            logger.info(f"check device job failed: {e}")
            compatible = False

        self.device_checked.emit(compatible)


class VerifyPinJob(Job):
    pin_verified = Signal(bool)

    # internal signals
    query_pin = Signal(int)
    choose_pin = Signal()

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

        self.pin_ui = pin_ui.connect_actions(
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

    @Slot(str)
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

    @Slot(str)
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

    @Slot(str)
    def trigger_error(self, msg: str) -> None:
        self.error.emit(self.__class__.__name__, Exception(msg))
        self.pin_verified.emit(False)


class EditCredentialJob(Job):
    credential_edited = Signal(Credential)

    def __init__(
        self,
        pin_cache: PinCache,
        pin_ui: PinUi,
        data: DeviceData,
        credential: Credential,
        secret: bytes,
        old_cred_id: bytes,
    ) -> None:
        super().__init__()

        self.pin_cache = pin_cache
        self.pin_ui = pin_ui
        self.data = data
        self.credential = credential
        self.secret = secret
        self.old_cred_id = old_cred_id

        self.all_credentials: Optional[Dict[bytes, Credential]] = None

        self.credential_edited.connect(lambda _: self.finished.emit())

    def run(self) -> None:
        list_credentials_job = ListCredentialsJob(
            self.pin_cache,
            self.pin_ui,
            self.data,
            pin_protected=True,
        )
        list_credentials_job.credentials_listed.connect(self.check_credential)
        self.spawn(list_credentials_job)

    @Slot(list)
    def check_credential(self, credentials: list[Credential]) -> None:
        self.all_credentials = {cred.id: cred for cred in credentials}
        # ids = set([credential.id for credential in credentials])

        if self.old_cred_id not in self.all_credentials:
            self.trigger_error(
                f"A credential with the name {self.old_cred_id!r} does not exists."
            )
            return

        if (
            self.credential.id != self.old_cred_id
            and self.credential.id in self.all_credentials
        ):
            self.trigger_error(
                f"A credential with the name {self.credential.name} does already exist."
            )
            return

        if self.credential.protected:
            verify_pin_job = VerifyPinJob(
                self.pin_cache,
                self.pin_ui,
                self.data,
                set_pin=self.credential.protected,
            )
            verify_pin_job.pin_verified.connect(self.edit_credential)
            self.spawn(verify_pin_job)
        else:
            self.edit_credential()

    @Slot()
    def edit_credential(self, successful: bool = True) -> None:
        if not successful:
            self.finished.emit()
            return

        # no new secret, new id
        if not self.credential.new_secret:
            # if pin-protected has changed
            self.edit_credential_final()

        else:
            # new secret, new id -> create new, delete old
            if self.old_cred_id != self.credential.id:
                self.add_credential(self.credential, self.secret, self.old_cred_id)

            # new secret, same id -> rename old, create new, delete renamed-old
            else:
                temp_cred_id = self.temp_rename_credential(self.old_cred_id)
                self.add_credential(self.credential, self.secret, temp_cred_id)

    def add_credential(
        self, cred: Credential, secret: bytes, then_delete_id: bytes
    ) -> None:
        add_job = AddCredentialJob(
            self.pin_cache, self.pin_ui, self.data, credential=cred, secret=secret
        )
        add_job.credential_added.connect(
            lambda cred: self.handle_created(cred, then_delete_id)
        )
        self.spawn(add_job)

    @Slot(Credential)
    def handle_created(self, credential: Credential, delete_id: bytes) -> None:
        self.credential = credential
        self.delete_credential(delete_id)

    @Slot()
    def delete_credential(self, cred_id: bytes) -> None:
        cred = Credential(
            id=cred_id,
            protected=self.credential.protected,
            touch_required=self.credential.touch_required,
        )
        del_job = DeleteCredentialJob(
            self.pin_cache,
            self.pin_ui,
            self.data,
            credential=cred,
        )
        del_job.credential_deleted.connect(self.handle_deleted)
        self.spawn(del_job)

    @Slot(Credential)
    def handle_deleted(self, credential: Credential) -> None:
        # drop credential
        self.credential_edited.emit(self.credential)

    @Slot()
    def temp_rename_credential(self, from_cred_id: bytes) -> bytes:
        new_cred_id = b"__" + from_cred_id
        assert self.all_credentials
        while new_cred_id in self.all_credentials.keys():
            new_cred_id += b"_"

        with self.data.open() as device:
            secrets = SecretsApp(device)
            with self.touch_prompt():
                secrets.update_credential(cred_id=from_cred_id, new_name=new_cred_id)

        return new_cred_id

    @Slot()
    def edit_credential_final(self) -> None:
        with self.data.open() as device:
            secrets = SecretsApp(device)
            with self.touch_prompt():

                reg_data = dict(
                    cred_id=self.old_cred_id,
                    touch_button=self.credential.touch_required,
                    # pin_based_encryption=self.credential.protected,
                )
                if self.old_cred_id != self.credential.id:
                    reg_data["new_name"] = self.credential.id

                if self.credential.login:
                    reg_data["login"] = self.credential.login
                if self.credential.password:
                    reg_data["password"] = self.credential.password
                if self.credential.comment:
                    reg_data["metadata"] = self.credential.comment

                try:
                    secrets.update_credential(**reg_data)  # type: ignore [arg-type]
                except SecretsAppException as e:
                    self.trigger_exception(e)
                    return

        self.credential_edited.emit(self.credential)


class AddCredentialJob(Job):
    credential_added = Signal(Credential)

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

    @Slot(list)
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

    @Slot(bool)
    def add_credential(self, successful: bool = True) -> None:
        if not successful:
            self.finished.emit()
            return

        with self.data.open() as device:
            secrets = SecretsApp(device)
            with self.touch_prompt():

                reg_data = dict(
                    credid=self.credential.id,
                    touch_button_required=self.credential.touch_required,
                    pin_based_encryption=self.credential.protected,
                )

                if self.credential.otp:
                    reg_data["secret"] = self.secret
                    reg_data["kind"] = self.credential.otp.raw_kind()

                if self.credential.login:
                    reg_data["login"] = self.credential.login
                if self.credential.password:
                    reg_data["password"] = self.credential.password
                if self.credential.comment:
                    reg_data["metadata"] = self.credential.comment

                try:
                    secrets.register(**reg_data)  # type: ignore [arg-type]
                except SecretsAppException as e:
                    self.trigger_exception(e)
                    return

        self.credential_added.emit(self.credential)


class DeleteCredentialJob(Job):
    credential_deleted = Signal(Credential)

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

    @Slot()
    def delete_credential(self) -> None:
        with self.data.open() as device:
            secrets = SecretsApp(device)
            try:
                secrets.delete(self.credential.id)
            except SecretsAppException as e:
                self.trigger_exception(e)
                return

            self.credential_deleted.emit(self.credential)


class GenerateOtpJob(Job):
    # TODO: make period and digits configurable

    otp_generated = Signal(OtpData)

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

    @Slot()
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
                self.trigger_exception(
                    RuntimeError(f"Unexpected OTP kind: {self.credential.otp}")
                )

            with self.touch_prompt():
                otp = secrets.calculate(self.credential.id, challenge).decode()

            self.otp_generated.emit(OtpData(otp, validity))


class ListCredentialsJob(Job):
    credentials_listed = Signal(list)
    uncheck_checkbox = Signal(bool)

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

    @Slot(bool)
    def list_protected_credentials(self, successful: bool) -> None:
        credentials = []
        if not successful:
            self.uncheck_checkbox.emit(True)

        with self.data.open() as device:
            secrets = SecretsApp(device)
            for credential in Credential.list(secrets):
                credentials.append(credential)

        self.credentials_listed.emit(credentials)


class GetCredentialJob(Job):
    received_credential = Signal(Credential)

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

        self.received_credential.connect(lambda _: self.finished.emit())

    def run(self) -> None:
        with self.touch_prompt():
            if self.credential.protected:
                verify_pin_job = VerifyPinJob(self.pin_cache, self.pin_ui, self.data)
                verify_pin_job.pin_verified.connect(self.get_credential)
                self.spawn(verify_pin_job)
            else:
                self.get_credential()

    @Slot()
    def get_credential(self) -> None:
        with self.data.open() as device:
            secrets = SecretsApp(device)
            try:
                pse = secrets.get_credential(self.credential.id)
            except SecretsAppException as e:
                self.trigger_exception(e)
                return

            cred = self.credential.extend_with_password_safe_entry(pse)
            self.received_credential.emit(cred)


class SecretsWorker(Worker):
    # TODO: remove DeviceData from signatures

    credential_added = Signal(Credential)
    credential_edited = Signal(Credential)
    credential_deleted = Signal(Credential)
    credentials_listed = Signal(list)
    uncheck_checkbox = Signal(bool)
    device_checked = Signal(bool)
    otp_generated = Signal(OtpData)
    received_credential = Signal(Credential)

    def __init__(self, widget: QWidget) -> None:
        super().__init__()

        self.pin_cache = PinCache()
        self.pin_ui = PinUi(widget)

    @Slot(DeviceData)
    def check_device(self, data: DeviceData) -> None:
        job = CheckDeviceJob(data)
        job.device_checked.connect(self.device_checked)
        self.run(job)

    @Slot(DeviceData, Credential, bytes)
    def add_credential(
        self, data: DeviceData, credential: Credential, secret: bytes
    ) -> None:
        job = AddCredentialJob(self.pin_cache, self.pin_ui, data, credential, secret)
        job.credential_added.connect(self.credential_added)
        self.run(job)

    @Slot(DeviceData, Credential)
    def delete_credential(self, data: DeviceData, credential: Credential) -> None:
        job = DeleteCredentialJob(self.pin_cache, self.pin_ui, data, credential)
        job.credential_deleted.connect(self.credential_deleted)
        self.run(job)

    @Slot(DeviceData, Credential)
    def generate_otp(self, data: DeviceData, credential: Credential) -> None:
        job = GenerateOtpJob(self.pin_cache, self.pin_ui, data, credential)
        job.otp_generated.connect(self.otp_generated)
        self.run(job)

    @Slot(DeviceData, bool)
    def refresh_credentials(self, data: DeviceData, pin_protected: bool) -> None:
        job = ListCredentialsJob(self.pin_cache, self.pin_ui, data, pin_protected)
        job.credentials_listed.connect(self.credentials_listed)
        job.uncheck_checkbox.connect(self.uncheck_checkbox)
        self.run(job)

    @Slot(DeviceData, Credential)
    def get_credential(self, data: DeviceData, credential: Credential) -> None:
        job = GetCredentialJob(self.pin_cache, self.pin_ui, data, credential)
        job.received_credential.connect(self.received_credential)
        self.run(job)

    @Slot(DeviceData, Credential, bytes, str)
    def edit_credential(
        self,
        data: DeviceData,
        credential: Credential,
        secret: bytes,
        old_cred_id: bytes,
    ) -> None:
        job = EditCredentialJob(
            self.pin_cache, self.pin_ui, data, credential, secret, old_cred_id
        )
        job.credential_edited.connect(self.credential_edited)
        self.run(job)
