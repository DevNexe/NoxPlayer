from PySide6.QtWidgets import (QApplication, QListWidget, QMainWindow, QWidget, QVBoxLayout,
                               QHBoxLayout, QSplitter, QListWidgetItem, QLabel, QPushButton, QSlider, QFrame,
                               QGraphicsDropShadowEffect, QGraphicsScene, QGraphicsPixmapItem, QGraphicsBlurEffect, QSizePolicy, QFileDialog)
# ИСПРАВЛЕНИЕ: Удаляем 'property as QProperty' из PySide6.QtCore
from PySide6.QtCore import (Qt, QPoint, QPropertyAnimation, QEasingCurve, QTimer,
                            QUrl, QByteArray, QRectF, QSettings, QCoreApplication) 
from PySide6.QtGui import (QPainter, QLinearGradient, QColor, QFont, QPen, QBrush,
                           QFontDatabase, QPixmap, QImage, QPainterPath, QFontMetrics, QIcon)
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput, QMediaMetaData
from PySide6.QtWidgets import (QApplication, QListWidget, QMainWindow, QWidget, QVBoxLayout,
                               QHBoxLayout, QSplitter, QListWidgetItem, QLabel, QPushButton, QSlider, QFrame,
                               QGraphicsDropShadowEffect, QGraphicsScene, QGraphicsPixmapItem, QGraphicsBlurEffect, QSizePolicy, QFileDialog)
from PySide6.QtCore import (Qt, QPoint, QSize, QPropertyAnimation, QEasingCurve, QTimer,
                            QUrl, QByteArray, QRectF, QRect, QSettings, Signal, QCoreApplication, Property, QSequentialAnimationGroup, QPauseAnimation) # <-- ИЗМЕНЕНО: Добавлен Property
from PySide6.QtGui import (QPainter, QLinearGradient, QRadialGradient, QColor, QFont, QPen, QBrush,
                           QFontDatabase, QIcon, QPixmap, QImage, QPainterPath, QFontMetrics)
# ...
import sys
import os

def resource_path(relative_path):
    try:
        # PyInstaller создает временную папку _MEIxxxx
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# --- НОВЫЙ КЛАСС ДЛЯ ЭЛЕМЕНТА ПЛЕЙЛИСТА ---
class PlaylistItemWidget(QWidget):
    delete_requested = Signal(QWidget)
    """Кастомный виджет для отображения одного трека в плейлисте."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(60)
        self.setStyleSheet("background: transparent;")
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(12, 8, 12, 8)
        main_layout.setSpacing(12)

        # Обложка
        self.cover_label = AlbumCover(radius=6, cover_ratio=1.0, blur_radius=0, is_playlist_item=True)
        self.cover_label.setFixedSize(48, 48)
        self.cover_label.setStyleSheet("background: transparent;")
        main_layout.addWidget(self.cover_label)

        # Текст
        text_layout = QVBoxLayout()
        text_layout.setContentsMargins(0, 0, 0, 0)
        text_layout.setSpacing(2)
        self.track_name_label = QLabel()
        self.track_name_label.setStyleSheet("""
            color: #ffffff;
            font-size: 15px;
            font-weight: 600;
            font-family: 'Segoe UI', Arial;
            background: transparent;
        """)
        self.track_name_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        text_layout.addWidget(self.track_name_label)
        self.artist_name_label = QLabel()
        self.artist_name_label.setStyleSheet("""
            color: rgba(255, 255, 255, 0.7);
            font-size: 13px;
            font-family: 'Segoe UI', Arial;
            background: transparent;
        """)
        self.artist_name_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        text_layout.addWidget(self.artist_name_label)
        main_layout.addLayout(text_layout)

        # Добавляем растяжку, которая "забирает" всю свободную ширину между текстом и кнопкой
        main_layout.addStretch()

        # Кнопка удаления (изначально скрыта)
        self.delete_btn = QPushButton()
        self.delete_btn.setFont(QFont("Material Symbols Rounded", 16))
        self.delete_btn.setText("\ue5cd")  # close icon
        self.delete_btn.setFixedSize(20, 20)
        self.delete_btn.setCursor(Qt.PointingHandCursor)
        self.delete_btn.setStyleSheet("""
            QPushButton {
                background: rgba(255, 255, 255, 0.15);
                color: #ff5555;
                border-radius: 10px;
                padding: 0px;
            }
            QPushButton:hover {
                background: rgba(255, 85, 85, 0.3);
                color: #ffffff;
            }
        """)
        self.delete_btn.hide()
        self.delete_btn.clicked.connect(lambda: self.delete_requested.emit(self))

        # Добавляем кнопку в конец лэйаута
        main_layout.addWidget(self.delete_btn)

    def set_track_info(self, track_name, artist_name, cover_pixmap=None):
        """Устанавливает информацию о треке с автоматическим обрезанием."""
        # Сохраняем полные строки для тултипа
        self._full_track_name = track_name
        self._full_artist_name = artist_name
        # Устанавливаем тултипы
        self.track_name_label.setToolTip(track_name)
        self.artist_name_label.setToolTip(artist_name)
        # Обрезаем текст с учётом доступной ширины
        self._update_elided_text()
        # Обложка
        self.cover_label.set_cover(cover_pixmap)

    def enterEvent(self, event):
        # При наведении показываем кнопку
        self.delete_btn.show()
        super().enterEvent(event)

    def leaveEvent(self, event):
        # При уходе курсора скрываем кнопку
        self.delete_btn.hide()
        super().leaveEvent(event)

    def _update_elided_text(self):
        """Обрезает текст с многоточием, если он не влезает."""
        # Доступная ширина = ширина виджета - ширина обложки - отступы
        # Используем width() без учета кнопки, так как кнопка позиционируется отдельно
        available_width = max(10, self.width() - 48 - 12 - 12)  # 48=cover, 12+12=отступы
        # Для названия трека
        fm = QFontMetrics(self.track_name_label.font())
        elided_track = fm.elidedText(self._full_track_name, Qt.ElideRight, available_width)
        self.track_name_label.setText(elided_track)
        # Для имени артиста
        fm2 = QFontMetrics(self.artist_name_label.font())
        elided_artist = fm2.elidedText(self._full_artist_name, Qt.ElideRight, available_width)
        self.artist_name_label.setText(elided_artist)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, '_full_track_name'):
            self._update_elided_text()

    def set_selected_style(self, selected):
        """Применяет стиль для выделенного элемента."""
        if selected:
            self.setStyleSheet("""
                background: rgba(0, 120, 255, 0.2);
                border-radius: 8px;
            """)
        else:
            self.setStyleSheet("background: transparent;")
            
class TitleBar(QWidget):
# ... (Класс TitleBar остается без изменений)
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.setFixedHeight(64)
        self.start = QPoint(0, 0)
        self.pressing = False

        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(0)

        # Левая часть - лого и название
        left_widget = QWidget()
        left_widget.setStyleSheet("background: transparent;")
        left_layout = QHBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(14)

        # Логотип из icon.ico
        logo = QLabel()
        logo.setFixedSize(36, 36)
        logo.setScaledContents(True)
        pixmap = QPixmap(resource_path("icon.ico"))
        if not pixmap.isNull():
            logo.setPixmap(pixmap.scaled(36, 36, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        logo.setStyleSheet("""
            background: transparent;
            border-radius: 14px;
        """)

        # Добавляем тень к логотипу
        logo_shadow = QGraphicsDropShadowEffect()
        logo_shadow.setBlurRadius(20)
        logo_shadow.setColor(QColor(0, 153, 255, 100))
        logo_shadow.setOffset(0, 2)
        logo.setGraphicsEffect(logo_shadow)

        title = QLabel("NoxPlayer")
        title.setStyleSheet("""
            color: #ffffff;
            font-size: 16px;
            font-weight: 600;
            font-family: 'Segoe UI', Arial;
        """)

        left_layout.addWidget(logo)
        left_layout.addWidget(title)
        left_layout.addStretch()

        # Центр - Now Playing с анимированной иконкой
        center_widget = QWidget()
        center_widget.setStyleSheet("background: transparent;")
        center_layout = QHBoxLayout(center_widget)
        center_layout.setContentsMargins(0, 0, 0, 0)
        center_layout.setSpacing(10)
        center_layout.setAlignment(Qt.AlignCenter)

        # Правая часть - кнопки
        right_widget = QWidget()
        right_widget.setStyleSheet("background: transparent;")
        right_layout = QHBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setAlignment(Qt.AlignRight)
        right_layout.setSpacing(6)

        playlist_btn = QPushButton()
        playlist_btn.setFont(QFont("Material Symbols Rounded", 18))
        playlist_btn.setText("\ue3c7")
        playlist_btn.setFixedSize(18, 18)
        playlist_btn.setCursor(Qt.PointingHandCursor)
        playlist_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #999999;
                border: 1px solid transparent;
                border-radius: 8px;
                font-size: 25px;
                text-align: center;
                font-weight: 500;
            }

            QPushButton:hover {
                color: #ffffff;
                background: rgba(255, 255, 255, 0.05);
            }

            QPushButton:pressed {
                background: rgba(255, 255, 255, 0.1);
            }
        """)

        playlist_btn.clicked.connect(self.parent.toggle_playlist)

        minimize_btn = QPushButton()
        minimize_btn.setFont(QFont("Material Symbols Rounded", 20))
        minimize_btn.setText("\ue15b")  # minimize icon

        maximize_btn = QPushButton()
        maximize_btn.setFont(QFont("Material Symbols Rounded", 18))
        maximize_btn.setText("\ue3c6")  # crop_square icon

        close_btn = QPushButton()
        close_btn.setFont(QFont("Material Symbols Rounded", 20))
        close_btn.setText("\ue5cd")  # close icon

        for btn in [minimize_btn, maximize_btn, close_btn]:
            btn.setFixedSize(36, 36)
            btn.setFocusPolicy(Qt.NoFocus)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: transparent;
                    color: #888888;
                    border: none;
                    border-radius: 8px;
                    font-weight: 300;
                }

                QPushButton:hover {
                    background-color: rgba(255, 255, 255, 0.08);
                    color: #ffffff;
                }
            """)

        close_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #888888;
                border: none;
                border-radius: 8px;
                font-weight: 300;
            }

            QPushButton:hover {
                background-color: #e81123;
                color: #ffffff;
            }
        """)

        minimize_btn.clicked.connect(self.parent.showMinimized)
        maximize_btn.clicked.connect(self.toggle_maximize)
        close_btn.clicked.connect(self.parent.close)

        right_layout.addWidget(minimize_btn)
        right_layout.addWidget(maximize_btn)
        right_layout.addWidget(close_btn)

        layout.addWidget(left_widget, 1)
        layout.addStretch(1)
        layout.addWidget(center_widget, 0)
        layout.addStretch(1)
        layout.addWidget(right_widget, 1)

    def toggle_maximize(self):
            if self.parent.isMaximized():
                self.parent.showNormal()
            else:
                self.parent.showMaximized()
            # НОВОЕ: Вызываем метод обновления стиля главного окна
            self.parent.update_window_style()

    def mouseDoubleClickEvent(self, event):
            if event.button() == Qt.LeftButton:
                self.toggle_maximize()
                self.parent.update_window_style() # НОВОЕ: Обновление стиля

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.pressing = True
            self.start = event.globalPosition().toPoint()

            # --- Фикс Windows поведения ---
            if self.parent.isMaximized():
                # Координата внутри title bar, где нажал
                click_pos = int(event.position().x())

                # Разворачиваем окно
                self.parent.showNormal()
                self.parent.update_window_style()

                # НОВАЯ ширина окна
                w = self.parent.width()

                # Центрирование позиции — как Windows делает
                ratio = click_pos / self.width()
                new_x = int(self.start.x() - w * ratio)

                self.parent.move(new_x, 0)

                # Пересчитываем стартовую точку
                self.start = QPoint(self.parent.x() + click_pos, event.globalPosition().toPoint().y())

    def mouseMoveEvent(self, event):
        if self.pressing:
            delta = event.globalPosition().toPoint() - self.start
            self.parent.move(self.parent.pos() + delta)
            self.start = event.globalPosition().toPoint()

    def mouseReleaseEvent(self, event):
        self.pressing = False

