# Copyright (c) 2021 Yubico AB
# All rights reserved.
#
#   Redistribution and use in source and binary forms, with or
#   without modification, are permitted provided that the following
#   conditions are met:
#
#    1. Redistributions of source code must retain the above copyright
#       notice, this list of conditions and the following disclaimer.
#    2. Redistributions in binary form must reproduce the above
#       copyright notice, this list of conditions and the following
#       disclaimer in the documentation and/or other materials provided
#       with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
# COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
# ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.


from .utils import websafe_decode
from .cose import CoseKey

from cryptography import x509
from cryptography.hazmat.backends import default_backend
from dataclasses import dataclass, fields, field as _field
from enum import Enum, unique
from datetime import date
from base64 import b64decode
from typing import Sequence, Mapping, Any, Optional

import json
import re


def _camel2snake(name: str) -> str:
    s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
    return re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1).lower()


def field(*, transform=lambda x: x, name: Optional[str] = None, **kwargs):
    return _field(metadata={"transform": transform, "name": name}, **kwargs)


class _DataObject:
    def __post_init__(self):
        for f in fields(self):
            transform = f.metadata.get("transform")
            value = getattr(self, f.name)
            if value:
                if transform:
                    setattr(self, f.name, transform(value))

    @classmethod
    def _wrap(cls, data: Optional[Mapping[str, Any]]):
        if data is None:
            return None
        if isinstance(data, cls):
            return data
        renames = {f.metadata.get("name"): f.name for f in fields(cls)}
        try:
            return cls(**{renames.get(k, _camel2snake(k)): v for k, v in data.items()})
        except Exception:
            print("error in ", cls, data.items(), renames)
            raise

    @classmethod
    def _wrap_list(cls, datas):
        return [cls._wrap(x) for x in datas] if datas is not None else None


@dataclass
class Version(_DataObject):
    major: int
    minor: int


@dataclass
class MetadataStatement(_DataObject):
    description: str
    authenticator_version: int = field()
    schema: int = field()
    upv: Sequence[Version] = field(transform=Version._wrap_list)
    attestation_types: Sequence[int] = field()
    user_verification_details: Sequence[Any] = field()  # TODO
    key_protection: int = field()
    matcher_protection: int = field()
    attachment_hint: int = field()
    tc_display: int = field()
    attestation_root_certificates: str = field()
    legal_header: Optional[str] = None
    aaid: Optional[str] = None
    aaguid: Optional[bytes] = field(
        transform=lambda x: bytes.fromhex(x.replace("-", "")), default=None
    )
    attestation_certificate_key_identifiers: Optional[Sequence[bytes]] = field(
        transform=lambda xs: [bytes.fromhex(x) for x in xs], default=None
    )
    alternative_descriptions: Optional[Mapping[str, str]] = None
    protocol_family: Optional[str] = None
    authentication_algorithms: Optional[Sequence[int]] = None
    public_key_alg_and_encodings: Optional[Sequence[int]] = None
    is_key_restricted: Optional[bool] = None
    is_fresh_user_verification_required: Optional[bool] = None
    crypto_strength: Optional[int] = None
    operating_env: Optional[str] = None
    tc_display_content_type: Optional[str] = None
    tc_display_png_characteristics: Optional[Any] = field(
        name="tcDisplayPNGCharacteristics", default=None
    )  # TODO
    ecdaa_trust_anchors: Optional[Any] = None  # TODO
    icon: Optional[str] = None
    supported_extensions: Optional[Sequence[Any]] = None  # TODO
    authenticator_get_info: Optional[Any] = None  # TODO


@dataclass
class RogueListEntry(_DataObject):
    sk: bytes
    date: int


@dataclass
class BiometricStatusReport(_DataObject):
    cert_level: int
    modality: str
    effective_date: int
    certification_descriptor: str
    certificate_number: str
    certification_policy_version: str
    certification_requirements_version: str


