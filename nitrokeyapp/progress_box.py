import logging
from dataclasses import dataclass
from typing import Callable, Optional

from PySide6.QtCore import QMetaObject, QObject, QTimer, Signal, Slot
from PySide6.QtWidgets import QProgressBar

logger = logging.getLogger(__name__)


class ProgressUi(QObject):
    start = Signal(str)
    stop = Signal()
    progress = Signal(int, int)

    # def __init__(self, parent: QObject) -> None:
    # super().__init__(parent)
    def __init__(self) -> None:
        super().__init__()

    def connect_ui(self, progress: "ProgressBox") -> None:
        self.start.connect(progress.show)
        self.progress.connect(progress.update)
        self.stop.connect(progress.hide)

    def connect_actions(
        self,
        start: Optional[Callable[[str], None]],
        stop: Optional[Callable[[], None]],
        progress: Optional[Callable[[int, int], None]],
    ) -> "ProgressUiConnection":
        con = ProgressUiConnection(self)
        if start:
            con.start = self.start.connect(start)
        if stop:
            con.stop = self.stop.connect(stop)
        if progress:
            con.progress = self.progress.connect(progress)
        return con


@dataclass
class ProgressUiConnection:
    progress_ui: ProgressUi
    start: Optional[QMetaObject.Connection] = None
    stop: Optional[QMetaObject.Connection] = None
    progress: Optional[QMetaObject.Connection] = None

    def disconnect_actions(self) -> None:
        if self.start:
            self.progress_ui.start.disconnect()
            self.start = None
        if self.stop:
            self.progress_ui.stop.disconnect()
            self.stop = None
        if self.progress:
            self.progress_ui.progress.disconnect()
            self.progress = None


class ProgressBox(QObject):
    def __init__(self, progress_bar: QProgressBar):
        super().__init__()

        self.progress_bar = progress_bar

        self.progress_bar.setTextVisible(True)

        # self.start.connect(self.show)
        # self.progress.connect(self.update)
        self.progress_bar.hide()
        self.progress_bar.setStyleSheet("color: #808080; font: bold;")

        self.hide_timer = QTimer(self)
        self.hide_timer.setSingleShot(True)
        self.hide_timer.setInterval(7000)
        self.hide_timer.timeout.connect(self.hide)

    @Slot(str)
    def show(self, txt: str) -> None:
        self.progress_bar.setFormat(f"{txt}: %p%")
        self.progress_bar.show()

    @Slot()
    def hide(self) -> None:
        self.progress_bar.hide()

    @Slot(int)
    def update(self, n: int, total: int) -> None:
        value = self.progress_bar.value()
        if n >= total:
            self.progress_bar.setValue(100)
            # self.progress_bar.hide()
        elif (n * 100 // total) > value:
            self.progress_bar.setValue((n * 100 // total))

        if self.hide_timer.isActive():
            self.hide_timer.stop()
        self.hide_timer.setInterval(7000)
        self.hide_timer.start()
