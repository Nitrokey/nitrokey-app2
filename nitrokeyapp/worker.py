import logging
from collections.abc import Generator
from contextlib import contextmanager

from PySide6.QtCore import QObject, Signal, Slot

from nitrokeyapp.common_ui import CommonUi

logger = logging.getLogger(__name__)

# TODO: DeviceJob
# - connection management
# - handling unexpected errors


class Job(QObject):
    finished = Signal()
    failed = Signal()

    def __init__(self, common_ui: CommonUi) -> None:
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
        logger.error(f"{self.__class__.__name__} failed: {msg}")
        self.common_ui.info.error.emit(f"{self.__class__.__name__}: {msg}")
        self.failed.emit()
        self.finished.emit()

    @Slot(Exception)
    def trigger_exception(self, exc: Exception) -> None:
        logger.error(f"{self.__class__.__name__} raised: {exc}", exc_info=exc)
        self.common_ui.info.error.emit(f"{self.__class__.__name__}: {exc}")
        self.failed.emit()
        self.finished.emit()

    def spawn(self, job: "Job") -> None:
        job.failed.connect(self.propagate_failure)
        job.run()

    @Slot()
    def propagate_failure(self) -> None:
        self.failed.emit()
        self.finished.emit()

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
        logger.info(f"{self.__class__.__name__} starting {job.__class__.__name__}")
        self.busy_state_changed.emit(True)

        job.finished.connect(lambda: self.busy_state_changed.emit(False))
        try:
            job.run()
        except Exception as e:
            job.trigger_exception(e)
