# Copyright 2026 Nitrokey Developers
#
# Licensed under the Apache License, Version 2.0, <LICENSE-APACHE or
# http://apache.org/licenses/LICENSE-2.0> or the MIT license <LICENSE-MIT or
# http://opensource.org/licenses/MIT>, at your option. This file may not be
# copied, modified, or distributed except according to those terms.

import datetime
import logging
import os
from dataclasses import dataclass
from typing import Any, Optional, Sequence

from cryptography import x509
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec, rsa
from cryptography.hazmat.primitives.ciphers import Cipher, modes
from cryptography.hazmat.primitives.serialization import Encoding, pkcs12

try:
    from cryptography.hazmat.decrepit.ciphers.algorithms import TripleDES
except ImportError:
    from cryptography.hazmat.primitives.ciphers.algorithms import (
        TripleDES,  # type: ignore[no-reattr]
    )

logger = logging.getLogger(__name__)

DEFAULT_ADMIN_KEY = bytes.fromhex("010203040506070801020304050607080102030405060708")
NK3_ATR = bytes.fromhex("3B8F01805D4E6974726F6B657900000000006A")

# SELECT PIV APDU (matches pynitrokey's piv_app.py)
PIV_SELECT_APDU = [
    0x00,
    0xA4,
    0x04,
    0x00,
    0x0C,
    0xA0,
    0x00,
    0x00,
    0x03,
    0x08,
    0x00,
    0x00,
    0x10,
    0x00,
    0x01,
    0x00,
    0x00,
]

# Map from slot hex string to certificate container object ID
KEY_TO_CERT_OBJ_ID = {
    "9A": bytes.fromhex("5FC105"),
    "9C": bytes.fromhex("5FC10A"),
    "9D": bytes.fromhex("5FC10B"),
    "9E": bytes.fromhex("5FC101"),
}

MAIN_SLOTS = ["9A", "9C", "9D", "9E"]

SLOT_DISPLAY_NAMES = {
    "9A": "9A – Authentication",
    "9C": "9C – Digital Signature",
    "9D": "9D – Key Management",
    "9E": "9E – Card Authentication",
}

ALGORITHM_NAMES = {
    0x06: "RSA 1024",
    0x07: "RSA 2048",
    0x05: "RSA 3072",
    0x16: "RSA 4096",
    0x11: "ECC P-256",
    0x14: "ECC P-384",
}


# ─── TLV helpers (ported from pynitrokey/tlv.py) ─────────────────────────────


def _tlv_build_one(tag: int, data: bytes) -> bytes:
    if tag <= 0xFF:
        tag_bytes = bytes([tag])
    else:
        tag_bytes = bytes([(tag >> 8) & 0xFF, tag & 0xFF])

    length = len(data)
    if length <= 127:
        len_bytes = bytes([length])
    elif length <= 255:
        len_bytes = bytes([0x81, length])
    else:
        len_bytes = bytes([0x82, (length >> 8) & 0xFF, length & 0xFF])

    return tag_bytes + len_bytes + data


class Tlv:
    @staticmethod
    def build(items: Sequence[tuple[int, bytes]]) -> bytes:
        return b"".join(_tlv_build_one(tag, data) for tag, data in items)

    @staticmethod
    def parse(data: bytes) -> list[tuple[int, bytes]]:
        result = []
        i = 0
        while i < len(data):
            if data[i] in (0x00, 0xFF):
                i += 1
                continue

            tag = data[i]
            i += 1
            if (tag & 0x1F) == 0x1F:
                while i < len(data) and (data[i] & 0x80):
                    tag = (tag << 8) | data[i]
                    i += 1
                if i < len(data):
                    tag = (tag << 8) | data[i]
                    i += 1

            if i >= len(data):
                break

            lb = data[i]
            i += 1
            if lb == 0x81:
                length = data[i]
                i += 1
            elif lb == 0x82:
                length = (data[i] << 8) | data[i + 1]
                i += 2
            else:
                length = lb

            result.append((tag, data[i : i + length]))
            i += length

        return result


def find_by_id(tag: int, items: list[tuple[int, bytes]]) -> Optional[bytes]:
    for t, b in items:
        if t == tag:
            return b
    return None


