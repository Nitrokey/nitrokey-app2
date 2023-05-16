from pynitrokey.nk3 import Nitrokey3Device
from PyQt5 import QtGui, QtWidgets
from PyQt5.QtCore import QSize, pyqtSlot

from nitrokeyapp.information_box import InfoBox
from nitrokeyapp.overview_tab import OverviewTab
from nitrokeyapp.pynitrokey_for_gui import Nk3Context, nk3_update


class Nk3Button(QtWidgets.QWidget):
    list_nk3_keys: list["Nk3Button"] = []

    @classmethod
    def get(cls) -> list["Nk3Button"]:
        return Nk3Button.list_nk3_keys

    def __init__(
        self,
        device: Nitrokey3Device,
        nitrokeys_window: QtWidgets.QScrollArea,
        layout_nk_btns: QtWidgets.QVBoxLayout,
        nitrokey3_frame: QtWidgets.QFrame,
        overview_tab: OverviewTab,
        tabs: QtWidgets.QTabWidget,
        buttonLayout_nk3: QtWidgets.QHBoxLayout,
        info_frame: InfoBox,
    ) -> None:
        super().__init__()
        self.device = device
        self.uuid = self.device.uuid()
        self.path = self.device.path
        self.version = self.device.version()
        self.nitrokeys_window = nitrokeys_window
        self.layout_nk_btns = layout_nk_btns
        self.nitrokey3_frame = nitrokey3_frame
        self.buttonlayout_nk3 = buttonLayout_nk3
        self.tabs = tabs
        self.overview_tab = overview_tab
        self.info_frame = info_frame
        # needs to create button in the vertical navigation with the nitrokey type and serial number as text
        self.btn_nk3 = QtWidgets.QPushButton(
            QtGui.QIcon(":/images/icon/usb_new.png"),
            "Nitrokey 3: " f"{str(self.uuid)[:5]}",
        )
        self.btn_nk3.setFixedSize(184, 40)
        self.btn_nk3.setIconSize(QSize(20, 20))
        self.btn_nk3.clicked.connect(lambda: self.nk3_btn_pressed())
        self.btn_nk3.setStyleSheet(
            "border :4px solid ;"
            "border-color : #474642;"
            "border-width: 2px;"
            "border-radius: 5px;"
            "font-size: 14pt;"
        )
        # "font-weight: bold;")
        self.layout_nk_btns.addWidget(self.btn_nk3)
        self.widget_nk_btns = QtWidgets.QWidget()
        self.widget_nk_btns.setLayout(self.layout_nk_btns)
        self.nitrokeys_window.setWidget(self.widget_nk_btns)
        self.own_update_btn = QtWidgets.QPushButton("Update", self.nitrokey3_frame)
        self.own_update_btn.setGeometry(12, 134, 413, 27)
        self.buttonlayout_nk3.addWidget(self.own_update_btn)
        self.own_update_btn.hide()
        self.ctx = Nk3Context(self.device.path)
        self.own_update_btn.clicked.connect(
            lambda: nk3_update(
                self.ctx,
                self.overview_tab.ui.progressBar_Update,
                self.overview_tab.ui.progressBar_Download,
                self.overview_tab.ui.progressBar_Finalization,
                None,
                None,
                False,
                self.info_frame,
            )
        )
        Nk3Button.list_nk3_keys.append(self)

    @pyqtSlot()
    def nk3_btn_pressed(self) -> None:
        self.tabs.show()
        self.overview_tab.refresh(str(self.path), str(self.uuid), str(self.version))
        for button in Nk3Button.get():
            button.own_update_btn.hide()
        self.own_update_btn.show()

    def __del__(self) -> None:
        self.tabs.hide()
        self.nitrokeys_window.update()
        self.btn_nk3.close()
        self.own_update_btn.close()
        Nk3Button.list_nk3_keys.remove(self)

    def set_device(self, device: Nitrokey3Device) -> None:
        self.device = device
        self.uuid = self.device.uuid()
        self.path = self.device.path
        self.version = self.device.version()
        self.overview_tab.refresh(str(self.path), str(self.uuid), str(self.version))
        self.ctx = Nk3Context(self.device.path)
