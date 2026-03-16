from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton
from PyQt5.QtCore import Qt, QPoint
from PyQt5.QtGui import QFont, QPixmap
from utils import resource_path


class TitleBar(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent   = parent
        self.pressing = False
        self.start    = QPoint(0, 0)
        self.setFixedHeight(42)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 2, 10, 0)
        layout.setSpacing(0)

        # ── Левая часть ──
        left = QWidget(); left.setStyleSheet("background:transparent;")
        ll = QHBoxLayout(left); ll.setContentsMargins(0,0,0,0); ll.setSpacing(14)

        logo = QLabel()
        logo.setFixedSize(24, 24); logo.setScaledContents(True)
        px = QPixmap(resource_path("icon.ico"))
        if not px.isNull():
            logo.setPixmap(px.scaled(24, 24, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        logo.setStyleSheet("background:transparent;")

        title = QLabel("NoxPlayer")
        title.setStyleSheet("color:#fff;font-size:16px;font-weight:600;font-family:'Segoe UI',Arial;")

        ll.addWidget(logo); ll.addWidget(title); ll.addStretch()

        # ── Центр ──
        center = QWidget(); center.setStyleSheet("background:transparent;")
        cl = QHBoxLayout(center); cl.setContentsMargins(0,0,0,0); cl.setAlignment(Qt.AlignCenter)

        # ── Правая часть ──
        right = QWidget(); right.setStyleSheet("background:transparent;")
        rl = QHBoxLayout(right); rl.setContentsMargins(0,0,0,0); rl.setAlignment(Qt.AlignRight); rl.setSpacing(6)

        pl_btn = QPushButton()
        pl_btn.setFont(QFont("Material Symbols Rounded", 18))
        pl_btn.setText("\ue3c7"); pl_btn.setFixedSize(18, 18); pl_btn.setCursor(Qt.PointingHandCursor)
        pl_btn.setStyleSheet("""
            QPushButton{background:transparent;color:#999;border:1px solid transparent;
                border-radius:8px;font-size:25px;text-align:center;font-weight:500;}
            QPushButton:hover{color:#fff;background:rgba(255,255,255,0.05);}
            QPushButton:pressed{background:rgba(255,255,255,0.1);}
        """)
        pl_btn.clicked.connect(self.parent.toggle_playlist)

        min_btn = self._win_btn("\ue15b", 18)
        max_btn = self._win_btn("\ue3c6", 14)
        cls_btn = self._win_btn("\ue5cd", 18, close=True)

        min_btn.clicked.connect(self.parent.showMinimized)
        max_btn.clicked.connect(self._toggle_max)
        cls_btn.clicked.connect(self.parent.close)

        rl.addWidget(min_btn); rl.addWidget(max_btn); rl.addWidget(cls_btn)

        layout.addWidget(left, 1)
        layout.addStretch(1)
        layout.addWidget(center, 0)
        layout.addStretch(1)
        layout.addWidget(right, 1)

    def _win_btn(self, icon, size, close=False):
        btn = QPushButton(); btn.setFont(QFont("Material Symbols Rounded", size))
        btn.setText(icon); btn.setFixedSize(28, 28)
        btn.setFocusPolicy(Qt.NoFocus); btn.setCursor(Qt.PointingHandCursor)
        if close:
            btn.setStyleSheet("""
                QPushButton{background:transparent;color:#888;border:none;border-radius:6px;font-weight:300;}
                QPushButton:hover{background:#e81123;color:#fff;}
            """)
        else:
            btn.setStyleSheet("""
                QPushButton{background:transparent;color:#888;border:none;border-radius:6px;font-weight:300;}
                QPushButton:hover{background:rgba(255,255,255,0.08);color:#fff;}
            """)
        return btn

    def _toggle_max(self):
        if self.parent.isMaximized(): self.parent.showNormal()
        else: self.parent.showMaximized()
        self.parent.update_window_style()

    def mouseDoubleClickEvent(self, e):
        if e.button() == Qt.LeftButton:
            self._toggle_max()

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self.pressing = True
            self.start = e.globalPos()
            if self.parent.isMaximized():
                click_pos = int(e.pos().x())
                self.parent.showNormal()
                self.parent.update_window_style()
                w = self.parent.width()
                new_x = int(self.start.x() - w * click_pos / self.width())
                self.parent.move(new_x, 0)
                self.start = QPoint(self.parent.x() + click_pos, e.globalPos().y())

    def mouseMoveEvent(self, e):
        if self.pressing:
            self.parent.move(self.parent.pos() + e.globalPos() - self.start)
            self.start = e.globalPos()

    def mouseReleaseEvent(self, e):
        self.pressing = False
