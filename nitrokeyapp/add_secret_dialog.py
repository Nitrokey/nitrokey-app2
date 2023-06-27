import binascii
from base64 import b32decode
from typing import Optional

from PyQt5.QtCore import pyqtSlot
from PyQt5.QtWidgets import QDialog, QDialogButtonBox, QWidget

from nitrokeyapp.secrets_tab.data import Credential, OtpKind
from nitrokeyapp.ui.add_secret_dialog import Ui_AddSecretDialog

# TODO:
# - max length
# - validate input
# - indicate missing/invalid fields

DEFAULT_OTP_KIND = OtpKind.TOTP


class AddSecretDialog(QDialog):
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)

        self.ui = Ui_AddSecretDialog()
        self.ui.setupUi(self)

        for kind in OtpKind:
            self.ui.comboBoxOtpType.addItem(str(kind))
        self.ui.comboBoxOtpType.setCurrentText(str(DEFAULT_OTP_KIND))

        self.ui.lineEditName.textChanged.connect(lambda _: self.refresh())
        self.ui.lineEditOtpSecret.textChanged.connect(lambda _: self.refresh())

        self.refresh()

    @pyqtSlot()
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
