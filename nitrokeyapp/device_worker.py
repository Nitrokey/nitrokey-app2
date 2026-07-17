import logging
from time import sleep

from PySide6.QtCore import QObject, Signal, Slot

from nitrokeyapp.device_data import DeviceData
from nitrokeyapp.device_manager import DeviceManager

logger = logging.getLogger(__name__)


class DeviceWorker(QObject):
    devices_updated = Signal(list)

    def __init__(self) -> None:
        super().__init__()
        self.device_manager = DeviceManager()

    @Slot()
    def detect_added_devices(self) -> None:
        if self._add():
            self._emit_devices()

    @Slot()
    def detect_removed_devices(self) -> None:
        devs = self.device_manager.remove()
        if not devs:
            logger.info("failed removing device")
            return

        logger.info(f"nk3 disconnected: {devs}")
        self._emit_devices()

    @Slot()
    def refresh_devices(self) -> None:
        self.device_manager.clear()
        self._add()
        self._emit_devices()

    def _add(self) -> list[DeviceData]:
        devs: list[DeviceData] = []
        for _tries in range(8):
            devs = self.device_manager.add()
            if devs:
                break
            sleep(0.25)

        if not devs:
            logger.info("failed adding device")
            return []

        logger.info(f"{len(devs)} nk3 device(s) connected:")
        for i, dev in enumerate(devs):
            logger.info(f"device #{i + 1}: {dev}")

        return devs

    def _emit_devices(self) -> None:
        self.devices_updated.emit(list(self.device_manager))
