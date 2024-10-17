import logging
from typing import List, Optional

from nitrokey import nk3
from nitrokey.nk3 import NK3, NK3Bootloader
from nitrokey.trussed import TrussedBase, TrussedDevice, Uuid, Version
from nitrokey.trussed.admin_app import Status

from nitrokeyapp.update import Nk3Context, UpdateGUI

logger = logging.getLogger(__name__)


class DeviceData:
    def __init__(self, device: TrussedBase) -> None:
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
        return isinstance(self._device, NK3Bootloader)

    @property
    def is_too_old(self) -> bool:
        if self.is_bootloader:
            return False

        try:
            assert self.name
            assert self.version
            assert self.status
            assert self.status.variant
            return False

        except Exception:
            return True

    @property
    def status(self) -> Status:
        assert isinstance(self._device, TrussedDevice)
        if not self._status:
            self._status = self._device.admin.status()
        return self._status

    @property
    def version(self) -> Version:
        assert isinstance(self._device, TrussedDevice)
        if not self._version:
            self._version = self._device.admin.version()

        return self._version

    @property
    def uuid(self) -> Optional[Uuid]:
        assert isinstance(self._device, TrussedDevice)
        if not self._uuid:
            self._uuid = self._device.uuid()
        return self._uuid

    @property
    def uuid_prefix(self) -> str:
        """
        The prefix of the UUID that is constant even when switching between
        stable and test firmware.
        """
        assert isinstance(self._device, TrussedDevice)
        return str(self.uuid)[:5]

    def open(self) -> NK3:
        device = NK3.open(self.path)
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
