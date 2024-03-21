from dataclasses import dataclass

from nitrokeyapp.information_box import InfoUi
from nitrokeyapp.progress_box import ProgressUi
from nitrokeyapp.prompt_box import PromptUi
from nitrokeyapp.touch import TouchUi


@dataclass
class CommonUi:
    touch: TouchUi
    info: InfoUi
    progress: ProgressUi
    prompt: PromptUi

    def __init__(self) -> None:
        self.touch = TouchUi()
        self.info = InfoUi()
        self.progress = ProgressUi()
        self.prompt = PromptUi()
