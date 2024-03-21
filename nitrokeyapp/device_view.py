from typing import Optional, Protocol

from PySide6.QtWidgets import QWidget

from nitrokeyapp.common_ui import CommonUi
from nitrokeyapp.device_data import DeviceData
from nitrokeyapp.worker import Worker


class DeviceView(Protocol):
    @property
    def common_ui(self) -> CommonUi:
        ...

    @property
    def title(self) -> str:
        ...

    @property
    def widget(self) -> QWidget:
        ...

    @property
    def worker(self) -> Optional[Worker]:
        ...

    def reset(self) -> None:
        ...

    def refresh(self, data: DeviceData) -> None:
        ...
