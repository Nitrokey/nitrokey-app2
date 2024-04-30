import logging

from PySide6.QtCore import QObject, QTimer, Signal, Slot
from PySide6.QtWidgets import QProgressBar

logger = logging.getLogger(__name__)


class ProgressUi(QObject):
    start = Signal(str)
    stop = Signal()
    progress = Signal(int, int)

    def __init__(self) -> None:
        super().__init__()


class ProgressBox(QObject):
    def __init__(self, progress_bar: QProgressBar):
        super().__init__()

        self.progress_bar = progress_bar

        self.progress_bar.setTextVisible(True)

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
        self.progress_bar.setValue(0)

    @Slot(int)
    def update(self, n: int, total: int) -> None:
        self.progress_bar.show()
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
