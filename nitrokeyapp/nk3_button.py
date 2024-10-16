from typing import Optional

from PySide6 import QtCore, QtGui, QtWidgets

from nitrokeyapp.device_data import DeviceData
from nitrokeyapp.qt_utils_mix_in import QtUtilsMixIn


class Nk3Button(QtWidgets.QToolButton):
    def __init__(
        self,
        data: DeviceData,
    ) -> None:
        super().__init__()

        self.setIcon(QtUtilsMixIn.get_qicon("nitrokey.svg"))

        self.data = data
        self.bootloader_data: Optional[DeviceData] = None

        self.setCheckable(True)
        self.setFocusPolicy(QtCore.Qt.FocusPolicy.NoFocus)

        self.setStyleSheet(
            """
            QToolButton { background-color: none; border: none; margin: 0;
               margin-top: 8px; padding: 0.25em; border-radius: 6px; text-align: right;
                font: bold; font-size: 10px; border: 1px solid palette(button);
            }
            QToolButton:checked { background-color: palette(button);
                 border: 1px outset palette(shadow);
                 font: bold; font-size: 10px;
            }
        """
        )
        self.effect = QtWidgets.QGraphicsColorizeEffect(self)
        self.effect.setColor(QtGui.QColor(115, 215, 125))
        self.effect.setStrength(0)
        self.setGraphicsEffect(self.effect)

        anims = QtCore.QSequentialAnimationGroup()

        # self.animation = QtCore.QPropertyAnimation(effect, b"color")
        # self.animation.setStartValue(QtGui.QColor(QtCore.Qt.red))
        # self.animation.setEndValue(QtGui.QColor(155,155,155))

        anim1 = QtCore.QPropertyAnimation(self.effect, b"strength")
        anim1.setStartValue(0)
        anim1.setEndValue(1)
        anim1.setDuration(1000)
        anim1.setEasingCurve(QtCore.QEasingCurve.InOutCubic)  # type: ignore [attr-defined]

        anim2 = QtCore.QPropertyAnimation(self.effect, b"strength")
        anim2.setStartValue(1)
        anim2.setEndValue(0)
        anim2.setDuration(1000)
        anim2.setEasingCurve(QtCore.QEasingCurve.InOutCubic)  # type: ignore [attr-defined]

        anims.setLoopCount(30)
        anims.addAnimation(anim1)
        anims.addAnimation(anim2)

        self.animation = anims

    def start_touch(self) -> None:
        self.animation.start()
        self.setToolTip("touch your Nitrokey 3")

    def stop_touch(self) -> None:
        self.animation.stop()
        self.setToolTip("")
        self.effect.setStrength(0)

    def fold(self) -> None:
        self.setText(self.data.uuid_prefix)
        self.setMinimumWidth(58)
        self.setMaximumWidth(58)
        self.setIconSize(QtCore.QSize(40, 40))
        self.setToolButtonStyle(
            QtCore.Qt.ToolButtonStyle.ToolButtonTextUnderIcon
        )

    def unfold(self) -> None:
        self.setChecked(False)
        self.setText(self.data.name)
        self.setMinimumWidth(178)
        self.setMaximumWidth(178)
        self.setIconSize(QtCore.QSize(32, 32))
        self.setToolButtonStyle(
            QtCore.Qt.ToolButtonStyle.ToolButtonTextBesideIcon
        )