# ─── Data classes ─────────────────────────────────────────────────────────────


@dataclass
class PivCertInfo:
    subject: str
    issuer: str
    serial: str
    not_before: str
    not_after: str

    @classmethod
    def from_der(cls, der: bytes) -> "PivCertInfo":
        cert = x509.load_der_x509_certificate(der)

        def _cn(name: x509.Name) -> str:
            try:
                return name.get_attributes_for_oid(x509.NameOID.COMMON_NAME)[0].value  # type: ignore[return-value]
            except Exception:
                return name.rfc4514_string()

        try:
            nb = cert.not_valid_before_utc.strftime("%Y-%m-%d")
            na = cert.not_valid_after_utc.strftime("%Y-%m-%d")
        except AttributeError:
            nb = cert.not_valid_before.strftime("%Y-%m-%d")  # type: ignore[attr-defined]
            na = cert.not_valid_after.strftime("%Y-%m-%d")  # type: ignore[attr-defined]

        return cls(
            subject=_cn(cert.subject),
            issuer=_cn(cert.issuer),
            serial=format(cert.serial_number, "X"),
            not_before=nb,
            not_after=na,
        )


@dataclass
class PivSlotInfo:
    slot_id: str
    display_name: str
    cert: Optional[PivCertInfo] = None

    @property
    def has_cert(self) -> bool:
        return self.cert is not None


# ─── PIV error ────────────────────────────────────────────────────────────────


class PivError(Exception):
    def __init__(self, status: int, message: str = "") -> None:
        self.status = status
        super().__init__(message or f"PIV error: {hex(status)}")

    @property
    def sw1(self) -> int:
        return (self.status >> 8) & 0xFF

    @property
    def sw2(self) -> int:
        return self.status & 0xFF

    @property
    def is_not_found(self) -> bool:
        return self.status == 0x6A82

    @property
    def is_wrong_pin(self) -> bool:
        return self.sw1 == 0x63

    @property
    def pin_retries(self) -> int:
        return self.sw2 & 0x0F if self.is_wrong_pin else 0


# ─── PivApp ───────────────────────────────────────────────────────────────────


