from PySide6 import QtCore, QtGui, QtWidgets
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
            QtUtilsMixIn.get_qicon("nitrokey.svg"),
            "Nitrokey 3: " f"{data.uuid_prefix}",
        )
        self.data = data
        # needs to create button in the vertical navigation with the nitrokey type and serial number as text
        # set material stylesheet if no system theme is set
        if not self.style().objectName() or self.style().objectName() == "fusion":
            apply_stylesheet(self, theme=get_theme_path())

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
        self.setText("")

    def unfold(self) -> None:
        self.setText("Nitrokey 3: " f"{str(self.data.uuid)[:5]}")
