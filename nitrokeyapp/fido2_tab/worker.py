import logging
from dataclasses import dataclass

from fido2.ctap import CtapError
from fido2.ctap2.base import Ctap2
from fido2.ctap2.credman import CredentialManagement
from fido2.ctap2.pin import ClientPin
from fido2.webauthn import PublicKeyCredentialDescriptor, PublicKeyCredentialType
from nitrokey.trussed import Uuid
from PySide6.QtCore import QObject, Signal, Slot
from PySide6.QtWidgets import QWidget

from nitrokeyapp.common_ui import CommonUi
from nitrokeyapp.device_data import DeviceData
from nitrokeyapp.worker import Job, Worker

from .data import Fido2Credential
from .ui import Fido2PinUi, Fido2PinUiConnection

logger = logging.getLogger(__name__)


@dataclass
class PinCache(QObject):
    uuid: Uuid | None = None
    pin: str | None = None

    pin_cached = Signal()
    pin_cleared = Signal()

    def __init__(self) -> None:
        super().__init__()

    @Slot()
    def clear(self) -> None:
        self.uuid = None
        self.pin = None
        self.pin_cleared.emit()

    def get(self, data: DeviceData) -> str | None:
        if data.uuid and self.uuid == data.uuid:
            return self.pin
        return None

    def update(self, data: DeviceData, pin: str) -> None:
        if not data.uuid:
            return
        self.uuid = data.uuid
        self.pin = pin
        self.pin_cached.emit()


class CheckDeviceJob(Job):
    device_checked = Signal(bool)

    def __init__(self, common_ui: CommonUi, data: DeviceData) -> None:
        super().__init__(common_ui)
        self.data = data
        self.device_checked.connect(lambda _: self.finished.emit())

    def run(self) -> None:
        compatible = False
        try:
            with self.data.open() as device:
                ctap2 = Ctap2(device.device)
                opts = ctap2.info.options or {}
                # FIDO2 credential management requires credMgmt or credentialMgmtPreview
                compatible = bool(opts.get("credMgmt") or opts.get("credentialMgmtPreview"))
        except Exception as e:
            logger.info(f"fido2 check device failed: {e}")
            compatible = False
        self.device_checked.emit(compatible)


class ListCredentialsJob(Job):
    credentials_listed = Signal(list)

    def __init__(
        self, common_ui: CommonUi, pin_cache: PinCache, pin_ui: Fido2PinUi, data: DeviceData
    ) -> None:
        super().__init__(common_ui)
        self.pin_cache = pin_cache
        self.pin_ui = pin_ui
        self.data = data
        self._pin_ui_conn: Fido2PinUiConnection | None = None

        self.credentials_listed.connect(lambda _: self.finished.emit())

    def cleanup(self) -> None:
        if self._pin_ui_conn is not None:
            self._pin_ui_conn.disconnect()
            self._pin_ui_conn = None

    def run(self) -> None:
        cached = self.pin_cache.get(self.data)
        if cached:
            self._do_list(cached)
            return

        retries = self._get_pin_retries()
        if retries is None:
            self.trigger_error("FIDO2 PIN is not set on this device")
            return

        self._pin_ui_conn = self.pin_ui.connect_actions(
            self._on_pin, lambda: self.credentials_listed.emit([])
        )
        self.pin_ui.query.emit(retries)

    def _get_pin_retries(self) -> int | None:
        try:
            with self.data.open() as device:
                ctap2 = Ctap2(device.device)
                if not ctap2.info.options.get("clientPin"):
                    return None
                client_pin = ClientPin(ctap2)
                return client_pin.get_pin_retries()[0]
        except Exception as e:
            logger.warning(f"failed to get fido2 pin retries: {e}")
            return None

    @Slot(str)
    def _on_pin(self, pin: str) -> None:
        self._do_list(pin, pin_was_queried=True)

    def _do_list(self, pin: str, pin_was_queried: bool = False) -> None:
        try:
            credentials = self._enumerate(pin)
        except CtapError as e:
            self.pin_cache.clear()
            self.trigger_error(f"FIDO2 PIN authentication failed: {e}")
            return
        except Exception as e:
            self.trigger_error(f"Failed to list FIDO2 credentials: {e}")
            return

        if pin_was_queried:
            self.pin_cache.update(self.data, pin)

        self.credentials_listed.emit(credentials)

    def _enumerate(self, pin: str) -> list[Fido2Credential]:
        with self.data.open() as device:
            ctap2 = Ctap2(device.device)
            client_pin = ClientPin(ctap2)
            token = client_pin.get_pin_token(pin, permissions=ClientPin.PERMISSION.CREDENTIAL_MGMT)
            cred_mgmt = CredentialManagement(ctap2, client_pin.protocol, token)

            metadata = cred_mgmt.get_metadata()
            existing = metadata.get(CredentialManagement.RESULT.EXISTING_CRED_COUNT, 0)
            if existing == 0:
                return []

            credentials: list[Fido2Credential] = []
            for rp_result in cred_mgmt.enumerate_rps():
                rp = rp_result.get(CredentialManagement.RESULT.RP) or {}
                rp_hash = rp_result.get(CredentialManagement.RESULT.RP_ID_HASH)
                rp_id = rp.get("id", "(unknown)")
                rp_name = rp.get("name")

                for cred in cred_mgmt.enumerate_creds(rp_hash):
                    cid = cred.get(CredentialManagement.RESULT.CREDENTIAL_ID) or {}
                    user = cred.get(CredentialManagement.RESULT.USER) or {}
                    credentials.append(
                        Fido2Credential(
                            rp_id=rp_id,
                            rp_name=rp_name,
                            user_id=user.get("id", b""),
                            user_name=user.get("name"),
                            user_display_name=user.get("displayName"),
                            credential_id=cid.get("id", b""),
                        )
                    )
            return credentials


