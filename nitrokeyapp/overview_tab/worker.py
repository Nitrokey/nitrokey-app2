import base64
import logging
from hashlib import sha256
from typing import Any, Tuple

from fido2.attestation.packed import PackedAttestation
from fido2.client import DefaultClientDataCollector, Fido2Client, UserInteraction, WebAuthnClient
from fido2.server import Fido2Server
from fido2.webauthn import (
    AttestationConveyancePreference,
    AttestationObject,
    AuthenticatorAttachment,
    PublicKeyCredentialRpEntity,
    PublicKeyCredentialUserEntity,
    UserVerificationRequirement,
)
from nitrokey.trussed import Fido2Certs, Transport, TrussedDevice
from nitrokey.trussed._connection.ctaphid import CtapHidConnection
from PySide6.QtCore import Signal, Slot

from nitrokeyapp.common_ui import CommonUi
from nitrokeyapp.device_data import DeviceData
from nitrokeyapp.update import UpdateGUI, UpdateResult
from nitrokeyapp.utils import get_transport
from nitrokeyapp.worker import Job, Worker

logger = logging.getLogger(__name__)

test_certs = [
    "c7d87cac86b69059bbff5c43872a20892267518614dfc9822c7ee55ad89f0022"
]  # Kept as a list so that we can add more test certs in future if needed


class UpdateDevice(Job):
    device_updated = Signal(UpdateResult)

    def __init__(self, common_ui: CommonUi, data: DeviceData, is_qubesos: bool) -> None:
        super().__init__(common_ui)

        self.data = data

        self.image: str | None = None
        self.is_qubesos = is_qubesos

        self.device_updated.connect(lambda _: self.finished.emit())

        self.update_gui = UpdateGUI(self.common_ui, data.model, self.is_qubesos)
        self.common_ui.prompt.confirmed.connect(self.cancel_busy_wait)

    def run(self) -> None:
        if not self.image:
            result = self.data.update(self.update_gui)
        else:
            result = self.data.update(self.update_gui, self.image)

        self.device_updated.emit(result)

    @Slot()
    def cleanup(self) -> None:
        self.common_ui.prompt.confirmed.disconnect()

    @Slot(bool)
    def cancel_busy_wait(self, confirmed: bool) -> None:
        self.update_gui.await_confirmation = confirmed


def verify_attestation(attestation_object: AttestationObject, client_data_hash: bytes) -> None:
    verifier = PackedAttestation()
    assert attestation_object.fmt == verifier.FORMAT
    verifier.verify(attestation_object.att_stmt, attestation_object.auth_data, client_data_hash)


class VerifyGenuine(Job):
    is_genuine = Signal(bool, str)

    def __init__(self, common_ui: CommonUi, data: DeviceData) -> None:
        super().__init__(common_ui)
        self.data = data

        self.is_genuine.connect(lambda _: self.finished.emit())

    def run(self) -> None:
        transport = get_transport()
        try:
            genuine = self._verify(transport)
        except Exception as e:
            self.trigger_error(f"Failed to verify device genuineness: {e}")
            return

        self.is_genuine.emit(genuine[0], genuine[1])

    def _verify(self, transport: Transport) -> Tuple[bool, str]:
        assert isinstance(self.data._device, TrussedDevice)
        touch = self.common_ui.touch

        class Interaction(UserInteraction):
            def prompt_up(self) -> None:
                touch.start.emit()

            def request_pin(self, permissions: Any, rd_id: str | None) -> str | None:
                raise ValueError("UV was discouraged")

            def request_uv(self, permissions: Any, rd_id: str | None) -> bool:
                return True

        client_data_collector = DefaultClientDataCollector(origin="https://example.com")
        if transport == Transport.CTAPHID:
            assert isinstance(self.data._device.connection, CtapHidConnection)
            fido2_client: WebAuthnClient = Fido2Client(
                device=self.data._device.connection.device,
                client_data_collector=client_data_collector,
                user_interaction=Interaction(),
            )
        else:
            try:
                from fido2.client.windows import WindowsClient

                fido2_client = WindowsClient(client_data_collector)
            except Exception as e:
                logger.warning(f"Unexpected state. This button should not have been enabled. {e}")

        firmware_version = self.data._device.admin.version()
        server = Fido2Server(
            PublicKeyCredentialRpEntity(id="example.com", name="Example RP"),
            attestation=AttestationConveyancePreference.DIRECT,
            verify_attestation=verify_attestation,
        )

        uv = UserVerificationRequirement.DISCOURAGED
        user = PublicKeyCredentialUserEntity(
            id=b"nitrokey_genuine_check", name="Nitrokey Genuine Check"
        )

        create_options, state = server.register_begin(
            user=user,
            user_verification=uv,
            authenticator_attachment=AuthenticatorAttachment.CROSS_PLATFORM,
        )

        try:
            make_credential_result = fido2_client.make_credential(create_options["publicKey"])
        except Exception:
            return False, "Client error or operation cancelled"

        touch.stop.emit()
        try:
            server.register_complete(state, make_credential_result)
        except ValueError as e:
            return False, str(e)
        except Exception:
            return False, "Bad signature"

        if "x5c" not in make_credential_result.response.attestation_object.att_stmt:
            return False, "Missing attestation certificate"

        cert = make_credential_result.response.attestation_object.att_stmt["x5c"]
        cert_hash = sha256(cert[0]).digest().hex()
        expected_certs = Fido2Certs.get(self.data._device.fido2_certs, firmware_version)
        if expected_certs and cert_hash in expected_certs.hashes:
            return True, "Verification successful"

        if cert_hash in test_certs:
            return False, "Nitrokey Test device"

        logger.warning(f"Unexpected cert hash {cert_hash}")
        logger.warning(f"Unexpected cert: {base64.urlsafe_b64encode(cert[0]).decode()}")
        return False, "Unexpected attestation certificate"


class OverviewWorker(Worker):
    # TODO: remove DeviceData from signatures
    device_updated = Signal(UpdateResult)
    genuine_device = Signal(bool, str)

    def __init__(self, common_ui: CommonUi) -> None:
        super().__init__(common_ui)

    @Slot(DeviceData, bool)
    def update_device(self, data: DeviceData, is_qubesos: bool) -> None:
        job = UpdateDevice(self.common_ui, data, is_qubesos)
        job.device_updated.connect(self.device_updated)
        self.run(job)

    @Slot(DeviceData, str, bool)
    def update_device_file(self, data: DeviceData, filename: str, is_qubesos: bool) -> None:
        job = UpdateDevice(self.common_ui, data, is_qubesos)
        job.image = filename
        job.device_updated.connect(self.device_updated)
        self.run(job)

    @Slot(DeviceData)
    def check_genuine(self, data: DeviceData) -> None:
        job = VerifyGenuine(self.common_ui, data)
        job.is_genuine.connect(self.genuine_device)
        self.run(job)
