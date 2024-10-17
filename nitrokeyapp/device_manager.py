import logging
from typing import Iterator, List

from nitrokeyapp.device_data import DeviceData

logger = logging.getLogger(__name__)


def match(lhs: DeviceData, rhs: DeviceData) -> bool:
    if lhs.path == rhs.path:
        if lhs.is_bootloader and rhs.is_bootloader:
            return True
        if lhs.uuid == rhs.uuid:
            return True
    elif lhs.path != rhs.path:
        if not lhs.is_bootloader and not rhs.is_bootloader:
            if lhs.uuid == rhs.uuid:
                return True
    return False


def test(devices: List[DeviceData]) -> bool:
    for dev in devices:
        if dev.is_bootloader:
            continue
        if dev.uuid is not None:
            continue
    return True


class DeviceManager:
    def __init__(self) -> None:
        self._devices: List[DeviceData] = []

    def __iter__(self) -> Iterator[DeviceData]:
        for item in self._devices:
            yield item

    def __len__(self) -> int:
        return len(self._devices)

    def clear(self) -> None:
        self._devices = []

    def add(self) -> List[DeviceData]:
        try:
            all_devs = DeviceData.list()
            test(all_devs)
        except Exception as e:
            logger.error(f"failed listing nk3 devices: {e}")
            return []

        new_devices = []
        for candidate in all_devs:
            # ignore bootloader device during update
            if (
                len(self._devices) == 1
                and self._devices[0].updating
                and candidate.is_bootloader
            ):
                continue

            # handle from bootloader-device updating
            if (
                len(self._devices) == 1
                and self._devices[0].is_bootloader
                and not candidate.is_bootloader
            ):
                self._devices[0].path = candidate.path
                self._devices[0]._device = candidate._device
                continue

            # typical case
            matched = False
            for my_dev in self._devices:
                try:
                    if match(my_dev, candidate):
                        my_dev.path = candidate.path
                        my_dev._device = candidate._device
                        matched = True
                        break
                except Exception:
                    return []

            if matched:
                continue

            # only actually add the device, if it was not consumed
            # to update an existing device
            self._devices.append(candidate)
            new_devices.append(candidate)

        return new_devices

    def remove(self) -> List[DeviceData]:
        try:
            all_devs = DeviceData.list()
            test(all_devs)
        except Exception as e:
            logger.error(f"failed listing nk3 devices: {e}")
            return []

        out = []
        for dev in self._devices:
            # skip any removal during device update
            if dev.updating:
                continue

            res = list(filter(lambda x: match(x, dev), all_devs))
            if len(res) == 0:
                self._devices.remove(dev)
                out.append(dev)

        return out
