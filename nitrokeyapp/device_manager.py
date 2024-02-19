import logging
from typing import List

from nitrokeyapp.device_data import DeviceData

logger = logging.getLogger(__name__)


def match(lhs: DeviceData, rhs: DeviceData) -> bool:
    if lhs.path == rhs.path:
        if lhs.is_bootloader and rhs.is_bootloader:
            return True
        if lhs.uuid == rhs.uuid:
            return True
    return False


class DeviceManager:
    def __init__(self) -> None:
        self._devices: List[DeviceData] = []

    def count(self) -> int:
        return len(self._devices)

    def add(self) -> List[DeviceData]:
        try:
            all_devs = DeviceData.list()
        except Exception as e:
            logger.error(f"failed listing nk3 devices: {e}")
            return []

        new_devices = []
        for candidate in all_devs:
            res = list(filter(lambda x: match(x, candidate), self._devices))
            if len(res) > 0:
                org_dev = res[0]
                # keep the most recent `path` + `_device`
                org_dev.path = candidate.path
                org_dev._device = candidate._device
                continue
            self._devices.append(candidate)
            new_devices.append(candidate)

        return new_devices

    def remove(self) -> List[DeviceData]:
        try:
            all_devs = DeviceData.list()
        except Exception as e:
            logger.error(f"failed listing nk3 devices: {e}")
            return []

        out = []
        for dev in self._devices:
            res = list(filter(lambda x: match(x, dev), all_devs))
            if len(res) == 0:
                self._devices.remove(dev)
                out.append(dev)

        return out

    def update(self) -> None:
        pass
