import logging
from typing import Optional

from PySide6.QtCore import Signal, Slot

from nitrokeyapp.common_ui import CommonUi
from nitrokeyapp.device_data import DeviceData
from nitrokeyapp.update import UpdateGUI
from nitrokeyapp.worker import Job, Worker

logger = logging.getLogger(__name__)


class UpdateDevice(Job):
    device_updated = Signal(bool)

    def __init__(
        self,
        common_ui: CommonUi,
        data: DeviceData,
        is_qubesos: bool,
    ) -> None:
        super().__init__(common_ui)

        self.data = data

        self.image: Optional[str] = None
        self.is_qubesos = is_qubesos

        self.device_updated.connect(lambda _: self.finished.emit())

        self.update_gui = UpdateGUI(self.common_ui, self.is_qubesos)
        self.common_ui.prompt.confirmed.connect(self.cancel_busy_wait)

    def run(self) -> None:
        if not self.image:
            success = self.data.update(self.update_gui)
        else:
            success = self.data.update(self.update_gui, self.image)

        self.device_updated.emit(success)

    @Slot()
    def cleanup(self) -> None:
        self.common_ui.prompt.confirmed.disconnect()

    @Slot(bool)
    def cancel_busy_wait(self, confirmed: bool) -> None:
        self.update_gui.await_confirmation = confirmed


class OverviewWorker(Worker):
    # TODO: remove DeviceData from signatures
    device_updated = Signal(bool)

    def __init__(self, common_ui: CommonUi) -> None:
        super().__init__(common_ui)

    @Slot(DeviceData, bool)
    def update_device(self, data: DeviceData, is_qubesos: bool) -> None:
        job = UpdateDevice(self.common_ui, data, is_qubesos)
        job.device_updated.connect(self.device_updated)
        self.run(job)

    @Slot(DeviceData, str)
    def update_device_file(
        self, data: DeviceData, filename: str, is_qubesos: bool
    ) -> None:
        job = UpdateDevice(self.common_ui, data, is_qubesos)
        job.image = filename
        job.device_updated.connect(self.device_updated)
        self.run(job)
