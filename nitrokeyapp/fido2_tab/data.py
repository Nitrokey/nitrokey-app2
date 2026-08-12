from dataclasses import dataclass, field

# COSE algorithm identifiers -> human readable names
# see https://www.iana.org/assignments/cose/cose.xhtml#algorithms
COSE_ALGORITHMS = {
    -7: "ES256",
    -8: "EdDSA",
    -35: "ES384",
    -36: "ES512",
    -37: "PS256",
    -38: "PS384",
    -39: "PS512",
    -257: "RS256",
    -258: "RS384",
    -259: "RS512",
    -65535: "RS1",
}

# credProtect policy values -> human readable names
# see CTAP 2.1, "Credential Protection (credProtect)"
CRED_PROTECT_POLICIES = {
    1: "User verification optional",
    2: "User verification optional (with credential list)",
    3: "User verification required",
}


@dataclass
class Fido2Credential:
    rp_id: str
    rp_name: str | None
    user_id: bytes
    user_name: str | None
    user_display_name: str | None
    credential_id: bytes
    algorithm: int | None = None
    cred_protect: int | None = None

    @property
    def rp_label(self) -> str:
        return self.rp_name or self.rp_id

    @property
    def user_label(self) -> str:
        return self.user_display_name or self.user_name or "(no name)"

    @property
    def algorithm_label(self) -> str | None:
        if self.algorithm is None:
            return None
        return COSE_ALGORITHMS.get(self.algorithm, str(self.algorithm))

    @property
    def cred_protect_label(self) -> str | None:
        if self.cred_protect is None:
            return None
        return CRED_PROTECT_POLICIES.get(self.cred_protect, str(self.cred_protect))

    @property
    def display(self) -> str:
        return f"{self.rp_label}: {self.user_label}"


@dataclass
class Fido2ListState:
    """Result of listing credentials, including device-wide slot metadata.

    ``valid`` is only set once the device metadata has actually been read; an
    aborted PIN entry yields the default (invalid) state so the UI can tell
    "no passkeys" apart from "we never got to look".
    """

    credentials: list[Fido2Credential] = field(default_factory=list)
    existing_count: int = 0
    remaining_count: int | None = None
    valid: bool = False

    @property
    def summary(self) -> str | None:
        """Short human-readable slot summary, or ``None`` when unknown.

        ``remaining_count`` is the authenticator's *maximum possible* remaining
        resident credentials, the real number can be lower depending on the
        algorithm of future keys, so it is shown as an upper bound.
        """
        if not self.valid:
            return None
        parts = [f"{self.existing_count} stored"]
        if self.remaining_count is not None:
            parts.append(f"up to {self.remaining_count} free")
        return "Passkeys: " + ", ".join(parts)
