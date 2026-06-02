from base64 import b64decode, b64encode
from dataclasses import dataclass
from datetime import datetime
from enum import Enum, auto, unique
from typing import Optional, Union

from nitrokey.nk3.secrets_app import Kind as RawKind
from nitrokey.nk3.secrets_app import ListItem, PasswordSafeEntry, SecretsApp

# TODO: these could be moved into pynitrokey


@unique
class OtpKind(Enum):
    HOTP = auto()
    TOTP = auto()

    def __str__(self) -> str:
        return self.name

    def raw_kind(self) -> RawKind:
        if self == OtpKind.HOTP:
            return RawKind.Hotp
        elif self == OtpKind.TOTP:
            return RawKind.Totp
        else:
            raise RuntimeError(f"Unexpected OTP kind: {self}")

    @classmethod
    def from_str(cls, s: str) -> "OtpKind":
        for kind in OtpKind:
            if kind.name == s:
                return kind
        raise RuntimeError(f"Unexpected OTP kind: {kind}")


@unique
class OtherKind(Enum):
    REVERSE_HOTP = auto()
    HMAC = auto()

    def __str__(self) -> str:
        return self.name

    def raw_kind(self) -> RawKind:
        if self == OtherKind.HMAC:
            return RawKind.Hmac
        elif self == OtherKind.REVERSE_HOTP:
            return RawKind.HotpReverse
        else:
            raise RuntimeError(f"Unexpected OTP kind: {self}")

    @classmethod
    def from_str(cls, s: str) -> "OtherKind":
        for kind in OtherKind:
            if kind.name == s:
                return kind
        raise RuntimeError(f"Unexpected Other kind: {kind}")


Kind = Union[OtpKind, OtherKind]


def _kind_from_raw(kind: RawKind) -> Optional[Kind]:
    if kind == RawKind.Hmac:
        return OtherKind.HMAC
    elif kind == RawKind.Hotp:
        return OtpKind.HOTP
    elif kind == RawKind.HotpReverse:
        return OtherKind.REVERSE_HOTP
    elif kind == RawKind.Totp:
        return OtpKind.TOTP
    elif kind == RawKind.NotSet:
        return None
    else:
        raise RuntimeError(f"Unexpected credential kind: {kind}")


@dataclass
class Credential:
    id: bytes
    otp: Optional[OtpKind] = None
    other: Optional[OtherKind] = None
    login: Optional[bytes] = None
    password: Optional[bytes] = None
    comment: Optional[bytes] = None
    protected: bool = False
    touch_required: bool = False

    loaded: bool = False
    new_secret: bool = False

    @property
    def name(self) -> str:
        return self.id.decode(errors="replace")

    @classmethod
    def from_list_item(cls, item: ListItem) -> "Credential":
        credential = cls(
            id=item.label,
            protected=item.properties.secret_encryption,
            touch_required=item.properties.touch_required,
        )

        kind = _kind_from_raw(item.kind)
        if isinstance(kind, OtpKind):
            credential.otp = kind
        elif isinstance(kind, OtherKind):
            credential.other = kind

        return credential

    @classmethod
    def list(cls, secrets: SecretsApp) -> list["Credential"]:
        credentials = []
        for item in secrets.list_with_properties():
            credentials.append(cls.from_list_item(item))
        return credentials

    def extend_with_password_safe_entry(self, item: PasswordSafeEntry) -> "Credential":
        if item.login:
            self.login = item.login
        if item.password:
            self.password = item.password
        if item.metadata:
            self.comment = item.metadata
        self.loaded = True
        return self

    def serialize_credential(self) -> dict:
        if not self.loaded:
            raise RuntimeError("Cannot serialize credential which is not loaded yet")
        credential_dict = {
            "id": b64encode(self.id).decode(),
            "kind": self.otp.raw_kind().value
            if self.otp
            else self.other.raw_kind().value
            if self.other
            else RawKind.NotSet.value,
            "login": b64encode(self.login).decode() if self.login else "",
            "password": b64encode(self.password).decode() if self.password else "",
            "comment": b64encode(self.comment).decode() if self.comment else "",
            "protected": self.protected,
            "touch_required": self.touch_required,
        }
        return credential_dict

    @classmethod
    def deserialize_credential(cls, credential_dict: dict) -> "Credential":
        id = credential_dict.get("id", "")
        login = credential_dict.get("login", "")
        password = credential_dict.get("password", "")
        comment = credential_dict.get("comment", "")
        credential = cls(
            id=id,
            login=b64decode(login) if login else None,
            password=b64decode(password) if password else None,
            comment=b64decode(comment) if comment else None,
            protected=credential_dict.get("protected", False),
            touch_required=credential_dict.get("touch_required", False),
        )

        kind = _kind_from_raw(RawKind(credential_dict.get("kind")))
        if isinstance(kind, OtpKind):
            credential.otp = kind
        elif isinstance(kind, OtherKind):
            credential.other = kind

        return credential


@dataclass
class OtpData:
    otp: str
    validity: Optional[tuple[datetime, datetime]] = None
