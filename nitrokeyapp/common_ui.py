from dataclasses import dataclass

from PySide6.QtCore import QObject, Signal

from nitrokeyapp.information_box import InfoUi
from nitrokeyapp.progress_box import ProgressUi
from nitrokeyapp.prompt_box import PromptUi
from nitrokeyapp.touch import TouchUi


class GuiUi(QObject):
    refresh_devices = Signal()

    def __init__(self) -> None:
        super().__init__()


@dataclass
class CommonUi:
    touch: TouchUi
    info: InfoUi
    progress: ProgressUi
    prompt: PromptUi
    gui: GuiUi

    def __init__(self) -> None:
        self.touch = TouchUi()
        self.info = InfoUi()
        self.progress = ProgressUi()
        self.prompt = PromptUi()
        self.gui = GuiUi()
