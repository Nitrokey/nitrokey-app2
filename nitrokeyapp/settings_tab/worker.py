import logging

from fido2.ctap2.base import Ctap2, Info
from fido2.ctap2.pin import ClientPin
from fido2.ctap2.credman import CredentialManagement
from fido2.ctap import CtapError
from nitrokey.nk3 import NK3
from nitrokey.nk3.secrets_app import SecretsApp, SecretsAppException, SelectResponse
from PySide6.QtCore import Signal, Slot

from nitrokeyapp.common_ui import CommonUi
from nitrokeyapp.device_data import DeviceData
from nitrokeyapp.worker import Job, Worker

logger = logging.getLogger(__name__)


class CheckFidoPinStatus(Job):
    status_fido = Signal(Info, int)

    def __init__(self, common_ui: CommonUi, data: DeviceData) -> None:
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

    def __init__(self, common_ui: CommonUi, data: DeviceData) -> None:
        super().__init__(common_ui)

        self.data = data

        self.info_passwords.connect(lambda _: self.finished.emit())

    def run(self) -> None:
        pin_status: bool = False
        with self.data.open() as device:
            if not isinstance(device, NK3):
                return
            secrets = SecretsApp(device)
            status = secrets.select()
            if status.pin_attempt_counter is not None:
                pin_status = True
            else:
                pin_status = False
            self.info_passwords.emit(pin_status, status)
        return

class CheckDiscoverableCreds(Job):
    discoverable_creds = Signal(list)

    def __init__(self, common_ui: CommonUi, data: DeviceData, pin: str) -> None:
        super().__init__(common_ui)
        self.data = data
        self.pin = pin
        self.discoverable_creds.connect(lambda: self.finished.emit())

    def run(self) -> None:
        with self.data.open() as device:
            ctap2 = Ctap2(device.device)
            c_pin = ClientPin(ctap2)

            try:
                client_token = c_pin.get_pin_token(self.pin, permissions=ClientPin.PERMISSION.CREDENTIAL_MGMT)
            except CtapError as error:
                logger.error("Failed to get pin token with credman permissions", exc_info=True)
                if error.code == CtapError.ERR.PIN_NOT_SET:
                    self.trigger_error("Please set a pin in order to manage credentials")
                if error.code == CtapError.ERR.PIN_AUTH_BLOCKED:
                    self.trigger_error("Pin authentication has been blocked, try reinserting the key or setting a pin if none is set")
                if error.code == CtapError.ERR.PIN_BLOCKED:
                    self.trigger_error("Your device has been blocked after too many failed unlock attempts, to fix this it will have to be reset. (If no pin is set, plugging it in again might fix this warning)")
                if error.code == CtapError.ERR.PIN_INVALID:
                    self.trigger_error("Wrong pin, please retry")
                self.discoverable_creds.emit([])
                return

            try:
                cred_man=CredentialManagement(ctap2, c_pin.protocol, client_token)
                cred_metadata = cred_man.get_metadata()
                cred_count = cred_metadata.get(CredentialManagement.RESULT.EXISTING_CRED_COUNT)
        
                if cred_count==0:
                    self.discoverable_creds.emit([])
                    return
        
                reliable_party_list = cred_man.enumerate_rps()
                self.discoverable_creds_list=[]
                for reliable_party_result in reliable_party_list:
                    reliable_party = reliable_party_result.get(CredentialManagement.RESULT.RP)
                    reliable_party_hash = reliable_party_result.get(CredentialManagement.RESULT.RP_ID_HASH)
                    assert isinstance(reliable_party, dict)
                    name_or_id = reliable_party.get("name", reliable_party.get("id", "(no id)"))
            
                    for cred in cred_man.enumerate_creds(reliable_party_hash):
                        _cred_id = cred.get(CredentialManagement.RESULT.CREDENTIAL_ID)
                        assert isinstance(_cred_id, dict)
                        cred_user = cred.get(CredentialManagement.RESULT.USER)
                        assert isinstance(cred_user, dict)
                        cred_dict={'rp_id':name_or_id, 'user': cred_user}
                        self.discoverable_creds_list.append(cred_dict)

                self.discoverable_creds.emit(self.discoverable_creds_list)

            except Exception as e:
                logger.error("Failed to enumerate discoverable credentials", exc_info=True)
                self.trigger_error(f"Failed to enumerate discoverable credentials: {e}")
                self.discoverable_creds.emit([])

class SaveFidoPinJob(Job):
    change_pw_fido = Signal()

    def __init__(self, common_ui: CommonUi, data: DeviceData, old_pin: str, new_pin: str) -> None:
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

    def __init__(self, common_ui: CommonUi, data: DeviceData, old_pin: str, new_pin: str) -> None:
        super().__init__(common_ui)

        self.data = data
        self.old_pin = old_pin
        self.new_pin = new_pin

        self.change_pw_passwords.connect(lambda: self.finished.emit())

    def check(self) -> bool:
        pin_status: bool = False
        with self.data.open() as device:
            if not isinstance(device, NK3):
                return pin_status
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
                if not isinstance(device, NK3):
                    return
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

    def __init__(self, common_ui: CommonUi, data: DeviceData) -> None:
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

    def __init__(self, common_ui: CommonUi, data: DeviceData) -> None:
        super().__init__(common_ui)

        self.data = data

        self.reset_passwords.connect(lambda: self.finished.emit())

    def run(self) -> None:
        with self.data.open() as device:
            if not isinstance(device, NK3):
                return
            secrets = SecretsApp(device)
            try:
                with self.touch_prompt():
                    secrets.reset()
                    self.common_ui.info.info.emit("PASSWORDS function reset successfully!")
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
    discoverable_creds= Signal(list)

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

    @Slot(DeviceData)
    def get_discoverablecreds(self, data: DeviceData, pin: str):
        job = CheckDiscoverableCreds(self.common_ui, data, pin)
        job.discoverable_creds.connect(self.discoverable_creds)
        self.run(job)