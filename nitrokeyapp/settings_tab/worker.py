import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Optional

from pynitrokey.fido2 import find
from fido2.ctap2.base import Ctap2
from fido2.ctap2.pin import ClientPin, PinProtocol

from pynitrokey.nk3.secrets_app import SecretsApp, SecretsAppException
from pynitrokey.trussed.utils import Uuid
from PySide6.QtCore import QObject, Signal, Slot
from PySide6.QtWidgets import QWidget

from nitrokeyapp.common_ui import CommonUi
from nitrokeyapp.device_data import DeviceData
from nitrokeyapp.worker import Job, Worker

logger = logging.getLogger(__name__)



class SettingsWorker(Worker):
    # TODO: remove DeviceData from signatures


#class VerifyPinChangeJob(Job):

    def __init__(
        self,
        common_ui: CommonUi,
        data: DeviceData,
    ) -> None:
        super().__init__(common_ui)

        self.data = data

        @Slot(DeviceData, str, str)
        def otp_change_pw(DeviceData, old_pin: str, new_pin: str) -> None:
            print(old_pin, new_pin)

            with self.data.open() as device:
                secrets = SecretsApp(device)
                try:
                    with self.touch_prompt():
                        secrets.change_pin_raw(old_pin, new_pin)

                except SecretsAppException as e:
                    self.trigger_error(f"PIN validation failed: {e}")




#class UpdateDevice(Job):
#    device_updated = Signal(bool)
#
#    def __init__(
#        self,
#        common_ui: CommonUi,
#        data: DeviceData,
#    ) -> None:
#        super().__init__(common_ui)
#
#        self.data = data
#
#        self.image: Optional[str] = None
#
#        self.device_updated.connect(lambda _: self.finished.emit())
#
#        self.update_gui = UpdateGUI(self.common_ui)
#        self.common_ui.prompt.confirmed.connect(self.cancel_busy_wait)
#
#    def run(self) -> None:
#        if not self.image:
#            success = self.data.update(self.update_gui)
#        else:
#            success = self.data.update(self.update_gui, self.image)
#
#        self.device_updated.emit(success)
#
#    @Slot()
#    def cleanup(self) -> None:
#        self.common_ui.prompt.confirmed.disconnect()
#
#    @Slot(bool)
#    def cancel_busy_wait(self, confirmed: bool) -> None:
#        self.update_gui.await_confirmation = confirmed


#class SettingsWorker(Worker):
#    # TODO: remove DeviceData from signatures
#    device_updated = Signal(bool)
#
#    def __init__(self, common_ui: CommonUi) -> None:
#        super().__init__(common_ui)
#
   # @Slot(DeviceData)
   # def update_device(self, data: DeviceData) -> None:
   #     job = UpdateDevice(self.common_ui, data)
   #     job.device_updated.connect(self.device_updated)
   #     self.run(job)
#
   # @Slot(DeviceData, str)
   # def update_device_file(self, data: DeviceData, filename: str) -> None:
   #     job = UpdateDevice(self.common_ui, data)
   #     job.image = filename
   #     job.device_updated.connect(self.device_updated)
   #     self.run(job)
