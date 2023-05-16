from typing import Protocol

from PyQt5.QtWidgets import QWidget

from nitrokeyapp.device_data import DeviceData


class DeviceView(Protocol):
    @property
    def title(self) -> str:
        ...

    @property
    def widget(self) -> QWidget:
        ...

    def reset(self) -> None:
        ...

    def refresh(self, data: DeviceData) -> None:
        ...