class PivApp:
    """PIV APDU session over a smartcard (pyscard) connection."""

    def __init__(self, connection: Any) -> None:
        self._conn = connection
        self._select_piv()

    def close(self) -> None:
        try:
            self._conn.disconnect()
        except Exception:
            pass
        try:
            self._conn.release()
        except Exception:
            pass

    def __enter__(self) -> "PivApp":
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()

    @classmethod
    def open(cls) -> "PivApp":
        """Open a PIV session on the first NK3 found via smartcard interface."""
        try:
            from smartcard.Exceptions import (  # type: ignore[import-not-found,import-untyped]
                CardConnectionException,
                NoCardException,
            )
            from smartcard.ExclusiveTransmitCardConnection import (  # type: ignore[import-not-found,import-untyped]
                ExclusiveTransmitCardConnection,
            )
            from smartcard.System import (  # type: ignore[import-not-found,import-untyped]
                readers as list_readers,
            )
        except ImportError:
            raise PivError(0x0000, "pyscard is not installed. Run: pip install pyscard") from None

        nk3_atr = list(NK3_ATR)
        for reader in list_readers():
            raw = reader.createConnection()
            conn = ExclusiveTransmitCardConnection(raw)
            try:
                conn.connect()
            except (NoCardException, CardConnectionException):
                continue
            try:
                atr = conn.getATR()
            except (NoCardException, CardConnectionException):
                try:
                    conn.release()
                except Exception:
                    pass
                continue
            if atr != nk3_atr:
                conn.disconnect()
                try:
                    conn.release()
                except Exception:
                    pass
                continue
            try:
                return cls(conn)
            except Exception:
                try:
                    conn.disconnect()
                except Exception:
                    pass
                try:
                    conn.release()
                except Exception:
                    pass
                raise

        raise PivError(0x0000, "No NK3 device found via smartcard interface")

    def _select_piv(self) -> None:
        data, sw1, sw2 = self._conn.transmit(PIV_SELECT_APDU)
        while sw1 == 0x61:
            data, sw1, sw2 = self._conn.transmit([0x00, 0xC0, 0x00, 0x00, sw2 or 0xFF])
        if sw1 != 0x90 or sw2 != 0x00:
            raise PivError((sw1 << 8) | sw2, "Failed to select PIV application")

    def send_receive(self, ins: int, p1: int, p2: int, data: bytes = b"") -> bytes:
        header = [0x00, ins, p1, p2]
        if data:
            if len(data) > 255:
                lc: list[int] = [0x00, len(data) >> 8, len(data) & 0xFF]
            else:
                lc = [len(data)]
            apdu = header + lc + list(data)
        else:
            apdu = header

        result_list, sw1, sw2 = self._conn.transmit(apdu)
        result = bytes(result_list)

        while sw1 == 0x61:
            le = sw2 if sw2 != 0 else 0xFF
            more_list, sw1, sw2 = self._conn.transmit([0x00, 0xC0, 0x00, 0x00, le])
            result += bytes(more_list)

        if sw1 != 0x90 or sw2 != 0x00:
            raise PivError((sw1 << 8) | sw2)

        return result

    def authenticate_admin(self, admin_key: bytes = DEFAULT_ADMIN_KEY) -> None:
        """Mutual-authenticate with the management key (3DES or AES)."""
        if len(admin_key) == 24:
            from cryptography.hazmat.primitives.ciphers import algorithms as _alg

            algorithm: Any = TripleDES(admin_key)
            algo_byte = 0x03
            expected_len = 8
        elif len(admin_key) == 16:
            from cryptography.hazmat.primitives.ciphers import algorithms as _alg

            algorithm = _alg.AES128(admin_key)
            algo_byte = 0x08
            expected_len = 16
        elif len(admin_key) == 32:
            from cryptography.hazmat.primitives.ciphers import algorithms as _alg

            algorithm = _alg.AES256(admin_key)
            algo_byte = 0x0C
            expected_len = 16
        else:
            raise PivError(0x0000, f"Unsupported management key length: {len(admin_key)}")

        challenge_body = Tlv.build([(0x7C, Tlv.build([(0x80, b"")]))])
        challenge_response = self.send_receive(0x87, algo_byte, 0x9B, challenge_body)

        general_auth_data = find_by_id(0x7C, Tlv.parse(challenge_response))
        if general_auth_data is None:
            raise PivError(0x0000, "No 0x7C in GENERAL AUTHENTICATE response")

        challenge = find_by_id(0x80, Tlv.parse(general_auth_data))
        if challenge is None or len(challenge) != expected_len:
            raise PivError(0x0000, "No valid challenge in GENERAL AUTHENTICATE response")

        our_challenge = os.urandom(expected_len)
        cipher = Cipher(algorithm, mode=modes.ECB())

        decryptor = cipher.decryptor()
        response = decryptor.update(challenge) + decryptor.finalize()

        decryptor = cipher.decryptor()
        our_challenge_encrypted = decryptor.update(our_challenge) + decryptor.finalize()

        response_body = Tlv.build(
            [(0x7C, Tlv.build([(0x80, response), (0x81, our_challenge_encrypted)]))]
        )
        final_response = self.send_receive(0x87, algo_byte, 0x9B, response_body)

        general_auth_data = find_by_id(0x7C, Tlv.parse(final_response))
        if general_auth_data is None:
            raise PivError(0x0000, "No 0x7C in final GENERAL AUTHENTICATE response")

        decoded_challenge = find_by_id(0x82, Tlv.parse(general_auth_data))
        if decoded_challenge != our_challenge:
            raise PivError(0x0000, "Management key authentication failed")

    def login(self, pin: str) -> None:
        body = _encode_pin(pin)
        self.send_receive(0x20, 0x00, 0x80, body)

    def get_pin_retries(self) -> int:
        """Returns remaining PIN attempts, or -1 if unknown."""
        result_list, sw1, sw2 = self._conn.transmit([0x00, 0x20, 0x00, 0x80])
        if sw1 == 0x63:
            return sw2 & 0x0F
        if sw1 == 0x69 and sw2 == 0x83:
            return 0
        return -1

    def change_pin(self, old_pin: str, new_pin: str) -> None:
        body = _encode_pin(old_pin) + _encode_pin(new_pin)
        self.send_receive(0x24, 0x00, 0x80, body)

    def change_puk(self, old_puk: str, new_puk: str) -> None:
        old_puk_bytes = old_puk.encode("utf-8")
        new_puk_bytes = new_puk.encode("utf-8")
        if len(old_puk_bytes) != 8 or len(new_puk_bytes) != 8:
            raise ValueError("PUK must be exactly 8 characters")
        self.send_receive(0x24, 0x00, 0x81, old_puk_bytes + new_puk_bytes)

    def reset_retry_counter(self, puk: str, new_pin: str) -> None:
        puk_bytes = puk.encode("utf-8")
        if len(puk_bytes) != 8:
            raise ValueError("PUK must be exactly 8 characters")
        self.send_receive(0x2C, 0x00, 0x80, puk_bytes + _encode_pin(new_pin))

    def factory_reset(self) -> None:
        self.send_receive(0xFB, 0x00, 0x00)

    def cert(self, container_id: bytes) -> Optional[bytes]:
        """Return DER certificate from a slot, or None if empty."""
        payload = Tlv.build([(0x5C, container_id)])
        try:
            response = self.send_receive(0xCB, 0x3F, 0xFF, payload)
        except PivError as e:
            if e.is_not_found:
                return None
            raise

        parsed = Tlv.parse(response)
        outer = find_by_id(0x53, parsed)
        if outer is None:
            return None
        inner = find_by_id(0x70, Tlv.parse(outer))
        return inner

    def generate_key(self, key_ref: int, algo_id: bytes) -> bytes:
        """Generate a keypair; returns raw response containing public key TLV."""
        body = Tlv.build([(0xAC, Tlv.build([(0x80, algo_id)]))])
        return self.send_receive(0x47, 0x00, key_ref, body)

    def raw_sign(self, payload: bytes, key_ref: int, algo: int) -> bytes:
        body = Tlv.build([(0x7C, Tlv.build([(0x81, payload), (0x82, b"")]))])
        result = self.send_receive(0x87, algo, key_ref, body)
        general_auth_data = find_by_id(0x7C, Tlv.parse(result))
        if general_auth_data is None:
            raise PivError(0x0000, "No 0x7C in sign response")
        signature = find_by_id(0x82, Tlv.parse(general_auth_data))
        if signature is None:
            raise PivError(0x0000, "No signature in sign response")
        return signature

    def sign_p256(self, data: bytes, key_ref: int) -> bytes:
        digest = hashes.Hash(hashes.SHA256())
        digest.update(data)
        return self.raw_sign(digest.finalize(), key_ref, 0x11)

    def sign_p384(self, data: bytes, key_ref: int) -> bytes:
        digest = hashes.Hash(hashes.SHA384())
        digest.update(data)
        return self.raw_sign(digest.finalize(), key_ref, 0x14)

    def sign_rsa2048(self, data: bytes, key_ref: int) -> bytes:
        return self.raw_sign(_prepare_pkcs1v15_sha256(data), key_ref, 0x07)

    def generate_key_and_cert(
        self, key_ref: int, algo_id: bytes, pin: str, admin_key: bytes = DEFAULT_ADMIN_KEY
    ) -> None:
        """Generate a keypair and write a self-signed certificate to the slot."""
        response = self.generate_key(key_ref, algo_id)

        # NK3 resets PIN auth after key generation — re-login before signing
        self.login(pin)

        data = Tlv.parse(response)
        pub_key_tlv = find_by_id(0x7F49, data)
        if pub_key_tlv is None:
            raise PivError(0x0000, "No public key in generate key response")
        pub_key_data = Tlv.parse(pub_key_tlv)

        algo_byte = algo_id[0]
        not_before = datetime.datetime(2000, 1, 1, tzinfo=datetime.timezone.utc)
        not_after = datetime.datetime(2099, 1, 1, tzinfo=datetime.timezone.utc)

        if algo_byte in (0x11, 0x14):
            point = find_by_id(0x86, pub_key_data)
            if point is None:
                raise PivError(0x0000, "No EC point in generate key response")
            coord_size = 32 if algo_byte == 0x11 else 48
            raw = point[1:]  # strip 0x04 uncompressed marker
            curve: ec.EllipticCurve = ec.SECP256R1() if algo_byte == 0x11 else ec.SECP384R1()
            public_key_ecc = ec.EllipticCurvePublicNumbers(
                int.from_bytes(raw[:coord_size], "big"),
                int.from_bytes(raw[coord_size:], "big"),
                curve,
            ).public_key()
            hash_algo: Any = hashes.SHA256() if algo_byte == 0x11 else hashes.SHA384()
            signer: Any = _EccPivSigner(self, key_ref, public_key_ecc, algo_byte)
            cert = (
                x509.CertificateBuilder()
                .subject_name(x509.Name([]))
                .issuer_name(x509.Name([]))
                .not_valid_before(not_before)
                .not_valid_after(not_after)
                .serial_number(x509.random_serial_number())
                .public_key(public_key_ecc)
                .sign(signer, hash_algo)
            )
        elif algo_byte == 0x07:
            modulus_data = find_by_id(0x81, pub_key_data)
            exponent_data = find_by_id(0x82, pub_key_data)
            if modulus_data is None or exponent_data is None:
                raise PivError(0x0000, "No RSA key data in generate key response")
            public_key_rsa = rsa.RSAPublicNumbers(
                int.from_bytes(exponent_data, "big"), int.from_bytes(modulus_data, "big")
            ).public_key()
            signer = _RsaPivSigner(self, key_ref, public_key_rsa)
            cert = (
                x509.CertificateBuilder()
                .subject_name(x509.Name([]))
                .issuer_name(x509.Name([]))
                .not_valid_before(not_before)
                .not_valid_after(not_after)
                .serial_number(x509.random_serial_number())
                .public_key(public_key_rsa)
                .sign(signer, hashes.SHA256())
            )
        else:
            raise PivError(0x0000, f"Unsupported algorithm for cert generation: {hex(algo_byte)}")

        cert_der = cert.public_bytes(Encoding.DER)
        slot_id_hex = format(key_ref, "02X")
        self.write_certificate(slot_id_hex, cert_der)

    def import_rsa2048(
        self, key_ref: int, key: rsa.RSAPrivateNumbers, public_key: rsa.RSAPublicNumbers
    ) -> None:
        self.send_receive(
            0xFE,
            0x07,
            key_ref,
            Tlv.build(
                [
                    (0x01, key.p.to_bytes(128, "big")),
                    (0x02, key.q.to_bytes(128, "big")),
                    (0x03, public_key.e.to_bytes((public_key.e.bit_length() + 7) // 8, "big")),
                ]
            ),
        )

    def write_certificate(self, slot_id: str, cert_der: bytes) -> None:
        container_id = KEY_TO_CERT_OBJ_ID[slot_id.upper()]
        payload = Tlv.build(
            [(0x5C, container_id), (0x53, Tlv.build([(0x70, cert_der), (0x71, bytes([0]))]))]
        )
        self.send_receive(0xDB, 0x3F, 0xFF, payload)

    def import_p12(
        self,
        slot_id: str,
        p12_data: bytes,
        password: Optional[bytes],
        admin_key: bytes = DEFAULT_ADMIN_KEY,
    ) -> None:
        """Import a PKCS#12 file (RSA 2048 only) into a slot."""
        private_key, certificate, _ = pkcs12.load_key_and_certificates(p12_data, password)

        if not isinstance(private_key, rsa.RSAPrivateKey) or private_key.key_size != 2048:
            raise ValueError("Only RSA 2048 keys are supported for import")
        if certificate is None:
            raise ValueError("No certificate found in P12 file")

        key_ref = int(slot_id.upper(), 16)

        self.authenticate_admin(admin_key)
        self.import_rsa2048(
            key_ref, private_key.private_numbers(), private_key.public_key().public_numbers()
        )
        self._select_piv()
        self.authenticate_admin(admin_key)
        self.write_certificate(slot_id, certificate.public_bytes(Encoding.DER))

    def list_slots(self) -> list[PivSlotInfo]:
        """Return info for the four main PIV slots."""
        slots = []
        for slot_id in MAIN_SLOTS:
            container_id = KEY_TO_CERT_OBJ_ID[slot_id]
            cert_info: Optional[PivCertInfo] = None
            try:
                der = self.cert(container_id)
                if der:
                    try:
                        cert_info = PivCertInfo.from_der(der)
                    except Exception as e:
                        logger.warning(f"Failed to parse cert for slot {slot_id}: {e}")
            except PivError as e:
                logger.debug(f"Error reading slot {slot_id}: {e}")
            slots.append(
                PivSlotInfo(
                    slot_id=slot_id, display_name=SLOT_DISPLAY_NAMES[slot_id], cert=cert_info
                )
            )
        return slots


# ─── Helpers ──────────────────────────────────────────────────────────────────


def _encode_pin(pin: str) -> bytes:
    body = pin.encode("utf-8")
    if len(body) > 8:
        raise ValueError("PIN must be at most 8 characters")
    return body + bytes([0xFF] * (8 - len(body)))


def _prepare_pkcs1v15_sha256(data: bytes) -> bytes:
    digest = hashes.Hash(hashes.SHA256())
    digest.update(data)
    hashed = digest.finalize()
    prefix = bytes.fromhex("3031300d060960864801650304020105000420")
    padding_len = 256 - 32 - 19 - 3
    padding = b"\x00\x01" + (b"\xff" * padding_len) + b"\x00"
    total = padding + prefix + hashed
    assert len(total) == 256
    return total


# ─── PIV signing proxy classes (wrap device signing for cert generation) ──────


class _RsaPivSigner(rsa.RSAPrivateKey):
    def __init__(self, device: PivApp, key_ref: int, public_key: rsa.RSAPublicKey) -> None:
        self._device = device
        self._key_ref = key_ref
        self._public_key = public_key

    def public_key(self) -> rsa.RSAPublicKey:
        return self._public_key

    @property
    def key_size(self) -> int:
        return self._public_key.key_size

    def sign(self, data: bytes, padding: Any, algorithm: Any) -> bytes:
        return self._device.sign_rsa2048(data, self._key_ref)

    def decrypt(self, ciphertext: bytes, padding: Any) -> bytes:
        raise NotImplementedError

    def private_numbers(self) -> rsa.RSAPrivateNumbers:
        raise NotImplementedError

    def private_bytes(self, encoding: Any, format: Any, encryption_algorithm: Any) -> bytes:
        raise NotImplementedError

    def __copy__(self) -> "_RsaPivSigner":
        raise NotImplementedError

    def __deepcopy__(self, memo: Any) -> "_RsaPivSigner":
        raise NotImplementedError


class _EccPivSigner(ec.EllipticCurvePrivateKey):
    def __init__(
        self, device: PivApp, key_ref: int, public_key: ec.EllipticCurvePublicKey, algo_byte: int
    ) -> None:
        self._device = device
        self._key_ref = key_ref
        self._public_key = public_key
        self._algo_byte = algo_byte

    def public_key(self) -> ec.EllipticCurvePublicKey:
        return self._public_key

    @property
    def curve(self) -> ec.EllipticCurve:
        return self._public_key.curve

    @property
    def key_size(self) -> int:
        return self._public_key.key_size

    def sign(self, data: bytes, signature_algorithm: Any) -> bytes:
        if self._algo_byte == 0x11:
            return self._device.sign_p256(data, self._key_ref)
        return self._device.sign_p384(data, self._key_ref)

    def exchange(self, algorithm: Any, peer_public_key: Any) -> bytes:
        raise NotImplementedError

    def private_numbers(self) -> ec.EllipticCurvePrivateNumbers:
        raise NotImplementedError

    def private_bytes(self, encoding: Any, format: Any, encryption_algorithm: Any) -> bytes:
        raise NotImplementedError

    def __copy__(self) -> "_EccPivSigner":
        raise NotImplementedError

    def __deepcopy__(self, memo: Any) -> "_EccPivSigner":
        raise NotImplementedError
