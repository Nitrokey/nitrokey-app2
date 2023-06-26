from PyQt5.QtCore import QRectF, QSize, Qt
from PyQt5.QtGui import QPainter, QPainterPath, QPen
from PyQt5.QtWidgets import QWidget


class ClockProgressBar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._value = 0
        self._max = 100

    def setValue(self, value):
        self._value = value
        self.update()

    def setMaximum(self, max_value):
        self._max = max_value
        self.update()

    def value(self):
        return self._value

    def maximum(self):
        return self._max

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        size = min(self.width(), self.height())
        progress_radius = size / 4 - 2 - 10
        progress_x = (self.width() - 2 * progress_radius - 20) / 2
        progress_y = (self.height() - 2 * progress_radius - 20) / 2
        progress_rect = QRectF(
            progress_x, progress_y, 2 * progress_radius, 2 * progress_radius
        )
        progress_angle = self._value / self._max * 360
        painter.setPen(QPen(Qt.blue, 6, Qt.SolidLine))

        path = QPainterPath()
        path.arcMoveTo(progress_rect, -90)
        path.arcTo(progress_rect, -90, -progress_angle)
        painter.drawPath(path)

        painter.setPen(Qt.black)
        painter.setFont(self.font())

        text = str(self._value)
        text_width = painter.fontMetrics().width(text)
        text_height = painter.fontMetrics().height()

        text_x = int(self.width() / 2 - text_width / 2)
        text_y = int((self.height() + size) / 2 + text_height / 2)

        painter.drawText(text_x, text_y, text)

        painter.end()

    def sizeHint(self):
        progress_radius = min(self.width(), self.height()) / 4 - 2 - 10
        widget_size = int(progress_radius + 20)
        return QSize(widget_size, widget_size)
