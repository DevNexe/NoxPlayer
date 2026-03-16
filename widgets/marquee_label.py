from PyQt5.QtWidgets import QLabel, QGraphicsScene, QGraphicsPixmapItem, QGraphicsBlurEffect
from PyQt5.QtCore import (Qt, QTimer, QPropertyAnimation, QEasingCurve,
                          QSequentialAnimationGroup, QPauseAnimation, pyqtProperty)
from PyQt5.QtGui import QPainter, QColor, QPen, QPainterPath, QFontMetrics, QPixmap, QImage
from PyQt5.QtCore import QRectF


class OutlineLabel(QLabel):
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self._outline_color = QColor(0, 0, 0)
        self._outline_width = 2
        self._blur_radius   = 0

    def setOutlineColor(self, color):
        self._outline_color = color
        self.update()

    def setOutlineWidth(self, width):
        self._outline_width = width
        self.update()

    def setOutlineBlurRadius(self, radius):
        self._blur_radius = radius
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        try:
            painter.setRenderHint(QPainter.Antialiasing)
            x_shift = self._text_x_offset if isinstance(self, MarqueeLabel) else 0

            metrics   = QFontMetrics(self.font())
            v_offset  = (self.height() - metrics.height()) / 2
            baseline  = metrics.ascent() + v_offset
            x_start   = self.contentsMargins().left()

            if not isinstance(self, MarqueeLabel):
                if self.alignment() & Qt.AlignHCenter:
                    x_start = (self.width() - metrics.horizontalAdvance(self.text())) / 2
                elif self.alignment() & Qt.AlignRight:
                    x_start = self.width() - metrics.horizontalAdvance(self.text()) - self.contentsMargins().right()

            path = QPainterPath()
            path.addText(x_start, baseline, self.font(), self.text())

            if self._blur_radius > 0:
                image = QImage(self.size(), QImage.Format_ARGB32_Premultiplied)
                image.fill(QColor(0, 0, 0, 0))
                sp = QPainter(image)
                try:
                    sp.setRenderHint(QPainter.Antialiasing)
                    sp.translate(x_shift, 0)
                    pen = QPen(self._outline_color)
                    pen.setWidthF(float(self._outline_width))
                    pen.setJoinStyle(Qt.RoundJoin)
                    sp.setPen(pen)
                    sp.setBrush(Qt.NoBrush)
                    sp.drawPath(path)
                finally:
                    if sp.isActive():
                        sp.end()

                scene = QGraphicsScene()
                item  = QGraphicsPixmapItem(QPixmap.fromImage(image))
                scene.addItem(item)
                eff = QGraphicsBlurEffect()
                eff.setBlurRadius(self._blur_radius)
                item.setGraphicsEffect(eff)

                blurred = QImage(self.size(), QImage.Format_ARGB32_Premultiplied)
                blurred.fill(QColor(0, 0, 0, 0))
                rp = QPainter(blurred)
                try:
                    rp.setRenderHint(QPainter.Antialiasing)
                    scene.render(rp, QRectF(self.rect()), QRectF(self.rect()))
                finally:
                    if rp.isActive():
                        rp.end()

                painter.drawPixmap(0, 0, QPixmap.fromImage(blurred))
                painter.translate(x_shift, 0)
            else:
                pen = QPen(self._outline_color)
                pen.setWidthF(float(self._outline_width))
                pen.setJoinStyle(Qt.RoundJoin)
                painter.setPen(pen)
                painter.setBrush(Qt.NoBrush)
                painter.translate(x_shift, 0)
                painter.drawPath(path)

            painter.setPen(Qt.NoPen)
            painter.setBrush(self.palette().brush(self.foregroundRole()))
            painter.drawPath(path)
        finally:
            if painter.isActive():
                painter.end()


class MarqueeLabel(OutlineLabel):
    _TEXT_X_PROPERTY = b"text_x_offset"

    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.animation      = None
        self._text_x_offset = 0.0
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self._start_animation)
        self.setContentsMargins(0, 0, 0, 0)
        self.setWordWrap(False)

    def _get_offset(self):   return self._text_x_offset
    def _set_offset(self, x):
        self._text_x_offset = x
        self.update()

    text_x_offset = pyqtProperty(float, _get_offset, _set_offset)

    def setText(self, text):
        super().setText(text)
        self._stop_animation()
        self._text_x_offset = 0.0
        self.timer.start(50)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._stop_animation()
        self._text_x_offset = 0.0
        self.timer.start(50)

    def _start_animation(self):
        if not self.isVisible() or self.width() < 20:
            return
        fm         = QFontMetrics(self.font())
        text_w     = fm.horizontalAdvance(self.text())
        label_w    = self.width() - self.contentsMargins().left() - self.contentsMargins().right()
        if text_w <= label_w:
            self._text_x_offset = 0.0
            self.update()
            return

        distance = text_w - label_w + 15
        duration = max(3000, int(distance * 80))
        self._stop_animation()

        def anim(start, end):
            a = QPropertyAnimation(self, self._TEXT_X_PROPERTY)
            a.setDuration(duration)
            a.setEasingCurve(QEasingCurve.Linear)
            a.setStartValue(float(start))
            a.setEndValue(float(end))
            return a

        self.animation = QSequentialAnimationGroup(self)
        self.animation.addAnimation(anim(0, -distance))
        self.animation.addAnimation(QPauseAnimation(1500))
        self.animation.addAnimation(anim(-distance, 0))
        self.animation.addAnimation(QPauseAnimation(1500))
        self.animation.setLoopCount(-1)
        self.animation.start()

    def _stop_animation(self):
        if self.animation and self.animation.state() == QPropertyAnimation.Running:
            self.animation.stop()
        self.animation = None
