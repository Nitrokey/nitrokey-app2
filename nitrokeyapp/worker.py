import inspect
import logging
from collections.abc import Callable, Generator
from contextlib import contextmanager
from functools import wraps
from typing import Any, TypeVar, cast

from PySide6.QtCore import QObject, Qt, Signal, Slot

from nitrokeyapp.common_ui import CommonUi

logger = logging.getLogger(__name__)

F = TypeVar("F", bound=Callable[..., Any])

POSITIONAL_KINDS = (inspect.Parameter.POSITIONAL_ONLY, inspect.Parameter.POSITIONAL_OR_KEYWORD)


def guarded_slot(*types: Any) -> Callable[[F], F]:
    """Slot decorator for job continuations.

    Qt calls a continuation straight from the event loop, so an exception in one
    would not be seen by Job.run_guarded. The job would never emit finished and
    the UI would stay busy until the app is restarted. Report the exception
    through the job instead, so it always ends with failed and finished.
    """

    def decorator(method: F) -> F:
        params = list(inspect.signature(method).parameters.values())
        positional = [p for p in params if p.kind in POSITIONAL_KINDS]
        takes_varargs = any(p.kind is p.VAR_POSITIONAL for p in params)
        limit = None if takes_varargs else len(positional) - 1

        @wraps(method)
        def wrapper(self: "Job", *args: Any, **kwargs: Any) -> None:
            try:
                method(self, *args[:limit], **kwargs)
            except Exception as e:
                self.trigger_exception(e)

        return cast(F, Slot(*types)(wrapper))

    return decorator


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

    def run_guarded(self) -> None:
        """Run the job, ending it with an error instead of letting exceptions escape."""
        try:
            self.run()
        except Exception as e:
            self.trigger_exception(e)

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
        job.run_guarded()

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

        job.finished.connect(
            lambda: self.busy_state_changed.emit(False), Qt.ConnectionType.SingleShotConnection
        )
        job.run_guarded()
