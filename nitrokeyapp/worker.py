from contextlib import contextmanager
from typing import Generator

from PySide6.QtCore import QObject, Signal, Slot

# TODO: DeviceJob
# - connection management
# - handling unexpected errors


class Job(QObject):
    finished = Signal()

    # standard UI
    error = Signal(str, Exception)
    start_touch = Signal()
    stop_touch = Signal()

    def __init__(self) -> None:
        super().__init__()

        self.finished.connect(self.cleanup)

    def run(self) -> None:
        pass

    @Slot()
    def cleanup(self) -> None:
        pass

    @Slot(str)
    def trigger_error(self, msg: str) -> None:
        self.error.emit(self.__class__.__name__, Exception(msg))
        self.finished.emit()

    @Slot(str, Exception)
    def trigger_exception(self, exc: Exception) -> None:
        self.error.emit(self.__class__.__name__, exc)
        self.finished.emit()

    def spawn(self, job: "Job") -> None:
        job.error.connect(self.error)
        job.start_touch.connect(self.start_touch)
        job.stop_touch.connect(self.stop_touch)
        job.run()

    @contextmanager
    def touch_prompt(self) -> Generator[None, None, None]:
        try:
            self.start_touch.emit()
            yield
        finally:
            self.stop_touch.emit()


class Worker(QObject):
    # standard UI
    busy_state_changed = Signal(bool)
    error = Signal(str, Exception)
    start_touch = Signal()
    stop_touch = Signal()

    def run(self, job: Job) -> None:
        self.busy_state_changed.emit(True)
        job.error.connect(self.error)
        job.start_touch.connect(self.start_touch)
        job.stop_touch.connect(self.stop_touch)
        job.finished.connect(lambda: self.busy_state_changed.emit(False))
        job.run()
