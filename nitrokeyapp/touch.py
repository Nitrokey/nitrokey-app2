from typing import TYPE_CHECKING, Optional

from PySide6 import QtWidgets
from PySide6.QtCore import QObject, QTimer, Signal, Slot

from nitrokeyapp.information_box import InfoBox
from nitrokeyapp.nk3_button import Nk3Button

if TYPE_CHECKING:
    from nitrokeyapp.gui import GUI


class TouchUi(QObject):
    start = Signal()
    stop = Signal()

    def __init__(self) -> None:
        super().__init__()


class TouchIndicator(QtWidgets.QWidget):
    def __init__(self, info_box: InfoBox, parent: "GUI") -> None:
        super().__init__(parent)

        # TODO: pass proper type here instead of "all"
        self.owner = parent
        self.active_btn: Optional[Nk3Button] = None
        self.info_box = info_box

        # show status bar info 750ms late
        t = QTimer(self)
        t.setSingleShot(True)
        t.setInterval(750)
        t.timeout.connect(self.info_box.set_touch_status)
        self.info_box_timer: QTimer = t

    @Slot()
    def start(self) -> None:
        if self.active_btn:
            return

        self.info_box_timer.start()

        for btn in self.owner.device_buttons:
            if btn.data == self.owner.selected_device:
                self.active_btn = btn
                break

        if self.active_btn:
            self.active_btn.start_touch()

    @Slot()
    def stop(self) -> None:
        if self.active_btn:
            self.active_btn.stop_touch()
            self.active_btn = None

        if self.info_box_timer.isActive():
            self.info_box_timer.stop()
        self.info_box.hide_touch()