@unique
class AuthenticatorStatus(str, Enum):
    NOT_FIDO_CERTIFIED = "NOT_FIDO_CERTIFIED"
    FIDO_CERTIFIED = "FIDO_CERTIFIED"
    USER_VERIFICATION_BYPASS = "USER_VERIFICATION_BYPASS"
    ATTESTATION_KEY_COMPROMISE = "ATTESTATION_KEY_COMPROMISE"
    USER_KEY_REMOTE_COMPROMISE = "USER_KEY_REMOTE_COMPROMISE"
    USER_KEY_PHYSICAL_COMPROMISE = "USER_KEY_PHYSICAL_COMPROMISE"
    UPDATE_AVAILABLE = "UPDATE_AVAILABLE"
    REVOKED = "REVOKED"
    SELF_ASSERTION_SUBMITTED = "SELF_ASSERTION_SUBMITTED"
    FIDO_CERTIFIED_L1 = "FIDO_CERTIFIED_L1"
    FIDO_CERTIFIED_L1plus = "FIDO_CERTIFIED_L1plus"
    FIDO_CERTIFIED_L2 = "FIDO_CERTIFIED_L2"
    FIDO_CERTIFIED_L2plus = "FIDO_CERTIFIED_L2plus"
    FIDO_CERTIFIED_L3 = "FIDO_CERTIFIED_L3"
    FIDO_CERTIFIED_L3plus = "FIDO_CERTIFIED_L3plus"


@dataclass
class StatusReport(_DataObject):
    status: AuthenticatorStatus = field(transform=AuthenticatorStatus)
    effective_date: Optional[date] = field(transform=date.fromisoformat, default=None)
    authenticator_version: Optional[int] = None
    certificate: Optional[bytes] = field(transform=b64decode, default=None)
    url: Optional[str] = None
    certification_descriptor: Optional[str] = None
    certificate_number: Optional[str] = None
    certification_policy_version: Optional[str] = None
    certification_requirements_version: Optional[str] = None


@dataclass
class MetadataBlobPayloadEntry(_DataObject):
    status_reports: Sequence[StatusReport] = field(transform=StatusReport._wrap_list)
    time_of_last_status_change: date = field(transform=date.fromisoformat)
    aaid: Optional[str] = None
    aaguid: Optional[bytes] = field(
        transform=lambda x: bytes.fromhex(x.replace("-", "")), default=None
    )
    attestation_certificate_key_identifiers: Optional[Sequence[bytes]] = field(
        transform=lambda xs: [bytes.fromhex(x) for x in xs], default=None
    )
    metadata_statement: Optional[MetadataStatement] = field(
        transform=MetadataStatement._wrap, default=None
    )
    biometric_status_reports: Optional[Sequence[BiometricStatusReport]] = field(
        transform=BiometricStatusReport._wrap_list, default=None
    )
    rogue_list_url: Optional[str] = field(name="rogueListURL", default=None)
    rogue_list_hash: Optional[bytes] = field(transform=bytes.fromhex, default=None)


@dataclass
class MetadataBlobPayload(_DataObject):
    legal_header: str
    no: int
    next_update: date = field(transform=date.fromisoformat)
    entries: Sequence[MetadataBlobPayloadEntry] = field(
        transform=MetadataBlobPayloadEntry._wrap_list
    )


def parse_blob(blob: bytes, ca: bytes = None):
    message, signature_b64 = blob.rsplit(b".", 1)
    signature = websafe_decode(signature_b64)
    header, payload = (json.loads(websafe_decode(x)) for x in message.split(b"."))

    # TODO: Check that ca is in the header? Validate the chain?
    if not ca:
        ca = websafe_decode(header["x5c"][0])

    certificate = x509.load_der_x509_certificate(ca, default_backend())
    public_key = CoseKey.for_name(header["alg"]).from_cryptography_key(
        certificate.public_key()
    )
    public_key.verify(message, signature)

    return MetadataBlobPayload._wrap(payload)
