import html
from collections.abc import Callable

from PySide6 import QtCore, QtGui, QtWidgets

from nitrokeyapp.device_data import DeviceData
from nitrokeyapp.qt_utils_mix_in import QtUtilsMixIn

FOLDED_WIDTH = 58
FOLDED_ICON_SIZE = 40
UNFOLDED_WIDTH = 178
UNFOLDED_ICON_SIZE = 32
ICON_SPACING = 6


class Nk3Button(QtWidgets.QToolButton):
    def __init__(self, data: DeviceData, on_click: Callable[[DeviceData], None]) -> None:
        super().__init__()

        self.setIcon(QtUtilsMixIn.get_qicon("nitrokey.svg"))

        self.data = data
        self.bootloader_data: DeviceData | None = None
        self.folded = False
        self.device_tooltip = ""

        self.clicked.connect(lambda: on_click(self.data))

        self.setCheckable(True)
        self.setFocusPolicy(QtCore.Qt.FocusPolicy.NoFocus)

        self.set_stylesheet_small()

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

    def set_stylesheet_big(self) -> None:
        self.setStyleSheet(
            """
            QToolButton {
                background-color: transparent;
                border: 1px solid transparent;
                margin: 0; margin-top: 6px;
                padding: 0.3em 0.5em;
                border-radius: 6px;
                font-weight: 600; font-size: 9pt;
                color: #768390;
            }
            QToolButton:hover {
                background-color: rgba(192, 57, 43, 0.18);
                color: #ff8070;
            }
            QToolButton:checked {
                background-color: rgba(192, 57, 43, 0.18);
                border: 1px solid rgba(192, 57, 43, 0.5);
                color: #ff8070;
                font-weight: 600; font-size: 9pt;
            }
        """
        )
        self.refresh_text()

    def set_stylesheet_small(self) -> None:
        self.setStyleSheet(
            """
            QToolButton {
                background-color: transparent;
                border: 1px solid transparent;
                margin: 0; margin-top: 6px;
                padding: 0.3em 0.5em;
                border-radius: 6px;
                font-weight: 600; font-size: 8pt;
                color: #768390;
            }
            QToolButton:hover {
                background-color: rgba(192, 57, 43, 0.18);
                color: #ff8070;
            }
            QToolButton:checked {
                background-color: rgba(192, 57, 43, 0.18);
                border: 1px solid rgba(192, 57, 43, 0.5);
                color: #ff8070;
                font-weight: 600; font-size: 8pt;
            }
        """
        )
        self.refresh_text()

    def start_touch(self) -> None:
        self.animation.start()
        self.setToolTip("touch your Nitrokey 3")

    def stop_touch(self) -> None:
        self.animation.stop()
        self.setToolTip(self.device_tooltip)
        self.effect.setStrength(0)

    def fold(self) -> None:
        self.folded = True
        self.setMinimumWidth(FOLDED_WIDTH)
        self.setMaximumWidth(FOLDED_WIDTH)
        self.setIconSize(QtCore.QSize(FOLDED_ICON_SIZE, FOLDED_ICON_SIZE))
        self.setToolButtonStyle(QtCore.Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
        self.refresh_text()

    def unfold(self) -> None:
        self.folded = False
        self.setChecked(False)
        self.setMinimumWidth(UNFOLDED_WIDTH)
        self.setMaximumWidth(UNFOLDED_WIDTH)
        self.setIconSize(QtCore.QSize(UNFOLDED_ICON_SIZE, UNFOLDED_ICON_SIZE))
        self.setToolButtonStyle(QtCore.Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.refresh_text()

    def refresh_text(self) -> None:
        label = self.data.display_label
        if self.data.is_bootloader:
            text = "BL" if self.folded else self.data.name
        elif not label:
            text = self.data.uuid_prefix if self.folded else self.data.name.replace(": ", "\n")
        elif self.folded:
            text = self.elide(label)
        else:
            text = self.elide(label) + "\n" + self.data.uuid_prefix
        # a single "&" would be taken as a keyboard shortcut marker
        self.setText(text.replace("&", "&&"))

        if label:
            self.device_tooltip = f"<p>{html.escape(label)}<br>{html.escape(self.data.name)}</p>"
        else:
            self.device_tooltip = self.data.name
        self.setToolTip(self.device_tooltip)

    def elide(self, text: str) -> str:
        # the style sheet sets the font, a horizontal padding of 0.5em and a 1px border
        self.ensurePolished()
        frame = self.fontInfo().pixelSize() + 2
        if self.folded:
            width = FOLDED_WIDTH - frame
        else:
            width = UNFOLDED_WIDTH - frame - UNFOLDED_ICON_SIZE - ICON_SPACING
        return self.fontMetrics().elidedText(text, QtCore.Qt.TextElideMode.ElideRight, width)
