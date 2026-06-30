from dataclasses import dataclass


@dataclass
class Fido2Credential:
    rp_id: str
    rp_name: str | None
    user_id: bytes
    user_name: str | None
    user_display_name: str | None
    credential_id: bytes

    @property
    def rp_label(self) -> str:
        return self.rp_name or self.rp_id

    @property
    def user_label(self) -> str:
        return self.user_display_name or self.user_name or "(no name)"

    @property
    def display(self) -> str:
        return f"{self.rp_label}: {self.user_label}"
