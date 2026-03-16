import os
import random

from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QSplitter, QListWidget, QListWidgetItem, QLabel,
                             QPushButton, QSlider, QFileDialog, QSizePolicy,
                             QGraphicsDropShadowEffect)
from PyQt5.QtCore import Qt, QUrl, QSize, QTimer, QSettings, QCoreApplication
from PyQt5.QtGui import QFont, QFontDatabase, QIcon, QColor, QPixmap, QImage
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent

from utils import resource_path, get_music_dir, get_artist_string
from widgets.title_bar import TitleBar
from widgets.album_cover import AlbumCover
from widgets.playlist_item import PlaylistItemWidget
from widgets.marquee_label import MarqueeLabel, OutlineLabel


class NoxPlayer(QMainWindow):
    LAST_TRACK_KEY = "lastTrackPath"
    SHUFFLE_KEY    = "shuffleMode"
    REPEAT_KEY     = "repeatMode"

    def __init__(self):
        super().__init__()
        self.setFixedSize(960, 740)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setWindowIcon(QIcon(resource_path("icon.ico")))

        self._init_player()

        self.shuffle_mode = False
        self.repeat_mode  = 0
        self.is_muted     = False
        self.last_volume  = 60

        # Шрифт
        fp = resource_path("MaterialSymbolsRounded.ttf")
        if os.path.exists(fp):
            fid = QFontDatabase.addApplicationFont(fp)
            fams = QFontDatabase.applicationFontFamilies(fid) if fid != -1 else []
            self.mfont = fams[0] if fams else "Segoe UI"
        else:
            self.mfont = "Segoe UI"

        # Центральный виджет
        central = QWidget()
        self.setCentralWidget(central)
        self.added_urls = set()
        self.update_window_style()

        ml = QVBoxLayout(central)
        ml.setContentsMargins(0, 0, 0, 0)
        ml.setSpacing(0)

        self.title_bar = TitleBar(self)
        ml.addWidget(self.title_bar)

        # Контент
        content = QWidget()
        content.setStyleSheet("background:transparent;")
        cl = QVBoxLayout(content)
        cl.setContentsMargins(12, 0, 12, 0)
        cl.setAlignment(Qt.AlignTop | Qt.AlignHCenter)

        album_c = QWidget()
        album_c.setStyleSheet("background:transparent;")
        album_c.setMinimumWidth(300)
        album_c.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        al = QVBoxLayout(album_c)
        al.setContentsMargins(0, 0, 0, 0)
        al.setSpacing(0)

        self.cover = AlbumCover(radius=16, cover_ratio=0.7, blur_radius=30, vertical_offset_ratio=0.15)
        ov = QVBoxLayout(self.cover)
        ov.setContentsMargins(25, 0, 25, 25)
        ov.setSpacing(0)
        ov.addStretch(1)

        self.track_lbl = MarqueeLabel("")
        self.track_lbl.setAlignment(Qt.AlignLeft)
        self.track_lbl.setStyleSheet(
            "color:#fff;font-size:34px;font-weight:600;font-family:'Segoe UI',Arial;"
            "background:transparent;letter-spacing:-0.5px;")
        self.track_lbl.setOutlineWidth(2)
        self.track_lbl.setOutlineColor(QColor(0, 0, 0))
        self.track_lbl.setOutlineBlurRadius(4)

        self.artist_lbl = OutlineLabel("Select a file to play")
        self.artist_lbl.setAlignment(Qt.AlignLeft)
        self.artist_lbl.setStyleSheet(
            "color:rgba(255,255,255,0.7);font-size:17px;font-family:'Segoe UI',Arial;background:transparent;")
        self.artist_lbl.setOutlineWidth(1)
        self.artist_lbl.setOutlineColor(QColor(0, 0, 0))
        self.artist_lbl.setOutlineBlurRadius(3)

        ov.addWidget(self.track_lbl)
        ov.addWidget(self.artist_lbl)

        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(40)
        shadow.setColor(QColor(0, 0, 0, 120))
        shadow.setOffset(0, 10)
        self.cover.setGraphicsEffect(shadow)

        al.addWidget(self.cover, 1)
        cl.addWidget(album_c, 1)

        # Плейлист
        self.playlist = QListWidget()
        self.playlist.setMinimumWidth(0)
        self.playlist.setMaximumWidth(600)
        self.playlist.setStyleSheet("""
            QListWidget{background:#0f0f0f;border:none;border-radius:0;
                padding:12px;padding-right:0;margin:0;padding-left:0;}
            QListWidget::item{padding:0;margin:0;}
            QListWidget::item:selected{background:transparent;}
            QListWidget::item:hover{background:transparent;}
            QScrollBar:vertical{border:none;background:#0f0f0f;width:10px;margin:10px 2px 10px 0;}
            QScrollBar::handle:vertical{background:rgba(255,255,255,40);min-height:30px;border-radius:4px;}
            QScrollBar::handle:vertical:hover{background:rgba(255,255,255,80);}
            QScrollBar::add-line:vertical,QScrollBar::sub-line:vertical{background:none;height:0;}
            QScrollBar::add-page:vertical,QScrollBar::sub-page:vertical{background:none;}
        """)
        self.playlist.itemSelectionChanged.connect(self._on_selection_changed)
        self.playlist.itemClicked.connect(lambda item: self.play_at(self.playlist.row(item)))

        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(6)
        splitter.setStyleSheet("""
            QSplitter::handle{background:#0f0f0f;border-radius:6px;
                border-top-right-radius:0;border-bottom-right-radius:0;}
            QSplitter::handle:hover{background:rgba(255,255,255,0.15);}
        """)
        splitter.addWidget(content)
        splitter.addWidget(self.playlist)
        splitter.setSizes([content.width(), 0])
        ml.addWidget(splitter, 1)

        self._build_controls(ml)

        # Сигналы
        self.player.positionChanged.connect(self._on_position)
        self.player.durationChanged.connect(self._on_duration)
        self.player.mediaStatusChanged.connect(self._on_media_status)
        self.prog.sliderMoved.connect(self.player.setPosition)
        self.vol_slider.setValue(60)
        self.vol_slider.valueChanged.connect(self._on_volume)
        self.time_total.setText(self._fmt(0))

        self.load_session()
        self.activateWindow()
        self.setFocus()
        self._load_settings()

    # ── Плеер ──────────────────────────────────────────────────────────────

    def _init_player(self):
        QCoreApplication.setOrganizationName("NoxSoftware")
        QCoreApplication.setApplicationName("NoxPlayer")
        self.player = QMediaPlayer()
        self.player.setVolume(60)
        self.is_playing = False

        # Детектор смены аудио устройства
        self._last_device = self._device_name()
        self._dev_timer = QTimer()
        self._dev_timer.setInterval(2000)
        self._dev_timer.timeout.connect(self._check_device)
        self._dev_timer.start()

    def _device_name(self):
        try:
            from PyQt5.QtMultimedia import QAudioDeviceInfo
            return QAudioDeviceInfo.defaultOutputDevice().deviceName()
        except Exception:
            return ""

    def _check_device(self):
        name = self._device_name()
        if name != self._last_device:
            self._last_device = name
            if self.is_playing:
                pos   = self.player.position()
                media = self.player.media()
                self.player.stop()
                QTimer.singleShot(400, lambda: self._restore(media, pos))

    def _restore(self, media, pos):
        self.player.setMedia(media)
        self.player.setPosition(pos)
        self.player.play()

    # ── Контролы ───────────────────────────────────────────────────────────

    def _build_controls(self, parent_layout):
        wrap = QWidget(); wrap.setStyleSheet("background:transparent;")
        wl = QVBoxLayout(wrap); wl.setContentsMargins(0, 25, 0, 25); wl.setSpacing(16)

        # Прогресс
        pw = QWidget(); pw.setStyleSheet("background:transparent;")
        pl = QHBoxLayout(pw); pl.setContentsMargins(14, 0, 14, 0); pl.setSpacing(16)

        self.time_cur = QLabel("0:00")
        self.time_cur.setStyleSheet("color:#777;font-size:13px;font-family:'Segoe UI';font-weight:500;")

        self.prog = QSlider(Qt.Horizontal)
        self.prog.setMaximum(245); self.prog.setValue(0); self.prog.setFocusPolicy(Qt.NoFocus)
        self.prog.setStyleSheet("""
            QSlider::groove:horizontal{height:4px;background:rgba(255,255,255,0.08);border-radius:2px;margin-top:4px;}
            QSlider::handle:horizontal{background:#888;width:12px;height:12px;border-radius:6px;margin:-4px 0;}
            QSlider::sub-page:horizontal{background:#888;border-radius:2px;margin-top:4px;}
            QSlider::sub-page:horizontal:hover,QSlider::handle:horizontal:hover{background:#aaa;}
        """)

        self.time_total = QLabel("0:00")
        self.time_total.setStyleSheet("color:#777;font-size:13px;font-family:'Segoe UI';font-weight:500;")

        pl.addWidget(self.time_cur); pl.addWidget(self.prog); pl.addWidget(self.time_total)

        # Кнопки
        bw = QWidget(); bw.setStyleSheet("background:transparent;")
        bl = QHBoxLayout(bw); bl.setContentsMargins(14, 0, 14, 0); bl.setSpacing(0)

        self.add_btn = self._icon_btn("\ue145", 20); self.add_btn.clicked.connect(self.open_files)
        self.dir_btn = self._icon_btn("\ue2c7", 20); self.dir_btn.clicked.connect(self.open_folder)

        # Громкость
        vw = QWidget(); vw.setStyleSheet("background:transparent;")
        vl = QHBoxLayout(vw); vl.setContentsMargins(0, 0, 14, 0); vl.setSpacing(8); vl.setAlignment(Qt.AlignRight)

        self.vol_icon = QPushButton()
        self.vol_icon.setFont(QFont(self.mfont, 22, QFont.Light))
        self.vol_icon.setText("\ue050"); self.vol_icon.setFixedSize(40, 40)
        self.vol_icon.setCursor(Qt.PointingHandCursor); self.vol_icon.setFocusPolicy(Qt.NoFocus)
        self.vol_icon.setStyleSheet(
            "QPushButton{background:transparent;border:none;color:#888;border-radius:20px;}"
            "QPushButton:hover{color:#fff;background:rgba(255,255,255,0.05);}")
        self.vol_icon.clicked.connect(self.toggle_mute)

        self.vol_slider = QSlider(Qt.Horizontal)
        self.vol_slider.setMinimumWidth(60); self.vol_slider.setMaximumWidth(120)
        self.vol_slider.setMinimum(0); self.vol_slider.setMaximum(100)
        self.vol_slider.setFocusPolicy(Qt.NoFocus)
        self.vol_slider.setStyleSheet("""
            QSlider::groove:horizontal{height:4px;background:rgba(255,255,255,0.08);border-radius:2px;}
            QSlider::handle:horizontal{background:#888;width:12px;height:12px;border-radius:6px;margin:-4px 0;}
            QSlider::sub-page:horizontal{background:#888;border-radius:2px;}
            QSlider::sub-page:horizontal:hover,QSlider::handle:horizontal:hover{background:#aaa;}
        """)
        vl.addStretch(); vl.addWidget(self.vol_icon); vl.addWidget(self.vol_slider)

        # Центр
        cw = QWidget(); cw.setStyleSheet("background:transparent;")
        ccl = QHBoxLayout(cw); ccl.setContentsMargins(0, 0, 0, 0); ccl.setSpacing(12); ccl.setAlignment(Qt.AlignCenter)

        self.shuf_btn   = self._ctrl_btn("\ue043", 22)
        self.prev_btn   = self._ctrl_btn("\ue045", 26)
        self.play_btn   = self._ctrl_btn("\ue037", 28)
        self.next_btn   = self._ctrl_btn("\ue044", 26)
        self.repeat_btn = self._ctrl_btn("\ue040", 22)

        self.shuf_btn.clicked.connect(self.toggle_shuffle)
        self.prev_btn.clicked.connect(self.play_prev)
        self.play_btn.clicked.connect(lambda: self.toggle_play())
        self.next_btn.clicked.connect(self.play_next)
        self.repeat_btn.clicked.connect(self.toggle_repeat)

        for b in [self.shuf_btn, self.prev_btn, self.play_btn, self.next_btn, self.repeat_btn]:
            ccl.addWidget(b)

        sp = QWidget(); sp.setFixedWidth(54); sp.setStyleSheet("background:transparent;")

        bl.addWidget(self.add_btn); bl.addWidget(self.dir_btn)
        bl.addStretch(1); bl.addWidget(sp); bl.addWidget(cw)
        bl.addStretch(1); bl.addWidget(vw)

        wl.addWidget(pw); wl.addWidget(bw)
        parent_layout.addWidget(wrap)

    def _icon_btn(self, icon, size):
        b = QPushButton(); b.setFont(QFont(self.mfont, size, QFont.Light))
        b.setText(icon); b.setFixedSize(46, 46); b.setCursor(Qt.PointingHandCursor); b.setFocusPolicy(Qt.NoFocus)
        b.setStyleSheet("QPushButton{background:transparent;border:none;color:#888;border-radius:23px;}"
                        "QPushButton:hover{color:#fff;background:rgba(255,255,255,0.05);}")
        return b

    def _ctrl_btn(self, icon, size):
        b = QPushButton(); b.setFont(QFont(self.mfont, size, QFont.Light))
        b.setText(icon); b.setFixedSize(46, 46); b.setCursor(Qt.PointingHandCursor); b.setFocusPolicy(Qt.NoFocus)
        b.setStyleSheet("QPushButton{background:transparent;border:none;color:#888;border-radius:23px;}"
                        "QPushButton:hover{color:#fff;background:rgba(255,255,255,0.05);}"
                        "QPushButton:pressed{background:rgba(255,255,255,0.1);}")
        return b

    # ── Плейлист ───────────────────────────────────────────────────────────

    def add_track(self, url):
        if url.isEmpty() or not url.isLocalFile():
            return
        s = url.toString()
        if s in self.added_urls:
            return
        self.added_urls.add(s)

        fp       = url.toLocalFile()
        fallback = os.path.splitext(os.path.basename(fp))[0]

        item = QListWidgetItem()
        item.setData(Qt.UserRole, url)
        item.setSizeHint(QSize(0, 60))

        widget = PlaylistItemWidget()
        widget.set_track_info(fallback, "Unknown Artist")
        widget.delete_requested.connect(self._on_delete)

        self.playlist.addItem(item)
        self.playlist.setItemWidget(item, widget)

        # Загрузка метаданных через mutagen (без WMF — нет session close timeout)
        QTimer.singleShot(0, lambda: self._load_metadata(url, widget, fallback))

    def _load_metadata(self, url, widget, fallback):
        """Загружает метаданные через mutagen — без WMF и без session close timeout."""
        try:
            from mutagen import File as MFile
            fp    = url.toLocalFile()
            audio = MFile(fp, easy=True)
            if audio is None:
                return
            title  = str(audio.get("title",  [fallback])[0])
            artist = str(audio.get("artist", ["Unknown Artist"])[0])

            # Обложка
            cover = None
            try:
                raw = MFile(fp)
                if raw and raw.tags:
                    for tag in raw.tags.values():
                        if hasattr(tag, "data"):
                            qi = QImage.fromData(tag.data)
                            if not qi.isNull():
                                cover = QPixmap.fromImage(qi)
                                break
            except Exception:
                pass

            try:
                widget.set_track_info(title, artist, cover)
            except RuntimeError:
                pass
        except ImportError:
            pass  # mutagen не установлен — оставляем fallback
        except Exception:
            pass

    def play_at(self, index):
        item = self.playlist.item(index)
        if item:
            self.player.setMedia(QMediaContent(item.data(Qt.UserRole)))
            self.playlist.setCurrentRow(index)
            self.toggle_play(True)

    def _on_delete(self, widget):
        for i in range(self.playlist.count()):
            item = self.playlist.item(i)
            if self.playlist.itemWidget(item) is widget:
                url     = item.data(Qt.UserRole)
                current = self.player.media().canonicalUrl()
                is_cur  = (url == current)
                if url and not url.isEmpty():
                    self.added_urls.discard(url.toString())
                self.playlist.takeItem(i)
                if is_cur:
                    self.player.stop()
                    self.player.setMedia(QMediaContent())
                    self.track_lbl.setText("Select a file to play")
                    self.artist_lbl.setText("")
                    self.cover.set_cover(None)
                    self.play_btn.setText("\ue037")
                    self.is_playing = False
                break

    def _on_selection_changed(self):
        for i in range(self.playlist.count()):
            item = self.playlist.item(i)
            w = self.playlist.itemWidget(item)
            if w: w.set_selected(item.isSelected())

    def toggle_playlist(self):
        sp = self.playlist.parent()
        if not isinstance(sp, QSplitter): return
        sz = sp.sizes()
        sp.setSizes([sz[0], 280] if sz[1] <= 5 else [sz[0]+sz[1], 0])

    def _dedup(self):
        seen, rm = set(), []
        for i in range(self.playlist.count()-1, -1, -1):
            item = self.playlist.item(i)
            if item:
                url = item.data(Qt.UserRole)
                if url and not url.isEmpty():
                    s = url.toString()
                    if s in seen: rm.append(i)
                    else: seen.add(s)
        for i in sorted(rm, reverse=True): self.playlist.takeItem(i)
        self.added_urls = seen.copy()

    # ── Воспроизведение ────────────────────────────────────────────────────

    def toggle_play(self, force=None):
        if force is not None:
            self.is_playing = force
        else:
            if self.player.media().isNull():
                self.open_files(); return
            self.is_playing = not self.is_playing
        if self.is_playing:
            self.player.play(); self.play_btn.setText("\ue034")
        else:
            self.player.pause(); self.play_btn.setText("\ue037")

    def play_next(self):
        n = self.playlist.count()
        if n: self.play_at((self.playlist.currentRow() + 1) % n)

    def _play_next_on_end(self):
        n = self.playlist.count()
        if not n: return
        row = self.playlist.currentRow()
        if self.repeat_mode == 0 and row == n - 1:
            self.toggle_play(False); return
        self.play_at((row + 1) % n)

    def play_prev(self):
        n = self.playlist.count()
        if not n: return
        row = self.playlist.currentRow()
        if self.shuffle_mode and n > 1:
            r = random.randint(0, n-1)
            while r == row: r = random.randint(0, n-1)
        elif self.repeat_mode == 2:
            r = row
        else:
            r = (row - 1) % n
        self.play_at(r)

    def _on_media_status(self, status):
        if status == QMediaPlayer.EndOfMedia:
            if self.repeat_mode == 2:
                self.player.setPosition(0); self.player.play()
            else:
                self._play_next_on_end()
        elif status == QMediaPlayer.LoadedMedia:
            self._update_track_info()

    def _update_track_info(self):
        title  = self.player.metaData("Title") or ""
        artist = get_artist_string(self.player)
        media  = self.player.media().canonicalUrl()
        fb     = os.path.splitext(os.path.basename(media.toLocalFile()))[0]
        self.track_lbl.setText(title or fb or "Unknown Title")
        self.artist_lbl.setText(artist or "Unknown Artist")

        img = self.player.metaData("ThumbnailImage") or self.player.metaData("CoverArtImage")
        px  = None
        if img:
            if isinstance(img, QImage): px = QPixmap.fromImage(img)
            elif isinstance(img, QPixmap): px = img
            elif isinstance(img, (bytes, bytearray)):
                try:
                    qi = QImage.fromData(bytes(img))
                    if not qi.isNull(): px = QPixmap.fromImage(qi)
                except Exception: pass
        self.cover.set_cover(px)

    # ── Позиция / громкость ────────────────────────────────────────────────

    def _on_position(self, pos):
        if not self.prog.isSliderDown():
            self.prog.setValue(pos)
            self.time_cur.setText(self._fmt(pos))

    def _on_duration(self, dur):
        self.prog.setMaximum(dur)
        self.time_total.setText(self._fmt(dur))
        self.prog.setValue(0)
        self.time_cur.setText(self._fmt(0))

    def _on_volume(self, v):
        self.player.setVolume(v)
        if self.is_muted and v > 0:
            self.is_muted = False
            self.vol_icon.setText("\ue050")

    def toggle_mute(self):
        if self.is_muted:
            self.player.setVolume(self.last_volume)
            self.vol_slider.setValue(self.last_volume)
            self.is_muted = False
            self.vol_icon.setText("\ue050")
        else:
            self.last_volume = self.vol_slider.value()
            self.player.setVolume(0)
            self.vol_slider.setValue(0)
            self.is_muted = True
            self.vol_icon.setText("\ue04f")

    @staticmethod
    def _fmt(ms):
        s = int(ms / 1000)
        return f"{s//60}:{s%60:02d}"

    # ── Shuffle / Repeat ───────────────────────────────────────────────────

    def toggle_shuffle(self):
        self.shuffle_mode = not self.shuffle_mode
        QSettings().setValue(self.SHUFFLE_KEY, self.shuffle_mode)
        if self.shuffle_mode and self.repeat_mode == 2:
            self.repeat_mode = 0; self._apply_repeat()
        c = "#fff" if self.shuffle_mode else "#888"
        self.shuf_btn.setStyleSheet(
            f"QPushButton{{background:transparent;border:none;color:{c};border-radius:23px;}}"
            "QPushButton:hover{color:#fff;background:rgba(255,255,255,0.05);}")

    def toggle_repeat(self):
        old = self.repeat_mode
        self.repeat_mode = (self.repeat_mode + 1) % 3
        QSettings().setValue(self.REPEAT_KEY, self.repeat_mode)
        if old != 2 and self.repeat_mode == 2:
            self.shuffle_mode = False
            self.shuf_btn.setStyleSheet(
                "QPushButton{background:transparent;border:none;color:#888;border-radius:23px;}"
                "QPushButton:hover{color:#fff;background:rgba(255,255,255,0.05);}")
        self._apply_repeat()

    def _apply_repeat(self):
        icons  = {0: ("\ue040", "#888"), 1: ("\ue040", "#fff"), 2: ("\ue041", "#fff")}
        ic, c  = icons[self.repeat_mode]
        self.repeat_btn.setText(ic)
        self.repeat_btn.setStyleSheet(
            f"QPushButton{{background:transparent;border:none;color:{c};border-radius:23px;}}"
            "QPushButton:hover{color:#fff;background:rgba(255,255,255,0.05);}")

    def _load_settings(self):
        s = QSettings()
        self.shuffle_mode = s.value(self.SHUFFLE_KEY, False, type=bool)
        if self.shuffle_mode:
            self.shuf_btn.setStyleSheet("QPushButton{color:#fff;}")
        self.repeat_mode = int(s.value(self.REPEAT_KEY, 0))
        self._apply_repeat()

    # ── Файловые диалоги ───────────────────────────────────────────────────

    def open_files(self):
        fd = QFileDialog()
        fd.setFileMode(QFileDialog.ExistingFiles)
        fd.setNameFilter("Audio Files (*.mp3 *.wav *.flac *.ogg *.m4a)")
        fd.setDirectory(get_music_dir())
        if fd.exec_():
            for fp in fd.selectedFiles():
                self.add_track(QUrl.fromLocalFile(fp))
            if not self.player.media().isNull(): return
            if self.playlist.count() > 0: self.play_at(0)

    def open_folder(self):
        folder = QFileDialog.getExistingDirectory(None, "Выберите папку с музыкой", get_music_dir())
        if not folder: return
        exts  = {'.mp3', '.wav', '.flac', '.ogg', '.m4a'}
        files = sorted(os.path.join(folder, f) for f in os.listdir(folder)
                       if os.path.splitext(f)[1].lower() in exts)
        if not files: return

        # Очищаем плейлист
        self.playlist.clear(); self.added_urls.clear()
        self.player.stop(); self.player.setMedia(QMediaContent())
        self.track_lbl.setText("Select a file to play")
        self.artist_lbl.setText(""); self.cover.set_cover(None)
        self.play_btn.setText("\ue037"); self.is_playing = False

        for fp in files: self.add_track(QUrl.fromLocalFile(fp))
        if self.playlist.count() > 0: self.play_at(0)

    # ── Сессия ─────────────────────────────────────────────────────────────

    def save_session(self):
        s = QSettings()
        cur = self.player.media().canonicalUrl()
        found = any(self.playlist.item(i).data(Qt.UserRole) == cur
                    for i in range(self.playlist.count())) if not cur.isEmpty() else False
        if found and cur.isLocalFile():
            s.setValue(self.LAST_TRACK_KEY, cur.toString())
        else:
            s.remove(self.LAST_TRACK_KEY)

        urls, seen = [], set()
        for i in range(self.playlist.count()):
            url = self.playlist.item(i).data(Qt.UserRole)
            if url and not url.isEmpty():
                st = url.toString()
                if st not in seen: urls.append(st); seen.add(st)
        s.setValue("playlist", urls)

        sp = self.playlist.parent()
        if isinstance(sp, QSplitter): s.setValue("playlist_width", sp.sizes()[1])

        self.added_urls.clear()
        for i in range(self.playlist.count()):
            url = self.playlist.item(i).data(Qt.UserRole)
            if url and not url.isEmpty(): self.added_urls.add(url.toString())

    def load_session(self):
        s = QSettings()
        for us in s.value("playlist", []):
            if isinstance(us, bytes):
                try: us = us.decode("utf-8")
                except: continue
            url = QUrl(us)
            if url.isLocalFile() and os.path.exists(url.toLocalFile()):
                self.add_track(url)
        self._dedup()

        path = s.value(self.LAST_TRACK_KEY, "")
        if isinstance(path, bytes):
            try: path = path.decode("utf-8")
            except: path = ""
        if path:
            url = QUrl(path)
            if url.isLocalFile() and os.path.exists(url.toLocalFile()):
                for i in range(self.playlist.count()):
                    if self.playlist.item(i).data(Qt.UserRole) == url:
                        self.player.setMedia(QMediaContent(url)); break

        width = s.value("playlist_width", 0)
        if isinstance(width, str): width = int(width) if width.isdigit() else 0
        elif isinstance(width, float): width = int(width)
        else: width = int(width) if width else 0

        sp = self.playlist.parent()
        if isinstance(sp, QSplitter):
            cur = sp.sizes(); total = cur[0] + cur[1]
            sp.setSizes([total - width, width] if width > 5 else [total, 0])

    # ── UI ─────────────────────────────────────────────────────────────────

    def update_window_style(self):
        r = "0px" if self.isMaximized() else "14px"
        self.centralWidget().setStyleSheet(
            f"background:qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #0a0a0a,stop:1 #050505);"
            f"border-radius:{r};")

    # ── События ────────────────────────────────────────────────────────────

    def closeEvent(self, e):
        self.save_session(); e.accept()

    def keyPressEvent(self, e):
        k = e.key(); m = e.modifiers()
        if   k == Qt.Key_Space: self.toggle_play()
        elif k == Qt.Key_Left:  self.play_prev()
        elif k == Qt.Key_Right: self.play_next()
        elif k == Qt.Key_Up:    self.vol_slider.setValue(min(100, self.vol_slider.value()+5))
        elif k == Qt.Key_Down:  self.vol_slider.setValue(max(0,   self.vol_slider.value()-5))
        elif k == Qt.Key_M:     self.toggle_mute()
        elif k == Qt.Key_P:     self.toggle_playlist()
        elif k == Qt.Key_S:     self.toggle_shuffle()
        elif k == Qt.Key_R:     self.toggle_repeat()
        elif k == Qt.Key_O and not m: self.open_files()
        else: super().keyPressEvent(e)