class AlbumCover(QWidget):
# ... (Класс AlbumCover остается без изменений)
    def __init__(self, radius=16, cover_ratio=0.7, blur_radius=30, is_playlist_item=False, vertical_offset_ratio=0.22):
        super().__init__()
        self.radius = radius
        self.cover_ratio = cover_ratio  # доля меньшей стороны для квадрата обложки
        self.blur_radius = blur_radius  # радиус размытия для фоновой обложки
        self.is_playlist_item = is_playlist_item
        self.vertical_offset_ratio = vertical_offset_ratio
        self.album_pixmap = None  # QPixmap или None

        # Кэш для размытого фона: (w, h, radius) -> QPixmap
        self._blur_cache = None

    def set_cover(self, pixmap):
        """Установить обложку (QPixmap, QImage или байты)."""
        if pixmap is None:
            self.album_pixmap = None
        else:
            if isinstance(pixmap, QImage):
                self.album_pixmap = QPixmap.fromImage(pixmap)
            elif isinstance(pixmap, QPixmap):
                self.album_pixmap = pixmap
            else:
                try:
                    qimg = QImage.fromData(pixmap)
                    if not qimg.isNull():
                        self.album_pixmap = QPixmap.fromImage(qimg)
                    else:
                        self.album_pixmap = None
                except Exception:
                    self.album_pixmap = None

        # Сброс кэша при смене обложки
        self._blur_cache = None
        self.update()

    def _create_blurred_background(self, target_size):
        """Создаёт размытую версию album_pixmap ровно размера target_size (QSize).
        Делает margin запас по краям, чтобы blur не обрезался, и кэширует результат."""
        if not self.album_pixmap or self.album_pixmap.isNull():
            return None

        # Уменьшаем радиус на 50% для текущего вычисления
        effective_blur = self.blur_radius / 2.0

        key = (target_size.width(), target_size.height(), effective_blur)
        if self._blur_cache and self._blur_cache[0] == key:
            return self._blur_cache[1]

        # margin должен быть больше радиуса размытия
        margin = max(8, int(effective_blur * 2))
        tmp_w = target_size.width() + margin * 2
        tmp_h = target_size.height() + margin * 2

        # Масштабируем исходную обложку так, чтобы она полностью заполнила временное полотно (crop)
        scaled = self.album_pixmap.scaled(tmp_w, tmp_h, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)

        # Создаём временное изображение и заполняем фоном
        tmp_img = QImage(tmp_w, tmp_h, QImage.Format_ARGB32)
        # фон — тёмный Slate 900
        tmp_img.fill(QColor(15, 23, 42))

        # Рисуем центрированный scaled на tmp_img
        p = QPainter(tmp_img)
        try:
            p.setRenderHint(QPainter.SmoothPixmapTransform)
            x = (tmp_w - scaled.width()) // 2
            y = (tmp_h - scaled.height()) // 2
            p.drawPixmap(x, y, scaled)
        finally:
            if p.isActive():
                p.end()

        # Помещаем в сцену и применяем blur
        scene = QGraphicsScene()
        item = QGraphicsPixmapItem(QPixmap.fromImage(tmp_img))
        item.setPos(0, 0)
        scene.addItem(item)
        scene.setSceneRect(0, 0, tmp_w, tmp_h)

        blur = QGraphicsBlurEffect()
        # Применяем уменьшенный на 50% радиус
        blur.setBlurRadius(effective_blur)
        item.setGraphicsEffect(blur)

        # Рендерим сцену в изображение
        out_img = QImage(tmp_w, tmp_h, QImage.Format_ARGB32)
        out_img.fill(QColor(0, 0, 0, 0))
        p2 = QPainter(out_img)
        try:
            p2.setRenderHint(QPainter.Antialiasing)
            scene.render(p2, QRectF(0, 0, tmp_w, tmp_h), QRectF(0, 0, tmp_w, tmp_h))
        finally:
            if p2.isActive():
                p2.end()

        # Кроп центральной области ровно target_size
        crop_x = (tmp_w - target_size.width()) // 2
        crop_y = (tmp_h - target_size.height()) // 2
        cropped = out_img.copy(crop_x, crop_y, target_size.width(), target_size.height())

        pixmap = QPixmap.fromImage(cropped)
        self._blur_cache = (key, pixmap)
        return pixmap

    def paintEvent(self, event):
        painter = QPainter(self)
        try:
            painter.setRenderHint(QPainter.Antialiasing)
            painter.setRenderHint(QPainter.SmoothPixmapTransform)

            w, h = float(self.width()), float(self.height())
            rect = QRectF(0, 0, w, h)
            
            main_path = QPainterPath()
            main_path.addRoundedRect(rect, self.radius, self.radius)
            
            painter.save() # (1) Состояние фона
            painter.setClipPath(main_path)

            # --- 1. ДИАГОНАЛЬНЫЙ ГРАДИЕНТ ---
            bg_grad = QLinearGradient(0, 0, w, h)
            bg_grad.setColorAt(0.0, QColor(45, 55, 75))
            bg_grad.setColorAt(1.0, QColor(10, 15, 20))
            painter.fillRect(self.rect(), QBrush(bg_grad))

            # --- 2. РАЗМЫТИЕ ПОВЕРХ ---
            blurred = self._create_blurred_background(self.size())
            if blurred and not blurred.isNull():
                painter.setOpacity(0.6) 
                painter.drawPixmap(0, 0, blurred)
                painter.setOpacity(1.0)

            painter.restore() # Конец Состояния (1)

            # --- 3. КОНТЕНТ (ОБЛОЖКА ИЛИ ИКОНКА) ---
            size = int(min(w, h) * self.cover_ratio)
            cx = (w - size) / 2.0
            
            # Для обложки оставляем твою логику смещения
            cy_cover = (h - size) / 2.0 if self.is_playlist_item else max(20.0, (h - size) * self.vertical_offset_ratio)
            cover_rect = QRectF(cx, cy_cover, float(size), float(size))

            if self.album_pixmap and not self.album_pixmap.isNull():
                # РИСУЕМ ОБЛОЖКУ (с твоим смещением)
                shadow_path = QPainterPath()
                shadow_path.addRoundedRect(cover_rect.adjusted(2, 6, 2, 6), 12, 12)
                painter.fillPath(shadow_path, QColor(0, 0, 0, 180))

                cover_path = QPainterPath()
                cover_path.addRoundedRect(cover_rect, 12, 12)
                
                painter.save() 
                painter.setClipPath(cover_path)
                scaled = self.album_pixmap.scaled(int(size), int(size), Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
                source_rect = QRect((scaled.width() - size) // 2, (scaled.height() - size) // 2, size, size)
                painter.drawPixmap(cover_rect.toRect(), scaled, source_rect)
                painter.restore()

                painter.setPen(QPen(QColor(255, 255, 255, 30), 1))
                painter.drawRoundedRect(cover_rect, 12, 12)
            else:
                # РИСУЕМ ИКОНКУ СТРОГО ПО ЦЕНТРУ ОКНА
                # Создаем отдельный rect для иконки, игнорируя cy_cover
                cy_centered = (h - size) / 2.0
                icon_rect = QRectF(cx, cy_centered, float(size), float(size))

                # Настройка шрифта
                font = QFont("Material Symbols Rounded", int(size * 0.5)) 
                painter.setFont(font)
                painter.setPen(QColor(255, 255, 255, 200))

                # Отрисовка символа audio_file (\ue405)
                painter.drawText(icon_rect, Qt.AlignCenter, "\ue405")

        except Exception as e:
            print(f"Paint error: {e}")
        finally:
            if painter.isActive():
                painter.end()

class OutlineLabel(QLabel):
    """Кастомный QLabel, который рисует текст с обводкой и размытой тенью."""
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self._outline_color = QColor(0, 0, 0)
        self._outline_width = 2
        self._blur_radius = 0 

    def setOutlineColor(self, color: QColor):
        self._outline_color = color
        self.update()

    def setOutlineWidth(self, width: int):
        self._outline_width = width
        self.update()

    def setOutlineBlurRadius(self, radius: int):
        self._blur_radius = radius
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        try:
            painter.setRenderHint(QPainter.Antialiasing)

            # 1. Определяем общий сдвиг (x_shift) для бегущей строки
            x_shift = self._text_x_offset if isinstance(self, MarqueeLabel) else 0

            # --- 2. Определяем путь текста (QPainterPath) ---
            path = QPainterPath()
            metrics = QFontMetrics(self.font())

            text_height = metrics.height()
            v_offset = (self.height() - text_height) / 2
            baseline = metrics.ascent() + v_offset
            
            x_start = self.contentsMargins().left()
            
            # Логика выравнивания, если это не MarqueeLabel
            if not isinstance(self, MarqueeLabel):
                if self.alignment() & Qt.AlignHCenter:
                    text_width = metrics.horizontalAdvance(self.text())
                    x_start = (self.width() - text_width) / 2
                elif self.alignment() & Qt.AlignRight:
                    text_width = metrics.horizontalAdvance(self.text())
                    x_start = self.width() - text_width - self.contentsMargins().right()

            path.addText(x_start, baseline, self.font(), self.text())
            
            # --- 3. Обводка (Outline) и Размытие (Blur) ---
            
            if self._blur_radius > 0:
                # Временный painter для рисования обводки для размытия
                image = QImage(self.size(), QImage.Format_ARGB32_Premultiplied)
                image.fill(QColor(0, 0, 0, 0))

                stroke_painter = QPainter(image)
                try:
                    stroke_painter.setRenderHint(QPainter.Antialiasing)
                    
                    # ПРИМЕНЯЕМ СДВИГ К ВРЕМЕННОМУ ХОЛСТУ (ТОЛЬКО ДЛЯ ТЕНИ)
                    stroke_painter.translate(x_shift, 0)
                        
                    pen = QPen(self._outline_color)
                    pen.setWidthF(float(self._outline_width))
                    pen.setJoinStyle(Qt.RoundJoin)
                    
                    stroke_painter.setPen(pen)
                    stroke_painter.setBrush(Qt.NoBrush)
                    stroke_painter.drawPath(path)
                finally:
                    if stroke_painter.isActive():
                        stroke_painter.end()

                # Применяем размытие через QGraphicsScene
                scene = QGraphicsScene()
                item = QGraphicsPixmapItem(QPixmap.fromImage(image))
                scene.addItem(item)
                
                blur_effect = QGraphicsBlurEffect()
                blur_effect.setBlurRadius(self._blur_radius)
                item.setGraphicsEffect(blur_effect)

                # Рендерим размытое изображение обратно
                # !!! ПРАВИЛЬНОЕ ОПРЕДЕЛЕНИЕ blurred_image !!!
                blurred_image = QImage(self.size(), QImage.Format_ARGB32_Premultiplied) 
                blurred_image.fill(QColor(0, 0, 0, 0))
                
                render_painter = QPainter(blurred_image)
                try:
                    render_painter.setRenderHint(QPainter.Antialiasing)
                    # Рендерим сцену (с размытым элементом) на наш холст blurred_image
                    scene.render(render_painter, QRectF(self.rect()), QRectF(self.rect()))
                finally:
                    if render_painter.isActive():
                        render_painter.end()

                # Рисуем размытую обводку на основной виджет
                painter.drawPixmap(0, 0, QPixmap.fromImage(blurred_image))
                
                # --- Переход к отрисовке заливки (Fill) ---
                # Если была размытая тень, то основной painter еще НЕ СДВИНУТ! Сдвигаем его.
                painter.translate(x_shift, 0)
            
            # Если размытие не задано, рисуем обычную обводку
            else:
                pen = QPen(self._outline_color)
                pen.setWidthF(float(self._outline_width))
                pen.setJoinStyle(Qt.RoundJoin)
                
                painter.setPen(pen)
                painter.setBrush(Qt.NoBrush)

                # Применяем сдвиг к основному painter для обводки
                painter.translate(x_shift, 0)
                painter.drawPath(path)
                
                # Заливка будет использовать тот же сдвиг, т.к. translate накопительный

            # --- 4. Заливка (Fill) ---
            painter.setPen(Qt.NoPen)
            painter.setBrush(self.palette().brush(self.foregroundRole())) 
            painter.drawPath(path) # Отрисовка текста (заливки)
        
        finally:
            if painter.isActive():
                painter.end()


class MarqueeLabel(OutlineLabel):
    """OutlineLabel с возможностью бегущей строки (marquee)."""
    
    _TEXT_X_PROPERTY = b"text_x_offset"

    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.animation = None
        self._text_x_offset = 0.0  # Текущая позиция текста
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self._start_animation)
        
        self.setContentsMargins(0, 0, 0, 0)
        self.setWordWrap(False) # Важно: запрещаем перенос

    # Свойство 'text_x_offset' для анимации - ИСПРАВЛЕННЫЙ СИНТАКСИС
    def get_text_x_offset(self):
        return self._text_x_offset

    def set_text_x_offset(self, x):
        self._text_x_offset = x
        self.update() 

    # 2. ИЗМЕНЕНИЕ: Используем декоратор @Property для регистрации в системе метаобъектов Qt.
    # Первый аргумент - тип данных (float), второй - геттер, третий - сеттер.
    text_x_offset = Property(float, get_text_x_offset, set_text_x_offset)

    def setText(self, text: str):
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
            
        metrics = QFontMetrics(self.font())
        text_width = metrics.horizontalAdvance(self.text())
        
        label_width = self.width() - self.contentsMargins().left() - self.contentsMargins().right()

        if text_width > label_width:
            distance = text_width - label_width + 15 
            duration = int(distance * 80) 
            duration = max(3000, duration) 

            self._stop_animation() # Останавливаем старую анимацию

            # --- 1. Анимация: Скролл Влево (0.0 -> -distance) ---
            anim_scroll_left = QPropertyAnimation(self, self._TEXT_X_PROPERTY)
            anim_scroll_left.setDuration(duration)
            anim_scroll_left.setEasingCurve(QEasingCurve.Linear)
            anim_scroll_left.setStartValue(0.0)
            anim_scroll_left.setEndValue(-distance)

            # --- 2. Пауза в конце (1.5 секунды) ---
            anim_pause_end = QPauseAnimation(1500) 

            # --- 3. Анимация: Скролл Вправо (-distance -> 0.0) ---
            anim_scroll_right = QPropertyAnimation(self, self._TEXT_X_PROPERTY)
            anim_scroll_right.setDuration(duration) # Та же длительность для плавной обратной скорости
            anim_scroll_right.setEasingCurve(QEasingCurve.Linear)
            anim_scroll_right.setStartValue(-distance)
            anim_scroll_right.setEndValue(0.0)

            # --- 4. Пауза в начале (1.5 секунды) ---
            anim_pause_start = QPauseAnimation(1500) 

            # --- 5. Группируем последовательность ---
            self.animation = QSequentialAnimationGroup(self)
            self.animation.addAnimation(anim_scroll_left)
            self.animation.addAnimation(anim_pause_end)
            self.animation.addAnimation(anim_scroll_right)
            self.animation.addAnimation(anim_pause_start)
            
            self.animation.setLoopCount(-1) # Бесконечный цикл для всей последовательности
            self.animation.start()
        else:
            self.animation = None
            self._text_x_offset = 0.0
            self.update()

    def _stop_animation(self):
        if self.animation and self.animation.state() == QPropertyAnimation.State.Running:
            self.animation.stop()
        self.animation = None
            
    # Не переопределяем paintEvent, так как логика добавлена в OutlineLabel.paintEvent
    # с проверкой isinstance(self, MarqueeLabel)

class NoxPlayer(QMainWindow):
    # НОВОЕ: Ключ для сохранения пути к файлу
    LAST_TRACK_KEY = "lastTrackPath"
    SHUFFLE_KEY = "shuffleMode"
    REPEAT_KEY = "repeatMode" 

    def __init__(self):
        super().__init__()
        self.setFixedSize(960, 740)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setFocusPolicy(Qt.StrongFocus)
        # Устанавливаем иконку приложения
        self.setWindowIcon(QIcon(resource_path("icon.ico")))

        self.init_player() # Инициализация медиа-плеера

        self.shuffle_mode = False
        self.repeat_mode = 0  # 0 = off, 1 = all, 2 = one

        # Загружаем шрифт Material Symbols
        font_path = resource_path("MaterialSymbolsRounded.ttf")
        if os.path.exists(font_path):
            font_id = QFontDatabase.addApplicationFont(font_path)
            if font_id != -1:
                families = QFontDatabase.applicationFontFamilies(font_id)
                if families:
                    self.material_font = families[0]
                else:
                    print("⚠️ Font loaded, but no family name found.")
                    self.material_font = "Segoe UI"
            else:
                print("❌ Failed to load font from:", font_path)
                self.material_font = "Segoe UI"
        else:
            print("❌ Font file not found:", font_path)
            self.material_font = "Segoe UI"
    
        central = QWidget()
        self.setCentralWidget(central)
        self.added_urls = set()  # Хранит строковые представления URL'ов, уже в плейлисте
        self.update_window_style()

        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.is_muted = False
        self.last_volume = 100  # Сохранённая громкость (в процентах)

        # Title bar
        self.title_bar = TitleBar(self)
        main_layout.addWidget(self.title_bar)

        # Основной контент
        content = QWidget()
        content.setStyleSheet("background: transparent;")
        content_layout = QVBoxLayout(content)
        # Отступы: 14px по бокам, 0 по вертикали для максимального растяжения.
        content_layout.setContentsMargins(14, 0, 14, 0) 
        content_layout.setAlignment(Qt.AlignTop | Qt.AlignHCenter)

        # Обложка альбома с тенью
        album_container = QWidget()
        album_container.setStyleSheet("background: transparent;")
        album_container.setMinimumWidth(300)
        album_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        album_layout = QVBoxLayout(album_container)
        album_layout.setContentsMargins(0, 0, 0, 0)
        album_layout.setSpacing(0)

        self.album_cover_bg = AlbumCover(radius=16, cover_ratio=0.7, blur_radius=30, vertical_offset_ratio=0.15)  # Поднимаем центральную обложку выше

        # Лэйаут для текста, который накладывается на обложку
        overlay_layout = QVBoxLayout(self.album_cover_bg)
        overlay_layout.setContentsMargins(25, 0, 25, 25) # Увеличен bottom margin для отступа
        overlay_layout.setSpacing(0)

        overlay_layout.addStretch(1) # Растяжка сверху толкает текст вниз

        self.text_clip_widget = QWidget()
        # Этот контейнер должен быть обрезан, чтобы сдвинутый текст не выходил за его рамки
        self.text_clip_widget.setContentsMargins(0, 0, 0, 0) 
        self.text_clip_widget.setStyleSheet("background: transparent;")
        
        text_clip_layout = QVBoxLayout(self.text_clip_widget)
        text_clip_layout.setContentsMargins(0, 0, 0, 0)
        text_clip_layout.setSpacing(0)
        # --- КОНЕЦ НОВОГО КОНТЕЙНЕРА ---


        # self.track_name_label = OutlineLabel("")  ← ЗАМЕНА
        self.track_name_label = MarqueeLabel("")
        self.track_name_label.setAlignment(Qt.AlignLeft)
        self.track_name_label.setStyleSheet("""
            color: #ffffff;
            font-size: 34px;
            font-weight: 600;
            font-family: 'Segoe UI', Arial;
            background: transparent;
            letter-spacing: -0.5px;
        """)
        # Устанавливаем толщину обводки и НОВЫЙ радиус размытия
        self.track_name_label.setOutlineWidth(2)
        self.track_name_label.setOutlineColor(QColor(0, 0, 0))
        self.track_name_label.setOutlineBlurRadius(4) # НОВОЕ

        # ИСПОЛЬЗУЕМ OutlineLabel ВМЕСТО QLabel
        self.artist_name_label = OutlineLabel("Select a file to play")
        self.artist_name_label.setAlignment(Qt.AlignLeft)
        self.artist_name_label.setStyleSheet("""
            color: rgba(255, 255, 255, 0.7);
            font-size: 17px;
            font-family: 'Segoe UI', Arial;
            background: transparent;
        """)
        # Устанавливаем толщину обводки и НОВЫЙ радиус размытия
        self.artist_name_label.setOutlineWidth(1)
        self.artist_name_label.setOutlineColor(QColor(0, 0, 0))
        self.artist_name_label.setOutlineBlurRadius(3) # НОВОЕ

        overlay_layout.addWidget(self.track_name_label)
        overlay_layout.addWidget(self.artist_name_label)

        # Добавляем тень к обложке
        cover_shadow = QGraphicsDropShadowEffect()
        cover_shadow.setBlurRadius(40)
        cover_shadow.setColor(QColor(0, 0, 0, 120))
        cover_shadow.setOffset(0, 10)
        self.album_cover_bg.setGraphicsEffect(cover_shadow)

        # Добавляем обложку в контейнер
        album_layout.addWidget(self.album_cover_bg, 1)

        # Добавляем album_container со stretch factor 1, чтобы он занял всю высоту
        content_layout.addWidget(album_container, 1) 
        # content_layout.addSpacing(25) УДАЛЕНО

        # === Плейлист ===
        self.playlist_widget = QListWidget()
        self.playlist_widget.setMinimumWidth(0)
        self.playlist_widget.setMaximumWidth(600)
        self.playlist_widget.setStyleSheet("""
            QListWidget {
                background: #0f0f0f;
                border: none;
                border-radius: 0px;
                padding: 12px;
                padding-right: 0;
                margin: 0;
                padding-left: 0;
            }
            QListWidget::item {
                /* Стиль для самого item не нужен, так как мы используем кастомный виджет */
                padding: 0;
                margin: 0;
            }
            QListWidget::item:selected {
                /* Стиль для выделенного item также не нужен, управляем через кастомный виджет */
                background: transparent;
            }
            QListWidget::item:hover {
                /* Стиль для наведения тоже не нужен, управляем через кастомный виджет */
                background: transparent;
            }
            QScrollBar:vertical {
                border: none;
                background: #0f0f0f; 
                width: 10px; /* Увеличил общую область, чтобы margin был заметен */
                /* Настройка margin: Сверху, Справа, Снизу, Слева */
                margin: 10px 2px 10px 0px; 
            }

            QScrollBar::handle:vertical {
                background: rgba(255, 255, 255, 40);
                min-height: 30px;
                border-radius: 4px;
            }
            
            QScrollBar::handle:vertical:hover {
                background: rgba(255, 255, 255, 80);
            }

            /* Убираем лишние элементы, но оставляем структуру */
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                background: none;
                height: 0px;
            }

            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }

            QScrollBar::sub-page:vertical {
                background: #0f0f0f; /* Например, слабый красный оттенок */
                margin: 10px 0px 0px 0px;       /* Должен совпадать с верхним margin основного блока */
            }

            /* Область под ползунком */
            QScrollBar::add-page:vertical {
                background: #0f0f0f; /* Например, слабый зеленый оттенок */
                margin: 0px 0px 10px 0px;       /* Должен совпадать с нижним margin основного блока */
            }
        """)

        # Подключаем сигнал для обработки выделения
        self.playlist_widget.itemSelectionChanged.connect(self.on_playlist_selection_changed)
        self.playlist_widget.itemClicked.connect(self.on_playlist_item_double_clicked)
        # Убираем старое подключение, так как теперь используется другой метод
        # self.playlist_widget.itemClicked.connect(self.on_playlist_item_double_clicked)
        # === QSplitter ===
        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(6)
        splitter.setStyleSheet("""
            QSplitter::handle {
                background: #0f0f0f;
                border-radius: 3px;
                border-top-right-radius: 0px;
                border-bottom-right-radius: 0px;
            }
            QSplitter::handle:hover {
                background: rgba(255, 255, 255, 0.15);
            }
        """)

        splitter.addWidget(content)
        splitter.addWidget(self.playlist_widget)

        # ВАЖНО: сжимаем плейлист до 0, но НЕ скрываем
        splitter.setSizes([content.width(), 0])  # ← именно так

        main_layout.addWidget(splitter, 1)

        # Панель управления
        self.create_controls(main_layout)

        # Соединение сигналов плеера с UI (Line 575 in the provided code)
        self.player.positionChanged.connect(self.update_position)
        self.player.durationChanged.connect(self.update_duration)
        self.player.mediaStatusChanged.connect(self.on_media_status_changed)
        self.progress.sliderMoved.connect(self.player.setPosition)
        # Установка начальных значений
        self.volume_slider.setValue(self.player.audioOutput().volume() * 100)
        self.volume_slider.valueChanged.connect(self.on_volume_slider_changed)
        self.time_total.setText(self.format_time(0))
        
        # НОВОЕ: Загрузка последнего трека при старте
        self.load_last_track() 
        self.activateWindow()
        self.setFocus()
        self.load_settings()

    def init_player(self):
        """Инициализирует объекты QMediaPlayer и QAudioOutput."""
        # НОВОЕ: Устанавливаем организацию и приложение для QSettings
        QCoreApplication.setOrganizationName("NoxSoftware")
        QCoreApplication.setApplicationName("NoxPlayer")
        
        self.player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.player.setAudioOutput(self.audio_output)
        self.is_playing = False

    def load_settings(self):
        settings = QSettings()
        
        # Загружаем Shuffle (по умолчанию False)
        self.shuffle_mode = settings.value(self.SHUFFLE_KEY, False, type=bool)
        if self.shuffle_mode:
            self.shuffle_btn.setStyleSheet("color: #ffffff;")
            
        # Загружаем Repeat (по умолчанию 0)
        self.repeat_mode = int(settings.value(self.REPEAT_KEY, 0))
        if self.repeat_mode == 1:
            self.repeat_btn.setText("\ue040")
            self.repeat_btn.setStyleSheet("color: #ffffff;")
        elif self.repeat_mode == 2:
            self.repeat_btn.setText("\ue041") # repeat_one icon
            self.repeat_btn.setStyleSheet("color: #ffffff;")

    def remove_duplicate_tracks(self):
        """Удаляет дубликаты из плейлиста, оставляя только первое вхождение."""
        seen_urls = set()
        to_remove = []
        for i in range(self.playlist_widget.count() - 1, -1, -1):  # идём с конца, чтобы безопасно удалять
            item = self.playlist_widget.item(i)
            if item:
                url = item.data(Qt.UserRole)
                if url and not url.isEmpty():
                    url_str = url.toString()
                    if url_str in seen_urls:
                        to_remove.append(i)
                    else:
                        seen_urls.add(url_str)

        # Удаляем в обратном порядке (чтобы индексы не сбивались)
        for index in sorted(to_remove, reverse=True):
            self.playlist_widget.takeItem(index)

        # Обновляем added_urls, чтобы отражать текущее состояние
        self.added_urls = seen_urls.copy()

    def on_volume_slider_changed(self, value):
        self.player.audioOutput().setVolume(value / 100.0)
        # Если пользователь двигает слайдер — автоматически размутим
        if self.is_muted and value > 0:
            self.is_muted = False
            self.volume_icon.setText("\ue050")  # volume_up

    def closeEvent(self, event):
        """Сохраняет текущий трек и плейлист перед закрытием."""
        self.save_last_track()
        event.accept()

    def _get_artist_string(self, meta):
        """Возвращает строку с перечислением всех артистов через запятую."""
        for key in [QMediaMetaData.ContributingArtist, QMediaMetaData.AlbumArtist, QMediaMetaData.Author]:
            val = meta.value(key)
            if val:
                if isinstance(val, list):
                    return ", ".join(str(artist) for artist in val if artist)
                else:
                    return str(val)
        return ""

    def toggle_playlist(self):
        splitter = self.playlist_widget.parent()
        if not isinstance(splitter, QSplitter):
            return
        sizes = splitter.sizes()
        content_width = sizes[0]
        playlist_width = sizes[1]

        if playlist_width <= 5:  # Скрыто
            new_width = 280
            splitter.setSizes([content_width, new_width])
        else:  # Открыто — сворачиваем
            splitter.setSizes([content_width + playlist_width, 0])

    def on_playlist_item_double_clicked(self, item):
        index = self.playlist_widget.row(item)
        self.play_track_at(index)

    def on_media_status_changed(self, status):
        if status == QMediaPlayer.MediaStatus.EndOfMedia:
            if self.repeat_mode == 2:
                # repeat one: перезапуск
                self.player.setPosition(0)
                self.player.play()
            else:
                self.play_next_on_end()  # ← ИСПОЛЬЗУЕМ НОВЫЙ МЕТОД
        elif status == QMediaPlayer.MediaStatus.LoadedMedia:
            self.update_track_info(status)

    def play_next(self):
        """Вызывается при нажатии клавиши → — всегда переходит к следующему треку (циклически)."""
        total = self.playlist_widget.count()
        if total == 0:
            return
        current_row = self.playlist_widget.currentRow()
        next_row = (current_row + 1) % total
        self.play_track_at(next_row)

    def play_next_on_end(self):
        """Вызывается при EndOfMedia — учитывает repeat_mode."""
        total = self.playlist_widget.count()
        if total == 0:
            return
        current_row = self.playlist_widget.currentRow()
        if self.repeat_mode == 0 and current_row == total - 1:
            # Последний трек и repeat=off → остановить
            self.toggle_play(False)
            return
        next_row = (current_row + 1) % total
        self.play_track_at(next_row)

    def play_prev(self):
        current_row = self.playlist_widget.currentRow()
        total = self.playlist_widget.count()
        if total == 0:
            return

        if self.shuffle_mode and total > 1:
            import random
            prev_row = random.randint(0, total - 1)
            while prev_row == current_row and total > 1:
                prev_row = random.randint(0, total - 1)
        else:
            if self.repeat_mode == 2:
                prev_row = current_row
            else:
                prev_row = (current_row - 1) % total

        self.play_track_at(prev_row)

    def toggle_shuffle(self):
        self.shuffle_mode = not self.shuffle_mode
        # Сохраняем состояние
        settings = QSettings()
        settings.setValue(self.SHUFFLE_KEY, self.shuffle_mode)
        # Если включаем shuffle — выключаем repeat one
        if self.shuffle_mode and self.repeat_mode == 2:
            self.repeat_mode = 0  # или 1, но точно не 2
            self.repeat_btn.setText("\ue040")
            self.repeat_btn.setStyleSheet("""
                QPushButton {
                    background: transparent;
                    border: none;
                    color: #888888;
                    border-radius: 23px;
                }
                QPushButton:hover {
                    color: #ffffff;
                    background: rgba(255, 255, 255, 0.05);
                }
            """)
        color = "#ffffff" if self.shuffle_mode else "#888888"
        self.shuffle_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                border: none;
                color: {color};
                border-radius: 23px;
            }}
            QPushButton:hover {{
                color: #ffffff;
                background: rgba(255, 255, 255, 0.05);
            }}
        """)
            
    def toggle_repeat(self):
        old_repeat = self.repeat_mode
        self.repeat_mode = (self.repeat_mode + 1) % 3

        settings = QSettings()
        settings.setValue(self.REPEAT_KEY, self.repeat_mode)
        
        # Если включаем repeat one — выключаем shuffle
        if old_repeat != 2 and self.repeat_mode == 2:
            self.shuffle_mode = False
            self.shuffle_btn.setStyleSheet("""
                QPushButton {
                    background: transparent;
                    border: none;
                    color: #888888;
                    border-radius: 23px;
                }
                QPushButton:hover {
                    color: #ffffff;
                    background: rgba(255, 255, 255, 0.05);
                }
            """)

        if self.repeat_mode == 0:
            icon = "\ue040"
            color = "#888888"
        elif self.repeat_mode == 1:
            icon = "\ue040"
            color = "#ffffff"
        else:  # repeat one
            icon = "\ue041"
            color = "#ffffff"

        self.repeat_btn.setText(icon)
        self.repeat_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                border: none;
                color: {color};
                border-radius: 23px;
            }}
            QPushButton:hover {{
                color: #ffffff;
                background: rgba(255, 255, 255, 0.05);
            }}
        """)

    def save_last_track(self):
        settings = QSettings()
        current_source = self.player.source()
        # Сохраняем только если источник есть в плейлисте
        should_save = False
        if not current_source.isEmpty() and current_source.isLocalFile():
            for i in range(self.playlist_widget.count()):
                item = self.playlist_widget.item(i)
                if item and item.data(Qt.UserRole) == current_source:
                    should_save = True
                    break
        if should_save:
            settings.setValue(self.LAST_TRACK_KEY, current_source.toString())
        else:
            settings.remove(self.LAST_TRACK_KEY)

        # Сохраняем плейлист
        playlist_urls = []
        seen = set()
        for i in range(self.playlist_widget.count()):
            item = self.playlist_widget.item(i)
            url = item.data(Qt.UserRole)
            if url and not url.isEmpty():
                url_str = url.toString()
                if url_str not in seen:
                    playlist_urls.append(url_str)
                    seen.add(url_str)

        settings.setValue("playlist", playlist_urls)

        # Сохраняем ширину плейлиста (0 если закрыт)
        splitter = self.playlist_widget.parent()
        if isinstance(splitter, QSplitter):
            width = splitter.sizes()[1]
            settings.setValue("playlist_width", width)

        # Синхронизируем added_urls с текущим плейлистом (на всякий случай)
        self.added_urls.clear()
        for i in range(self.playlist_widget.count()):
            item = self.playlist_widget.item(i)
            url = item.data(Qt.UserRole)
            if url and not url.isEmpty():
                self.added_urls.add(url.toString())

    def load_last_track(self):
        settings = QSettings()
        playlist_urls = settings.value("playlist", [])
        if playlist_urls:
            for url_str in playlist_urls:
                if isinstance(url_str, bytes):
                    try:
                        url_str = url_str.decode("utf-8")
                    except UnicodeDecodeError:
                        continue
                url = QUrl(url_str)
                if url.isLocalFile() and os.path.exists(url.toLocalFile()):
                    self.add_track_to_playlist(url)  # ← уже защищён от дублей

        # Но на случай, если старая версия сохранила дубли — чистим
        self.remove_duplicate_tracks()  # ← ДОБАВЬ ЭТУ СТРОКУ

        # --- 2. Загружаем последний трек ---
        path = settings.value(self.LAST_TRACK_KEY, "")
        if isinstance(path, bytes):
            try:
                path = path.decode("utf-8")
            except UnicodeDecodeError:
                path = ""
        if path:
            url = QUrl(path)
            if url.isLocalFile() and os.path.exists(url.toLocalFile()):
                # Проверяем, есть ли этот URL в плейлисте
                found_in_playlist = False
                for i in range(self.playlist_widget.count()):
                    item = self.playlist_widget.item(i)
                    item_url = item.data(Qt.UserRole)
                    if item_url == url:
                        found_in_playlist = True
                        break
                if found_in_playlist:
                    self.player.setSource(url)

        # --- 3. Восстанавливаем ширину плейлиста ---
        width = settings.value("playlist_width", 0)
        if isinstance(width, str):
            width = int(width) if width.isdigit() else 0
        elif isinstance(width, float):
            width = int(width)
        else:
            width = 0

        splitter = self.playlist_widget.parent()
        if isinstance(splitter, QSplitter):
            if width <= 5:
                current = splitter.sizes()
                splitter.setSizes([current[0] + current[1], 0])
            else:
                current = splitter.sizes()
                total = current[0] + current[1]
                splitter.setSizes([total - width, width])

    def on_playlist_item_delete(self, widget):
        """Удаляет элемент плейлиста по запросу из PlaylistItemWidget."""
        for i in range(self.playlist_widget.count()):
            item = self.playlist_widget.item(i)
            if self.playlist_widget.itemWidget(item) is widget:
                url = item.data(Qt.UserRole)
                current_source = self.player.source()

                # Проверяем, является ли удаляемый трек текущим
                is_current = (url and not url.isEmpty() and url == current_source)

                if url and not url.isEmpty():
                    self.added_urls.discard(url.toString())

                self.playlist_widget.takeItem(i)

                # Если удалили текущий трек — останавливаем воспроизведение и сбрасываем источник
                if is_current:
                    self.player.setSource(QUrl())  # Очищаем источник
                    self.track_name_label.setText("Select a file to play")
                    self.artist_name_label.setText("")
                    self.album_cover_bg.set_cover(None)
                    self.play_btn.setText("\ue037")  # play icon
                    self.is_playing = False

                break

    def _add_track_to_playlist_no_check(self, url: QUrl):
        """Добавляет трек в плейлист БЕЗ проверки дубликатов (только для load_last_track)."""
        file_path = url.toLocalFile()
        fallback_title = os.path.splitext(os.path.basename(file_path))[0]
        fallback_artist = "Unknown Artist"

        item = QListWidgetItem()
        item.setData(Qt.UserRole, url)
        item.setSizeHint(QSize(0, 60))

        widget = PlaylistItemWidget()
        widget.set_track_info(fallback_title, fallback_artist)
        widget.delete_requested.connect(self.on_playlist_item_delete)

        self.playlist_widget.addItem(item)
        self.playlist_widget.setItemWidget(item, widget)

        # Загружаем метаданные асинхронно
        meta = QMediaPlayer()
        meta.setSource(url)

        def safe_delete():
            if hasattr(meta, "_deleted"):
                return
            meta._deleted = True
            meta.deleteLater()

        def on_meta_loaded():
            title = meta.metaData().value(QMediaMetaData.Title) or fallback_title
            artist = self._get_artist_string(meta.metaData()) or "Unknown Artist"
            cover_pixmap = None

            img = None
            try:
                img = meta.metaData().value(QMediaMetaData.ThumbnailImage)
            except Exception:
                pass
            if not img:
                try:
                    img = meta.metaData().value(QMediaMetaData.CoverArtImage)
                except Exception:
                    pass
            if img:
                if isinstance(img, QImage):
                    cover_pixmap = QPixmap.fromImage(img)
                elif isinstance(img, QPixmap):
                    cover_pixmap = img
                elif isinstance(img, (bytes, bytearray, QByteArray)):
                    try:
                        qimg = QImage.fromData(bytes(img))
                        if not qimg.isNull():
                            cover_pixmap = QPixmap.fromImage(qimg)
                    except Exception:
                        pass
                else:
                    try:
                        qimg = QImage.fromData(img)
                        if not qimg.isNull():
                            cover_pixmap = QPixmap.fromImage(qimg)
                    except Exception:
                        pass

            widget.set_track_info(title, artist, cover_pixmap)
            safe_delete()

        meta.mediaStatusChanged.connect(
            lambda s: on_meta_loaded() if s == QMediaPlayer.MediaStatus.LoadedMedia else None
        )
        QTimer.singleShot(2000, safe_delete)

    def update_window_style(self):
        """Обновляет border-radius в зависимости от состояния окна."""
        if self.isMaximized():
            style = """
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #0a0a0a, stop:1 #050505);
                border-radius: 0px;
            """
        else:
            style = """
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #0a0a0a, stop:1 #050505);
                border-radius: 14px;
            """
        self.centralWidget().setStyleSheet(style)

    def format_time(self, milliseconds):
        """Конвертирует миллисекунды в формат M:SS."""
        seconds = int(milliseconds / 1000)
        minutes = int(seconds / 60)
        seconds = seconds % 60
        return f"{minutes}:{seconds:02d}"

    def update_position(self, position):
        """Обновляет ползунок и текущее время."""
        if not self.progress.isSliderDown():
            self.progress.setValue(position)
            self.time_current.setText(self.format_time(position))

    def update_duration(self, duration):
        """Обновляет максимальное значение ползунка и общее время."""
        self.progress.setMaximum(duration)
        self.time_total.setText(self.format_time(duration))
        self.progress.setValue(0)
        self.time_current.setText(self.format_time(0))

    def update_track_info(self, status):
        if status != QMediaPlayer.MediaStatus.LoadedMedia:
            return

        meta = self.player.metaData()

        title = meta.value(QMediaMetaData.Title)
        artist = self._get_artist_string(meta)
        album = meta.value(QMediaMetaData.AlbumTitle)

        # Имя файла как fallback
        media = self.player.source()
        # Fallback to file name if a valid title isn't found
        filename = media.fileName() if media.isLocalFile() else media.toString() # Use full string as fallback
        base_filename = os.path.basename(filename)
        title_fallback = os.path.splitext(base_filename)[0]
        
        if not title:
             title = title_fallback if title_fallback else "Unknown Title"
             
        if not artist:
            artist = "Unknown Artist"

        self.track_name_label.setText(title)
        self.artist_name_label.setText(artist)

        # Попытка получить обложку — поддерживаем QImage, QPixmap, bytes/QByteArray
        cover_pixmap = None
        img = None
        try:
            # Try official keys first
            img = meta.value(QMediaMetaData.ThumbnailImage)
        except Exception:
            img = None

        if not img:
            # try CoverArtImage as fallback
            try:
                img = meta.value(QMediaMetaData.CoverArtImage)
            except Exception:
                img = None

        if img:
            # QImage
            if isinstance(img, QImage):
                cover_pixmap = QPixmap.fromImage(img)
            # QPixmap
            elif isinstance(img, QPixmap):
                cover_pixmap = img
            # QByteArray / bytes
            elif isinstance(img, (bytes, bytearray, QByteArray)):
                try:
                    qimg = QImage.fromData(bytes(img))
                    if not qimg.isNull():
                        cover_pixmap = QPixmap.fromImage(qimg)
                except Exception:
                    cover_pixmap = None
            else:
                # Пытаться конвертировать через QImage.fromData
                try:
                    # Tries to convert generic Python object to QByteArray/bytes if possible
                    qimg = QImage.fromData(img)
                    if not qimg.isNull():
                        cover_pixmap = QPixmap.fromImage(qimg)
                except Exception:
                    cover_pixmap = None

        # Устанавливаем обложку (или очищаем)
        self.album_cover_bg.set_cover(cover_pixmap)

    def open_file_dialog(self):
        file_dialog = QFileDialog()
        file_dialog.setFileMode(QFileDialog.ExistingFiles)
        file_dialog.setNameFilter("Audio Files (*.mp3 *.wav *.flac *.ogg *.m4a)")
        if file_dialog.exec():
            selected_files = file_dialog.selectedFiles()
            for file_path in selected_files:
                url = QUrl.fromLocalFile(file_path)
                self.add_track_to_playlist(url)
            # Автоматически запускаем первый, если ещё ничего не играет
            if not self.player.source().isEmpty():
                return
            if self.playlist_widget.count() > 0:
                self.play_track_at(0)

    def add_track_to_playlist(self, url: QUrl):
        """Добавляет трек в плейлист, если он ещё не добавлен."""
        if url.isEmpty() or not url.isLocalFile():
            return

        url_str = url.toString()
        if url_str in self.added_urls:
            return  # Дубликат — пропускаем

        # Добавляем URL в множество
        self.added_urls.add(url_str)

        file_path = url.toLocalFile()
        fallback_title = os.path.splitext(os.path.basename(file_path))[0]
        fallback_artist = "Unknown Artist"

        item = QListWidgetItem()
        item.setData(Qt.UserRole, url)
        item.setSizeHint(QSize(0, 60))

        widget = PlaylistItemWidget()
        widget.set_track_info(fallback_title, fallback_artist)
        widget.delete_requested.connect(self.on_playlist_item_delete)

        self.playlist_widget.addItem(item)
        self.playlist_widget.setItemWidget(item, widget)

        # Загружаем метаданные асинхронно (как было)
        meta = QMediaPlayer()
        meta.setSource(url)

        def safe_delete():
            if hasattr(meta, "_deleted"):
                return
            meta._deleted = True
            meta.deleteLater()

        def on_meta_loaded():
            title = meta.metaData().value(QMediaMetaData.Title) or fallback_title
            artist = self._get_artist_string(meta.metaData()) or "Unknown Artist"
            cover_pixmap = None

            img = None
            try:
                img = meta.metaData().value(QMediaMetaData.ThumbnailImage)
            except Exception:
                pass
            if not img:
                try:
                    img = meta.metaData().value(QMediaMetaData.CoverArtImage)
                except Exception:
                    pass
            if img:
                if isinstance(img, QImage):
                    cover_pixmap = QPixmap.fromImage(img)
                elif isinstance(img, QPixmap):
                    cover_pixmap = img
                elif isinstance(img, (bytes, bytearray, QByteArray)):
                    try:
                        qimg = QImage.fromData(bytes(img))
                        if not qimg.isNull():
                            cover_pixmap = QPixmap.fromImage(qimg)
                    except Exception:
                        pass
                else:
                    try:
                        qimg = QImage.fromData(img)
                        if not qimg.isNull():
                            cover_pixmap = QPixmap.fromImage(qimg)
                    except Exception:
                        pass

            widget.set_track_info(title, artist, cover_pixmap)
            safe_delete()

        meta.mediaStatusChanged.connect(
            lambda s: on_meta_loaded() if s == QMediaPlayer.MediaStatus.LoadedMedia else None
        )
        QTimer.singleShot(2000, safe_delete)

    def play_track_at(self, index: int):
        item = self.playlist_widget.item(index)
        if item:
            url = item.data(Qt.UserRole)
            self.player.setSource(url)
            self.playlist_widget.setCurrentRow(index)
            self.toggle_play(True)

    def create_controls(self, parent_layout):
        controls = QWidget()
        controls.setStyleSheet("background: transparent;")
        controls_layout = QVBoxLayout(controls)
        # Отступ сверху 25px
        controls_layout.setContentsMargins(0, 25, 0, 25)
        controls_layout.setSpacing(16)

        # Прогресс бар
        progress_widget = QWidget()
        progress_widget.setStyleSheet("background: transparent;")
        progress_layout = QHBoxLayout(progress_widget)
        progress_layout.setContentsMargins(14, 0, 14, 0)
        progress_layout.setSpacing(16)

        self.time_current = QLabel("0:00")
        self.time_current.setStyleSheet("""
            color: #777777;
            font-size: 13px;
            font-family: 'Segoe UI';
            font-weight: 500;
        """)

        self.progress = QSlider(Qt.Horizontal)
        self.progress.setMaximum(245)
        self.progress.setValue(0)
        self.progress.setStyleSheet("""
            QSlider::groove:horizontal {
                height: 4px;
                background: rgba(255, 255, 255, 0.08);
                border-radius: 2px;
                margin-top: 4px;
            }
            QSlider::handle:horizontal {
                background: #888888;
                width: 12px;
                height: 12px;
                border-radius: 6px;
                margin: -4px 0;
            }
            QSlider::sub-page:horizontal {
                background: #888888;
                border-radius: 2px;
                margin-top: 4px;
            }
            QSlider::sub-page:horizontal:hover,
            QSlider::handle:horizontal:hover {
                background: #aaaaaa;
            }
        """)

        self.time_total = QLabel("0:00")
        self.time_total.setStyleSheet("""
            color: #777777;
            font-size: 13px;
            font-family: 'Segoe UI';
            font-weight: 500;
        """)

        progress_layout.addWidget(self.time_current)
        progress_layout.addWidget(self.progress)
        progress_layout.addWidget(self.time_total)

        # Кнопки управления (MAIN LAYOUT)
        buttons_widget = QWidget()
        buttons_widget.setStyleSheet("background: transparent;")
        buttons_layout = QHBoxLayout(buttons_widget)
        buttons_layout.setContentsMargins(14, 0, 14, 0)
        buttons_layout.setSpacing(0)

        # 1. ЛЕВЫЙ БЛОК (Добавить музыку)
        self.add_music_btn = QPushButton()
        self.add_music_btn.setFont(QFont(self.material_font, 20, QFont.Light))
        self.add_music_btn.setText("\ue145") # create_new_folder icon
        self.add_music_btn.setFixedSize(46, 46)
        self.add_music_btn.setCursor(Qt.PointingHandCursor)
        self.add_music_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                color: #888888;
                border-radius: 23px;
            }
            QPushButton:hover {
                color: #ffffff;
                background: rgba(255, 255, 255, 0.05);
            }
        """)
        self.add_music_btn.clicked.connect(self.open_file_dialog)

        # 1b. ЛЕВЫЙ БЛОК (Открыть новые файлы — очистить и добавить)
        self.open_new_btn = QPushButton()
        self.open_new_btn.setFont(QFont(self.material_font, 20, QFont.Light))
        self.open_new_btn.setText("\ue2c7")  # folder_open icon (Material Symbols)
        self.open_new_btn.setFixedSize(46, 46)
        self.open_new_btn.setCursor(Qt.PointingHandCursor)
        self.open_new_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                color: #888888;
                border-radius: 23px;
            }
            QPushButton:hover {
                color: #ffffff;
                background: rgba(255, 255, 255, 0.05);
            }
        """)
        self.open_new_btn.clicked.connect(self.open_new_files)

        # 2. Виджет громкости (ПРАВЫЙ БЛОК)
        volume_widget = QWidget()
        volume_widget.setStyleSheet("background: transparent;")
        volume_layout = QHBoxLayout(volume_widget)
        volume_layout.setContentsMargins(0, 0, 14, 0)
        volume_layout.setSpacing(8)
        volume_layout.setAlignment(Qt.AlignRight)

        self.volume_icon = QPushButton()
        self.volume_icon.setFont(QFont(self.material_font, 22, QFont.Light))
        self.volume_icon.setText("\ue050")
        self.volume_icon.setFixedSize(40, 40)
        self.volume_icon.setCursor(Qt.PointingHandCursor)
        self.volume_icon.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                color: #888888;
                border-radius: 20px;
            }
            QPushButton:hover {
                color: #ffffff;
                background: rgba(255, 255, 255, 0.05);
            }
        """)

        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setMinimumWidth(60)
        self.volume_slider.setMaximumWidth(120)
        self.volume_slider.setMinimum(0)
        self.volume_slider.setMaximum(100)
        self.volume_slider.setValue(60)
        self.volume_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                height: 4px;
                background: rgba(255, 255, 255, 0.08);
                border-radius: 2px;
            }
            QSlider::handle:horizontal {
                background: #888888;
                width: 12px;
                height: 12px;
                border-radius: 6px;
                margin: -4px 0;
            }
            QSlider::sub-page:horizontal {
                background: #888888;
                border-radius: 2px;
            }
            QSlider::sub-page:horizontal:hover,
            QSlider::handle:horizontal:hover {
                background: #aaaaaa;
            }
        """)

        volume_layout.addStretch()
        volume_layout.addWidget(self.volume_icon)
        volume_layout.addWidget(self.volume_slider)
        self.volume_icon.clicked.connect(self.toggle_mute)

        # 3. Центральные кнопки управления (center_buttons)
        center_buttons = QWidget()
        center_buttons.setStyleSheet("background: transparent;")
        center_layout = QHBoxLayout(center_buttons)
        center_layout.setContentsMargins(0, 0, 0, 0)
        center_layout.setSpacing(12)
        center_layout.setAlignment(Qt.AlignCenter)

        # Создание кнопок
        self.shuffle_btn = QPushButton()
        self.shuffle_btn.setFont(QFont(self.material_font, 22, QFont.Light))
        self.shuffle_btn.setText("\ue043")

        self.prev_btn = QPushButton()
        self.prev_btn.setFont(QFont(self.material_font, 26, QFont.Light))
        self.prev_btn.setText("\ue045")

        self.play_btn = QPushButton()
        self.play_btn.setFont(QFont(self.material_font, 28, QFont.Light))
        self.play_btn.setText("\ue037")

        self.next_btn = QPushButton()
        self.next_btn.setFont(QFont(self.material_font, 26, QFont.Light))
        self.next_btn.setText("\ue044")

        self.repeat_btn = QPushButton()
        self.repeat_btn.setFont(QFont(self.material_font, 22, QFont.Light))
        self.repeat_btn.setText("\ue040")

        # Пример для play_btn
        self.play_btn.setFocusPolicy(Qt.NoFocus)
        self.prev_btn.setFocusPolicy(Qt.NoFocus)
        self.next_btn.setFocusPolicy(Qt.NoFocus)
        self.shuffle_btn.setFocusPolicy(Qt.NoFocus)
        self.repeat_btn.setFocusPolicy(Qt.NoFocus)
        self.add_music_btn.setFocusPolicy(Qt.NoFocus)
        self.volume_icon.setFocusPolicy(Qt.NoFocus)

        # Для слайдеров
        self.progress.setFocusPolicy(Qt.NoFocus)
        self.volume_slider.setFocusPolicy(Qt.NoFocus)

        # Общие стили для кнопок
        for btn in [self.shuffle_btn, self.prev_btn, self.next_btn, self.repeat_btn]:
            btn.setFixedSize(46, 46)
            btn.setFocusPolicy(Qt.NoFocus)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setStyleSheet("""
                QPushButton {
                    background: transparent;
                    border: none;
                    color: #888888;
                    border-radius: 23px;
                }
                QPushButton:hover {
                    color: #ffffff;
                    background: rgba(255, 255, 255, 0.05);
                }
                QPushButton:pressed {
                    background: rgba(255, 255, 255, 0.1);
                }
            """)

        self.play_btn.setFixedSize(46, 46)
        self.play_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                border-radius: 12px;
                color: #888888;
                padding-left: 2px;
            }
            QPushButton:hover {
                color: #ffffff;
                background: rgba(255, 255, 255, 0.05);
            }
            QPushButton:pressed {
                background: rgba(255, 255, 255, 0.1);
            }
        """)

        self.shuffle_btn.clicked.connect(self.toggle_shuffle)
        self.prev_btn.clicked.connect(self.play_prev)
        self.play_btn.clicked.connect(lambda: self.toggle_play())
        self.next_btn.clicked.connect(self.play_next)
        self.repeat_btn.clicked.connect(self.toggle_repeat)

        center_layout.addWidget(self.shuffle_btn)
        center_layout.addWidget(self.prev_btn)
        center_layout.addWidget(self.play_btn)
        center_layout.addWidget(self.next_btn)
        center_layout.addWidget(self.repeat_btn)

        # -----------------------------------------------------------
        # СБОРКА buttons_layout (FIXED ORDER)
        
        # 1. Left Block: Add Music Button
        buttons_layout.addWidget(self.add_music_btn)
        buttons_layout.addWidget(self.open_new_btn) 

        # 2. Stretch 1 (Push center block to the middle)
        buttons_layout.addStretch(1)           

        volume_spacer_widget = QWidget()
        # Задаем фиксированную ширину, равную кнопке "Добавить музыку"
        # 46px (ширина кнопки) + 0px (spacing).
        volume_spacer_widget.setFixedWidth(54)
        volume_spacer_widget.setStyleSheet("background: transparent;")
        
        buttons_layout.addWidget(volume_spacer_widget)

        # 3. Center Block: Playback Controls
        buttons_layout.addWidget(center_buttons) 

        # 4. Stretch 2 (Push center block to the middle)
        buttons_layout.addStretch(1)           

        # 5. Right Block: Volume Control
        buttons_layout.addWidget(volume_widget)  

        # -----------------------------------------------------------
        # СБОРКА controls_layout (Hierarchy)

        controls_layout.addWidget(progress_widget)
        controls_layout.addWidget(buttons_widget)
        parent_layout.addWidget(controls)

    def open_new_files(self):
        """Очищает плейлист и открывает новые файлы."""
        # Очищаем плейлист
        self.playlist_widget.clear()
        self.added_urls.clear()
        # Очищаем источник плеера, если он был
        self.player.setSource(QUrl())
        # Сбрасываем UI
        self.track_name_label.setText("Select a file to play")
        self.artist_name_label.setText("")
        self.album_cover_bg.set_cover(None)
        self.play_btn.setText("\ue037")  # play_arrow icon
        self.is_playing = False

        # Открываем диалог выбора файлов
        file_dialog = QFileDialog()
        file_dialog.setFileMode(QFileDialog.ExistingFiles)
        file_dialog.setNameFilter("Audio Files (*.mp3 *.wav *.flac *.ogg *.m4a)")
        if file_dialog.exec():
            selected_files = file_dialog.selectedFiles()
            for file_path in selected_files:
                url = QUrl.fromLocalFile(file_path)
                self.add_track_to_playlist(url)
            # Автоматически запускаем первый трек, если плейлист не пуст
            if self.playlist_widget.count() > 0:
                self.play_track_at(0)

    def toggle_mute(self):
        if self.is_muted:
            # Восстанавливаем громкость
            self.player.audioOutput().setVolume(self.last_volume / 100.0)
            self.volume_slider.setValue(self.last_volume)
            self.is_muted = False
            # Иконка: звук включён
            self.volume_icon.setText("\ue050")  # volume_up
        else:
            # Сохраняем текущую громкость и отключаем
            self.last_volume = self.volume_slider.value()
            self.player.audioOutput().setVolume(0)
            self.volume_slider.setValue(0)
            self.is_muted = True
            # Иконка: мут
            self.volume_icon.setText("\ue04f")  # volume_off

    def toggle_play(self, force_play=None):
        """Переключает состояние воспроизведения/паузы."""
        if force_play is not None:
            self.is_playing = force_play
        else:
            # Only toggle if a source is set (QoL fix)
            if self.player.source().isEmpty():
                # If no file is loaded, clicking play should open file dialog
                self.open_file_dialog()
                return

            self.is_playing = not self.is_playing

        if self.is_playing:
            self.player.play()
            self.play_btn.setText("\ue034")  # pause icon
        else:
            self.player.pause()
            self.play_btn.setText("\ue037")  # play_arrow icon

    def on_playlist_selection_changed(self):
        """Обрабатывает изменение выделения в плейлисте."""
        # Применяем стиль ко всем элементам
        for i in range(self.playlist_widget.count()):
            item = self.playlist_widget.item(i)
            widget = self.playlist_widget.itemWidget(item)
            if widget:
                is_selected = item.isSelected()
                widget.set_selected_style(is_selected)

    def on_playlist_item_double_clicked(self, item):
        """Обрабатывает двойной клик по элементу плейлиста."""
        index = self.playlist_widget.row(item)
        self.play_track_at(index)

    def keyPressEvent(self, event):
        key = event.key()
        modifiers = event.modifiers()

        # Play / Pause
        if key == Qt.Key_Space:
            self.toggle_play()
        # Prev / Next
        elif key == Qt.Key_Left:
            self.play_prev()
        elif key == Qt.Key_Right:
            self.play_next()
        # Громкость
        elif key == Qt.Key_Up:
            current = self.volume_slider.value()
            self.volume_slider.setValue(min(100, current + 5))
        elif key == Qt.Key_Down:
            current = self.volume_slider.value()
            self.volume_slider.setValue(max(0, current - 5))
        # Mute / Unmute
        elif key == Qt.Key_M:
            self.toggle_mute()
        # Переключить плейлист
        elif key == Qt.Key_P:
            self.toggle_playlist()
        # Shuffle
        elif key == Qt.Key_S:
            self.toggle_shuffle()
        # Repeat
        elif key == Qt.Key_R:
            self.toggle_repeat()
        # Открыть файлы
        elif key == Qt.Key_O and not modifiers:
            self.open_file_dialog()
        # Ctrl+O — тоже можно, но не обязательно; если хочешь — раскомментируй else ниже
        else:
            super().keyPressEvent(event)

if __name__ == "__main__":
    import platform

    # В блоке if __name__ == "__main__":
    if platform.system() == "Windows":
        try:
            import ctypes
            myappid = 'my.noxplayer.v1'
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
        except Exception:
            pass

    app = QApplication(sys.argv)
    
    # Устанавливаем иконку для ВСЕГО приложения
    app_icon = QIcon(resource_path("icon.ico"))
    app.setWindowIcon(app_icon)
    
    window = NoxPlayer()
    window.show()
    sys.exit(app.exec())