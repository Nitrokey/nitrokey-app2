from contextlib import contextmanager
from typing import Generator

from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot

# TODO: DeviceJob
# - connection management
# - handling unexpected errors


class Job(QObject):
    finished = pyqtSignal()

    # standard UI
    error = pyqtSignal(str)
    start_touch = pyqtSignal()
    stop_touch = pyqtSignal()

    def __init__(self) -> None:
        super().__init__()

        self.finished.connect(self.cleanup)

    def run(self) -> None:
        pass

    @pyqtSlot()
    def cleanup(self) -> None:
        pass

    @pyqtSlot(str)
    def trigger_error(self, msg: str) -> None:
        self.error.emit(msg)
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
    busy_state_changed = pyqtSignal(bool)
    error = pyqtSignal(str)
    start_touch = pyqtSignal()
    stop_touch = pyqtSignal()

    def run(self, job: Job) -> None:
        self.busy_state_changed.emit(True)
        job.error.connect(self.error)
        job.start_touch.connect(self.start_touch)
        job.stop_touch.connect(self.stop_touch)
        job.finished.connect(lambda: self.busy_state_changed.emit(False))
        job.run()
