import binascii
from base64 import b32decode
from typing import Optional

from PySide6.QtCore import Slot
from PySide6.QtWidgets import QDialog, QDialogButtonBox, QWidget

from nitrokeyapp.qt_utils_mix_in import QtUtilsMixIn
from nitrokeyapp.secrets_tab.data import Credential, OtpKind

# TODO:
# - max length
# - validate input
# - indicate missing/invalid fields

DEFAULT_OTP_KIND = OtpKind.TOTP


class AddSecretDialog(QtUtilsMixIn, QDialog):
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        QDialog.__init__(self, parent)
        QtUtilsMixIn.__init__(self)

        # self.ui === self -> this tricks mypy due to monkey-patching self
        self.ui = self.load_ui("add_secret_dialog.ui", self)

        for kind in OtpKind:
            self.ui.comboBoxOtpType.addItem(str(kind))
        self.ui.comboBoxOtpType.setCurrentText(str(DEFAULT_OTP_KIND))

        self.ui.lineEditName.textChanged.connect(lambda _: self.refresh())
        self.ui.lineEditOtpSecret.textChanged.connect(lambda _: self.refresh())

        self.refresh()

    @Slot()
    def refresh(self) -> None:
        errors = []

        if not self.ui.lineEditName.text():
            errors.append("Name must not be empty")

        secret = self.ui.lineEditOtpSecret.text()
        if not secret:
            errors.append("OTP Secret must not be empty")
        elif not is_base32(secret):
            errors.append("OTP Secret must be a valid Base32 string")

        is_ok = len(errors) == 0

        button = self.ui.buttonBox.button(QDialogButtonBox.StandardButton.Ok)
        button.setEnabled(is_ok)

        tooltip = ""
        if not is_ok:
            tooltip = "Please fix the following errors:"
            for error in errors:
                tooltip += f"\n- {error}"
        button.setToolTip(tooltip)

    def credential(self) -> Credential:
        name = self.ui.lineEditName.text()
        kind_str = self.ui.comboBoxOtpType.currentText()
        user_presence = self.ui.checkBoxUserPresence.isChecked()
        pin_protected = self.ui.checkBoxPinProtection.isChecked()
        assert name

        kind = OtpKind.from_str(kind_str)

        return Credential(
            id=name.encode(),
            otp=kind,
            protected=pin_protected,
            touch_required=user_presence,
        )

    def secret(self) -> bytes:
        otp_secret = self.ui.lineEditOtpSecret.text()
        assert otp_secret
        return parse_base32(otp_secret)


def parse_base32(s: str) -> bytes:
    n = len(s) % 8
    if n:
        s += (8 - n) * "="
    return b32decode(s, casefold=True)


def is_base32(s: str) -> bool:
    try:
        parse_base32(s)
        return True
    except binascii.Error:
        return False
