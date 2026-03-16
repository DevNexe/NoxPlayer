from PyQt5.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel, QPushButton
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QFontMetrics
from widgets.album_cover import AlbumCover


class PlaylistItemWidget(QWidget):
    delete_requested = pyqtSignal(QWidget)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(60)
        self.setStyleSheet("background: transparent;")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(12)

        self.cover = AlbumCover(radius=6, cover_ratio=1.0, blur_radius=0, is_playlist_item=True)
        self.cover.setFixedSize(48, 48)
        self.cover.setStyleSheet("background: transparent;")
        layout.addWidget(self.cover)

        text = QVBoxLayout()
        text.setContentsMargins(0, 0, 0, 0)
        text.setSpacing(2)

        self.title_lbl = QLabel()
        self.title_lbl.setStyleSheet(
            "color:#fff;font-size:15px;font-weight:600;font-family:'Segoe UI',Arial;background:transparent;")
        self.title_lbl.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        self.artist_lbl = QLabel()
        self.artist_lbl.setStyleSheet(
            "color:rgba(255,255,255,0.7);font-size:13px;font-family:'Segoe UI',Arial;background:transparent;")
        self.artist_lbl.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        text.addWidget(self.title_lbl)
        text.addWidget(self.artist_lbl)
        layout.addLayout(text)
        layout.addStretch()

        self.del_btn = QPushButton()
        self.del_btn.setFont(QFont("Material Symbols Rounded", 16))
        self.del_btn.setText("\ue5cd")
        self.del_btn.setFixedSize(20, 20)
        self.del_btn.setCursor(Qt.PointingHandCursor)
        self.del_btn.setStyleSheet("""
            QPushButton{background:rgba(255,255,255,0.15);color:#ff5555;border-radius:10px;padding:0px;}
            QPushButton:hover{background:rgba(255,85,85,0.3);color:#fff;}
        """)
        self.del_btn.hide()
        self.del_btn.clicked.connect(lambda: self.delete_requested.emit(self))
        layout.addWidget(self.del_btn)

    def set_track_info(self, title, artist, cover_pixmap=None):
        self._title  = str(title)  if title  else ""
        self._artist = str(artist) if artist else ""
        self.title_lbl.setToolTip(self._title)
        self.artist_lbl.setToolTip(self._artist)
        self._elide()
        self.cover.set_cover(cover_pixmap)

    def enterEvent(self, e): self.del_btn.show(); super().enterEvent(e)
    def leaveEvent(self, e): self.del_btn.hide(); super().leaveEvent(e)

    def _elide(self):
        aw = max(10, self.width() - 48 - 24)
        self.title_lbl.setText(QFontMetrics(self.title_lbl.font()).elidedText(self._title, Qt.ElideRight, aw))
        self.artist_lbl.setText(QFontMetrics(self.artist_lbl.font()).elidedText(self._artist, Qt.ElideRight, aw))

    def resizeEvent(self, e):
        super().resizeEvent(e)
        if hasattr(self, '_title'): self._elide()

    def set_selected(self, sel):
        self.setStyleSheet("background:rgba(0,120,255,0.2);border-radius:8px;" if sel else "background:transparent;")
