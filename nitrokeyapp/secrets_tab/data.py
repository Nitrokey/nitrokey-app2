from dataclasses import dataclass
from datetime import datetime
from enum import Enum, auto, unique
from typing import Optional, Union

from pynitrokey.nk3.secrets_app import Kind as RawKind
from pynitrokey.nk3.secrets_app import ListItem, PasswordSafeEntry, SecretsApp

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


@dataclass
class OtpData:
    otp: str
    validity: Optional[tuple[datetime, datetime]] = None
