import logging
from typing import List, Optional

from nitrokey import nk3, nkpk
from nitrokey.nk3 import NK3
from nitrokey.nkpk import NKPK
from nitrokey.trussed import Model, TrussedBase, TrussedBootloader, TrussedDevice, Uuid, Version
from nitrokey.trussed.admin_app import Status

from nitrokeyapp.update import UpdateContext, UpdateGUI, UpdateResult, UpdateStatus

logger = logging.getLogger(__name__)


class DeviceData:
    def __init__(self, device: TrussedBase) -> None:
        self.path = device.path
        self.model = device.model
        self.updating = False

        self._status: Optional[Status] = None
        self._uuid: Optional[Uuid] = None
        self._version: Optional[Version] = None
        self._device = device

    def __repr__(self) -> str:
        fields = {
            "path": self.path,
            "is_bootloader": self.is_bootloader,
            "uuid": self._uuid,
            "status": self._status,
            "version": self._version,
            "updating": self.updating,
        }
        fields_str = ", ".join([f"{key}={value}" for key, value in fields.items()])
        return f"DeviceData({fields_str})"

    @classmethod
    def list(cls) -> List["DeviceData"]:
        nk3_devices = [cls(dev) for dev in nk3.list()]
        nkpk_devices = [cls(dev) for dev in nkpk.list()]
        return nk3_devices + nkpk_devices

    @property
    def name(self) -> str:
        if self.is_bootloader:
            # desc = self.path.split("/")[-1]
            return f"{self.model} (BL)"
        else:
            return f"{self.model}: {self.uuid_prefix}"

    @property
    def is_bootloader(self) -> bool:
        return isinstance(self._device, TrussedBootloader)

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

    def open(self) -> TrussedDevice:
        device: Optional[TrussedDevice] = None
        if self.model == Model.NK3:
            device = NK3.open(self.path)
        elif self.model == Model.NKPK:
            device = NKPK.open(self.path)

        if device:
            return device
        else:
            # TODO: improve error handling
            raise RuntimeError(f"Failed to open {self.model} device {self.uuid} at {self.path}")

    def update(self, ui: UpdateGUI, image: Optional[str] = None) -> UpdateResult:
        self.updating = True
        result = UpdateContext(self.path, self.model).update(ui, image)
        if result.status == UpdateStatus.SUCCESS:
            logger.info(f"{self.model} successfully updated")
        else:
            logger.error(f"{self.model} update failed: {result}")
        self.updating = False
        return result
