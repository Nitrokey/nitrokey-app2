import logging
from typing import Any, List, Optional

from nitrokey import nk3
from nitrokey.nk3 import NK3, NK3Bootloader
from nitrokey.trussed import TrussedBase, TrussedDevice, Uuid, Version, should_default_ccid
from nitrokey.trussed.admin_app import Status

from nitrokeyapp.update import Nk3Context, UpdateGUI, UpdateResult, UpdateStatus

logger = logging.getLogger(__name__)


# Wrapper over the NK3 class that does not connect/disconnect on __enter__
# and __exit__.
#
# This allows keeping only one connection running for each device and not re-open
# the connection each time
class CcidNk3Wrapper(NK3):
    def __init__(self, inner: NK3) -> None:
        self.inner = inner

    def __getattribute__(self, name: str) -> Any:
        return getattr(self.inner, name)

    def __enter__(self) -> Any:
        return self

    def __exit__(self, exc_type: None, exc_val: None, exc_tb: None) -> None:
        pass


class DeviceData:
    def __init__(self, device: TrussedBase, using_ccid: bool) -> None:
        self.path = device.path
        self.updating = False

        self._status: Optional[Status] = None
        self._uuid: Optional[Uuid] = None
        self._version: Optional[Version] = None
        self._device = device
        self._using_ccid = using_ccid

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
        use_ccid = should_default_ccid()
        return [cls(dev, use_ccid) for dev in nk3.list(use_ccid, exclusive=False)]

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
        if not isinstance(self._device, NK3):
            raise RuntimeError("Trying to open a device that is a bootloader")

        if not self._using_ccid:
            device = NK3.clone(self._device, exclusive=True)
            if device:
                return device
            else:
                # TODO: improve error handling
                raise RuntimeError(f"Failed to open device {self.uuid} at {self.path}")
        else:
            return CcidNk3Wrapper(self._device)

    def update(self, ui: UpdateGUI, image: Optional[str] = None) -> UpdateResult:
        self.updating = True
        if self.path is None:
            return UpdateResult(
                UpdateStatus.ERROR, "Administrator rights are required for updating"
            )
        result = Nk3Context(self.path).update(ui, image)
        if result.status == UpdateStatus.SUCCESS:
            logger.info("Nitrokey 3 successfully updated")
        else:
            logger.error(f"Nitrokey 3 update failed: {result}")
        self.updating = False
        return result
