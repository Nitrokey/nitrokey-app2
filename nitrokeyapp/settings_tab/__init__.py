import binascii
import logging
from base64 import b32decode, b32encode
from enum import Enum
from random import randbytes
from typing import Callable, Optional

from PySide6.QtCore import Qt, QThread, QTimer, Signal, Slot
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import QLineEdit, QListWidgetItem, QWidget

from nitrokeyapp.common_ui import CommonUi
from nitrokeyapp.device_data import DeviceData
from nitrokeyapp.qt_utils_mix_in import QtUtilsMixIn
from nitrokeyapp.worker import Worker

from .worker import SettingsWorker

# logger = logging.getLogger(__name__)

# class SettingsTabState(Enum):
#    Initial = 0
#    ShowCred = 1
#   AddCred = 2
#   EditCred = 3
#
#   NotAvailable = 99


class SettingsTab(QtUtilsMixIn, QWidget):
    # standard UI
    #    busy_state_changed = Signal(bool)
    #    error = Signal(str, Exception)
    #    start_touch = Signal()
    #    stop_touch = Signal()

    # worker triggers
    #    trigger_add_credential = Signal(DeviceData, Credential, bytes)

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        QWidget.__init__(self, parent)
        QtUtilsMixIn.__init__(self)

        self.data: Optional[DeviceData] = None
        self.common_ui = CommonUi()

        self.worker_thread = QThread()
        self._worker = SettingsWorker(self.common_ui)
        self._worker.moveToThread(self.worker_thread)
        self.worker_thread.start()

        self.ui = self.load_ui("settings_tab.ui", self)

    @property
    def title(self) -> str:
        return "Settings"

    @property
    def widget(self) -> QWidget:
        return self.ui

    @property
    def worker(self) -> Optional[Worker]:
        return self._worker

    def reset(self) -> None:
        self.data = None

    def refresh(self, data: DeviceData, force: bool = False) -> None:
        if data == self.data and not force:
            return
        self.reset()
        self.data = data

    def set_device_data(
        self, path: str, uuid: str, version: str, variant: str, init_status: str
    ) -> None:
        self.ui.nk3_path.setText(path)
        self.ui.nk3_uuid.setText(uuid)
        self.ui.nk3_version.setText(version)
        self.ui.nk3_variant.setText(variant)
        self.ui.nk3_status.setText(init_status)
