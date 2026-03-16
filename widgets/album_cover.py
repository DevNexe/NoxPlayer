from PyQt5.QtWidgets import QWidget, QGraphicsScene, QGraphicsPixmapItem, QGraphicsBlurEffect
from PyQt5.QtCore import Qt, QRectF, QRect
from PyQt5.QtGui import (QPainter, QLinearGradient, QColor, QBrush, QPen,
                         QPainterPath, QPixmap, QImage, QFont)


class AlbumCover(QWidget):
    def __init__(self, radius=16, cover_ratio=0.7, blur_radius=30,
                 is_playlist_item=False, vertical_offset_ratio=0.22):
        super().__init__()
        self.radius               = radius
        self.cover_ratio          = cover_ratio
        self.blur_radius          = blur_radius
        self.is_playlist_item     = is_playlist_item
        self.vertical_offset_ratio = vertical_offset_ratio
        self.album_pixmap         = None
        self._blur_cache          = None

    def set_cover(self, pixmap):
        if pixmap is None:
            self.album_pixmap = None
        elif isinstance(pixmap, QImage):
            self.album_pixmap = QPixmap.fromImage(pixmap)
        elif isinstance(pixmap, QPixmap):
            self.album_pixmap = pixmap
        else:
            try:
                qimg = QImage.fromData(pixmap)
                self.album_pixmap = QPixmap.fromImage(qimg) if not qimg.isNull() else None
            except Exception:
                self.album_pixmap = None
        self._blur_cache = None
        self.update()

    def _blurred_bg(self, target_size):
        if not self.album_pixmap or self.album_pixmap.isNull():
            return None
        eff_blur = self.blur_radius / 2.0
        key = (target_size.width(), target_size.height(), eff_blur)
        if self._blur_cache and self._blur_cache[0] == key:
            return self._blur_cache[1]

        margin = max(8, int(eff_blur * 2))
        tw, th = target_size.width() + margin*2, target_size.height() + margin*2
        scaled = self.album_pixmap.scaled(tw, th, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)

        tmp = QImage(tw, th, QImage.Format_ARGB32)
        tmp.fill(QColor(15, 23, 42))
        p = QPainter(tmp)
        try:
            p.setRenderHint(QPainter.SmoothPixmapTransform)
            p.drawPixmap((tw - scaled.width()) // 2, (th - scaled.height()) // 2, scaled)
        finally:
            if p.isActive(): p.end()

        scene = QGraphicsScene()
        item  = QGraphicsPixmapItem(QPixmap.fromImage(tmp))
        item.setPos(0, 0)
        scene.addItem(item)
        scene.setSceneRect(0, 0, tw, th)
        blur = QGraphicsBlurEffect()
        blur.setBlurRadius(eff_blur)
        item.setGraphicsEffect(blur)

        out = QImage(tw, th, QImage.Format_ARGB32)
        out.fill(QColor(0, 0, 0, 0))
        p2 = QPainter(out)
        try:
            p2.setRenderHint(QPainter.Antialiasing)
            scene.render(p2, QRectF(0, 0, tw, th), QRectF(0, 0, tw, th))
        finally:
            if p2.isActive(): p2.end()

        cx = (tw - target_size.width()) // 2
        cy = (th - target_size.height()) // 2
        px = QPixmap.fromImage(out.copy(cx, cy, target_size.width(), target_size.height()))
        self._blur_cache = (key, px)
        return px

    def paintEvent(self, event):
        painter = QPainter(self)
        try:
            painter.setRenderHint(QPainter.Antialiasing)
            painter.setRenderHint(QPainter.SmoothPixmapTransform)
            w, h = float(self.width()), float(self.height())

            main_path = QPainterPath()
            main_path.addRoundedRect(QRectF(0, 0, w, h), self.radius, self.radius)

            painter.save()
            painter.setClipPath(main_path)
            grad = QLinearGradient(0, 0, w, h)
            grad.setColorAt(0.0, QColor(45, 55, 75))
            grad.setColorAt(1.0, QColor(10, 15, 20))
            painter.fillRect(self.rect(), QBrush(grad))
            blurred = self._blurred_bg(self.size())
            if blurred and not blurred.isNull():
                painter.setOpacity(0.6)
                painter.drawPixmap(0, 0, blurred)
                painter.setOpacity(1.0)
            painter.restore()

            size = int(min(w, h) * self.cover_ratio)
            cx   = (w - size) / 2.0
            if self.is_playlist_item:
                cy = (h - size) / 2.0
            else:
                cy = max(20.0, (h - size) * self.vertical_offset_ratio)
            cover_rect = QRectF(cx, cy, float(size), float(size))

            if self.album_pixmap and not self.album_pixmap.isNull():
                sp = QPainterPath()
                sp.addRoundedRect(cover_rect.adjusted(2, 6, 2, 6), 12, 12)
                painter.fillPath(sp, QColor(0, 0, 0, 180))

                cp = QPainterPath()
                cp.addRoundedRect(cover_rect, 12, 12)
                painter.save()
                painter.setClipPath(cp)
                sc = self.album_pixmap.scaled(int(size), int(size),
                    Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
                src = QRect((sc.width()-size)//2, (sc.height()-size)//2, size, size)
                painter.drawPixmap(cover_rect.toRect(), sc, src)
                painter.restore()
                painter.setPen(QPen(QColor(255, 255, 255, 30), 1))
                painter.drawRoundedRect(cover_rect, 12, 12)
            else:
                ir = QRectF(cx, (h - size) / 2.0, float(size), float(size))
                painter.setFont(QFont("Material Symbols Rounded", int(size * 0.5)))
                painter.setPen(QColor(255, 255, 255, 200))
                painter.drawText(ir, Qt.AlignCenter, "\ue405")
        except Exception as e:
            print(f"Paint error: {e}")
        finally:
            if painter.isActive():
                painter.end()
