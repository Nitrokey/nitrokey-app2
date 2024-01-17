import logging
from typing import Optional

from pynitrokey.nk3 import Nitrokey3Device

from nitrokeyapp.update import Nk3Context, UpdateGUI

logger = logging.getLogger(__name__)


class DeviceData:
    def __init__(self, device: Nitrokey3Device) -> None:
        self.path = device.path
        self.uuid = device.uuid()
        self.version = device.version()
        self.updating = False
        self.status = device.admin.status()

    @property
    def uuid_prefix(self) -> str:
        """
        The prefix of the UUID that is constant even when switching between
        stable and test firmware.
        """
        return str(self.uuid)[:5]

    def open(self) -> Nitrokey3Device:
        device = Nitrokey3Device.open(self.path)
        if device:
            return device
        else:
            # TODO: improve error handling
            raise RuntimeError(f"Failed to open device {self.uuid} at {self.path}")

    def update(
        self,
        ui: UpdateGUI,
        image: Optional[str] = None,
    ) -> bool:
        self.updating = True
        try:
            Nk3Context(self.path).update(ui, image)
            logger.info("Nitrokey 3 successfully updated")
            self.updating = False
            return True
        except Exception as e:
            logger.info(f"Nitrokey 3 failed to update - {e}")
            self.updating = False
            return False
