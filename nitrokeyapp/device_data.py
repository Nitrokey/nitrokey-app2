import logging
from typing import TYPE_CHECKING

from pynitrokey.nk3 import Nitrokey3Device

from nitrokeyapp.information_box import InfoBox
from nitrokeyapp.update import Nk3Context

# TODO: This fixes a circular dependency, but should be avoided if possible
if TYPE_CHECKING:
    from nitrokeyapp.overview_tab import OverviewTab

logger = logging.getLogger(__name__)


class DeviceData:
    def __init__(self, device: Nitrokey3Device) -> None:
        self.device = device
        self.path = device.path
        self.uuid = device.uuid()
        self.version = device.version()
        self.updating = False

    def update(
        self,
        overview_tab: "OverviewTab",
        info_frame: InfoBox,
    ) -> None:
        try:
            self.updating = True
            Nk3Context(self.path).update(overview_tab, info_frame)
            self.updating = False
            logger.info("Successfully updated the Nitrokey 3")
            info_frame.set_text("Successfully updated the Nitrokey 3.")
        except Exception as e:
            self.updating = False
            logger.info(f"Failed to update Nitrokey 3 {e}")
            info_frame.set_text("Failed to update Nitrokey 3.")
