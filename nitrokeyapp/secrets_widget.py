from datetime import datetime
from typing import Optional

from PyQt5.QtCore import pyqtSlot
from PyQt5.QtWidgets import QInputDialog, QLineEdit, QMessageBox, QWidget

from pynitrokey.nk3 import Nitrokey3Device
from pynitrokey.nk3.secrets_app import SecretsApp

from nitrokeyapp.ui.secrets import Ui_SecretsWidget

# TODO: handle unhappy paths
# TODO: support PIN-less credentials only
# TODO: determine credential kind from List
# TODO: support adding credentials
# TODO: support deleting credentials
# TODO: indicate button press
# TODO: handle wrong channel
# TODO: active tab styling
# TODO: HOTP support
# TODO: TOTP period config


class SecretsWidget(QWidget):
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        QWidget.__init__(self, parent)

        self.ui = Ui_SecretsWidget()
        self.ui.setupUi(self)

        self.ui.pushButtonOtpGenerate.pressed.connect(self.generate_otp)
        self.ui.secretsList.currentTextChanged.connect(self.credential_changed)

        self.device: Optional[Nitrokey3Device] = None
        self.pin: Optional[str] = None
        self.initialized = False
        self.reset()

    def reset(self) -> None:
        self.ui.secretsList.clear()
        self.ui.credentialWidget.hide()
        self.ui.buttonDelete.setEnabled(False)

    def update_data(self) -> None:
        if not self.device:
            return
        if self.initialized:
            return

        self.reset()

        app = SecretsApp(self.device)
        select = app.select()
        print(select)

        if select.pin_attempt_counter is None:
            # TODO: fix
            raise Exception("PIN not set")
        if select.pin_attempt_counter == 0:
            # TODO: fix
            raise Exception("PIN blocked")

        (pin, ok) = QInputDialog.getText(
            self,
            "Enter Secrets PIN",
            f"Please enter your secrets PIN ({select.pin_attempt_counter} attempts left)",
            QLineEdit.EchoMode.Password,
        )
        if not ok:
            # TODO: fix
            raise Exception("cancelled")

        app.verify_pin_raw(pin)
        self.pin = pin

        for entry in app.list():
            self.ui.secretsList.addItem(entry.decode())

        self.initialized = True

    @pyqtSlot(str)
    def credential_changed(self, credential: str) -> None:
        self.ui.credentialWidget.show()
        # TODO: determine algorithm from list response
        self.ui.labelOtpAlgorithm.setText("TOTP")

    @pyqtSlot()
    def generate_otp(self) -> None:
        # TODO: handle OTP without PIN
        if not self.device:
            return
        if not self.pin:
            return
        credential_item = self.ui.secretsList.currentItem()
        if not credential_item:
            return
        # TODO: handle HOTP
        # TODO: make period configurable?
        credential_name = credential_item.text()
        app = SecretsApp(self.device)
        challenge = int(datetime.timestamp(datetime.now())) // 30
        app.verify_pin_raw(self.pin)
        otp = app.calculate(credential_name.encode(), challenge).decode()
        QMessageBox.information(
            self,
            f"One-Time Password for {credential_name}",
            otp,
        )