class DeleteCredentialJob(Job):
    credential_deleted = Signal(object)

    def __init__(
        self,
        common_ui: CommonUi,
        pin_cache: PinCache,
        pin_ui: Fido2PinUi,
        data: DeviceData,
        credential: Fido2Credential,
    ) -> None:
        super().__init__(common_ui)
        self.pin_cache = pin_cache
        self.pin_ui = pin_ui
        self.data = data
        self.credential = credential
        self._pin_ui_conn: Fido2PinUiConnection | None = None

        self.credential_deleted.connect(lambda _: self.finished.emit())

    def cleanup(self) -> None:
        if self._pin_ui_conn is not None:
            self._pin_ui_conn.disconnect()
            self._pin_ui_conn = None

    def run(self) -> None:
        cached = self.pin_cache.get(self.data)
        if cached:
            self._do_delete(cached)
            return

        retries = self._get_pin_retries()
        if retries is None:
            self.trigger_error("FIDO2 PIN is not set on this device")
            return

        self._pin_ui_conn = self.pin_ui.connect_actions(
            self._on_pin, lambda: self.credential_deleted.emit(None)
        )
        self.pin_ui.query.emit(retries)

    def _get_pin_retries(self) -> int | None:
        try:
            with self.data.open() as device:
                ctap2 = Ctap2(device.device)
                if not ctap2.info.options.get("clientPin"):
                    return None
                client_pin = ClientPin(ctap2)
                return client_pin.get_pin_retries()[0]
        except Exception as e:
            logger.warning(f"failed to get fido2 pin retries: {e}")
            return None

    @Slot(str)
    def _on_pin(self, pin: str) -> None:
        self._do_delete(pin, pin_was_queried=True)

    def _do_delete(self, pin: str, pin_was_queried: bool = False) -> None:
        try:
            with self.data.open() as device:
                ctap2 = Ctap2(device.device)
                client_pin = ClientPin(ctap2)
                token = client_pin.get_pin_token(
                    pin, permissions=ClientPin.PERMISSION.CREDENTIAL_MGMT
                )
                cred_mgmt = CredentialManagement(ctap2, client_pin.protocol, token)
                descriptor = PublicKeyCredentialDescriptor(
                    type=PublicKeyCredentialType.PUBLIC_KEY, id=self.credential.credential_id
                )
                cred_mgmt.delete_cred(descriptor)
        except CtapError as e:
            self.pin_cache.clear()
            self.trigger_error(f"FIDO2 delete failed: {e}")
            return
        except Exception as e:
            self.trigger_error(f"Failed to delete FIDO2 credential: {e}")
            return

        if pin_was_queried:
            self.pin_cache.update(self.data, pin)

        self.common_ui.info.info.emit("FIDO2 credential deleted")
        self.credential_deleted.emit(self.credential)


class Fido2Worker(Worker):
    credentials_listed = Signal(list)
    credential_deleted = Signal(object)
    device_checked = Signal(bool)

    def __init__(self, common_ui: CommonUi, app_widget: QWidget) -> None:
        super().__init__(common_ui)
        self.pin_cache = PinCache()
        self.pin_ui = Fido2PinUi(app_widget)

    @Slot(DeviceData)
    def check_device(self, data: DeviceData) -> None:
        job = CheckDeviceJob(self.common_ui, data)
        job.device_checked.connect(self.device_checked)
        self.run(job)

    @Slot(DeviceData)
    def refresh_credentials(self, data: DeviceData) -> None:
        job = ListCredentialsJob(self.common_ui, self.pin_cache, self.pin_ui, data)
        job.credentials_listed.connect(self.credentials_listed)
        self.run(job)

    @Slot(DeviceData, object)
    def delete_credential(self, data: DeviceData, credential: Fido2Credential) -> None:
        job = DeleteCredentialJob(self.common_ui, self.pin_cache, self.pin_ui, data, credential)
        job.credential_deleted.connect(self.credential_deleted)
        self.run(job)
