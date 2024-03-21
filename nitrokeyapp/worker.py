from contextlib import contextmanager
from typing import Generator

from PySide6.QtCore import QObject, Signal, Slot

from nitrokeyapp.common_ui import CommonUi

# TODO: DeviceJob
# - connection management
# - handling unexpected errors


class Job(QObject):
    finished = Signal()

    def __init__(
        self,
        common_ui: CommonUi,
    ) -> None:
        super().__init__()

        self.common_ui = common_ui

        self.finished.connect(self.cleanup)

    def run(self) -> None:
        pass

    @Slot()
    def cleanup(self) -> None:
        pass

    @Slot(str)
    def trigger_error(self, msg: str) -> None:
        self.common_ui.info.error.emit(self.__class__.__name__ + str(Exception(msg)))
        self.finished.emit()

    @Slot(str, Exception)
    def trigger_exception(self, exc: Exception) -> None:
        self.common_ui.info.error.emit(self.__class__.__name__ + str(exc))
        self.finished.emit()

    def spawn(self, job: "Job") -> None:
        job.run()

    @contextmanager
    def touch_prompt(self) -> Generator[None, None, None]:
        try:
            self.common_ui.touch.start.emit()
            yield
        finally:
            self.common_ui.touch.stop.emit()


class Worker(QObject):
    # standard UI
    busy_state_changed = Signal(bool)

    def __init__(self, owner_common_ui: CommonUi) -> None:
        super().__init__()
        self.common_ui = owner_common_ui

    def run(self, job: Job) -> None:
        self.busy_state_changed.emit(True)

        job.finished.connect(lambda: self.busy_state_changed.emit(False))
        job.run()
