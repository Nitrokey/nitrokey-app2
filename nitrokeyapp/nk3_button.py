from PySide6 import QtWidgets
from qt_material import apply_stylesheet

from nitrokeyapp import get_theme_path
from nitrokeyapp.device_data import DeviceData
from nitrokeyapp.qt_utils_mix_in import QtUtilsMixIn


class Nk3Button(QtWidgets.QPushButton):
    def __init__(
        self,
        data: DeviceData,
    ) -> None:
        super().__init__(
            QtUtilsMixIn.get_qicon("usb_new.png"),
            "Nitrokey 3: " f"{str(data.uuid)[:5]}",
        )
        self.data = data
        # needs to create button in the vertical navigation with the nitrokey type and serial number as text
        # set material stylesheet if no system theme is set
        if not self.style().objectName() or self.style().objectName() == "fusion":
            apply_stylesheet(self, theme=get_theme_path())
