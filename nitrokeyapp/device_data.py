import logging
from typing import List, Optional

from pynitrokey import nk3
from pynitrokey.nk3.device import Nitrokey3Device
from pynitrokey.trussed.admin_app import Status
from pynitrokey.trussed.base import NitrokeyTrussedBase
from pynitrokey.trussed.device import NitrokeyTrussedDevice
from pynitrokey.trussed.utils import Uuid, Version

from nitrokeyapp.update import Nk3Context, UpdateGUI

logger = logging.getLogger(__name__)


class DeviceData:
    def __init__(self, device: NitrokeyTrussedBase) -> None:
        self.path = device.path
        self.updating = False

        self._status: Optional[Status] = None
        self._uuid: Optional[Uuid] = None
        self._version: Optional[Version] = None
        self._device = device

    @classmethod
    def list(cls) -> List["DeviceData"]:
        return [cls(dev) for dev in nk3.list()]

    @property
    def name(self) -> str:
        if self.is_bootloader:
            # desc = self.path.split("/")[-1]
            return "Nitrokey 3 (BL)"
        return f"Nitrokey 3: {self.uuid_prefix}"

    @property
    def is_bootloader(self) -> bool:
        return not isinstance(self._device, NitrokeyTrussedDevice)

    @property
    def status(self) -> Status:
        assert isinstance(self._device, NitrokeyTrussedDevice)
        if not self._status:
            self._status = self._device.admin.status()
        return self._status

    @property
    def version(self) -> Version:
        assert isinstance(self._device, NitrokeyTrussedDevice)
        if not self._version:
            self._version = self._device.admin.version()

        return self._version

    @property
    def uuid(self) -> Optional[Uuid]:
        assert isinstance(self._device, NitrokeyTrussedDevice)
        if not self._uuid:
            self._uuid = self._device.uuid()
        return self._uuid

    @property
    def uuid_prefix(self) -> str:
        """
        The prefix of the UUID that is constant even when switching between
        stable and test firmware.
        """
        assert isinstance(self._device, NitrokeyTrussedDevice)
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
