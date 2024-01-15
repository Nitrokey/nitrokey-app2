import logging
from typing import TYPE_CHECKING, Optional

from pynitrokey.nk3 import Nitrokey3Device

from nitrokeyapp.information_box import InfoBox
from nitrokeyapp.update import Nk3Context

# TODO: This fixes a circular dependency, but should be avoided if possible
if TYPE_CHECKING:
    from nitrokeyapp.overview_tab import OverviewTab

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
        overview_tab: "OverviewTab",
        info_frame: InfoBox,
        image: Optional[str] = None,
    ) -> None:
        self.updating = True
        overview_tab.update_btns_during_update(False)
        try:
            Nk3Context(self.path).update(overview_tab, info_frame, image)
            logger.info("Successfully updated the Nitrokey 3")
            info_frame.set_status("Successfully updated the Nitrokey 3.")
        except Exception as e:
            logger.info(f"Failed to update Nitrokey 3 {e}")
            info_frame.set_status("Failed to update Nitrokey 3.")
        self.updating = False
        overview_tab.update_btns_during_update(True)
