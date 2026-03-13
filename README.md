<div align="center">

<br/>

*NoxPlayer*

**A sleek, frameless music player built with Python & PySide6**

<br/>

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![PySide6](https://img.shields.io/badge/PySide6-6.x-41CD52?style=flat-square&logo=qt&logoColor=white)](https://doc.qt.io/qtforpython/)
[![Platform](https://img.shields.io/badge/Platform-Windows-0078D4?style=flat-square&logo=windows&logoColor=white)](https://github.com/DevNexe)
[![License](https://img.shields.io/badge/License-MIT-f0a500?style=flat-square)](LICENSE)
[![GitHub](https://img.shields.io/badge/GitHub-DevNexe-181717?style=flat-square&logo=github)](https://github.com/DevNexe)

</div>

---

## ✦ Overview

**NoxPlayer** is a modern, frameless desktop music player crafted in Python. It features a dark, minimal aesthetic with blurred album art backgrounds, smooth animations, and an intuitive playlist system — all without a single native window chrome element in sight.

Built as part of the [Nox ecosystem](https://github.com/DevNexe/nox) by **DevNexe**.

---

## ✦ Features

| | Feature | Description |
|---|---|---|
| 🎨 | **Blurred Album Art** | Dynamic background blur derived from the current track's cover art |
| 📋 | **Playlist Management** | Add, remove, and reorder tracks with a slide-in playlist panel |
| 🔀 | **Shuffle & Repeat** | Three repeat modes (off / all / one) + shuffle, mutually exclusive with repeat-one |
| 🎵 | **Marquee Track Title** | Long titles scroll back and forth with smooth easing animations |
| 💾 | **Session Persistence** | Last track, full playlist, and player state are restored on relaunch |
| ⌨️ | **Keyboard Shortcuts** | Full keyboard control — play, skip, volume, mute, shuffle, and more |
| 🖼️ | **Frameless Window** | Custom title bar with drag, minimize, maximize, and snap support |
| 📁 | **Drag & Replace** | Open new files and instantly replace the current playlist |
| 🔊 | **Volume Control** | Inline volume slider with mute toggle and smart unmute |
| 🖋️ | **Outlined Text** | GPU-rendered text with configurable outline + blur shadow |

---

## ✦ Keyboard Shortcuts

| Key | Action |
|---|---|
| `Space` | Play / Pause |
| `←` / `→` | Previous / Next track |
| `↑` / `↓` | Volume up / down |
| `M` | Toggle mute |
| `S` | Toggle shuffle |
| `R` | Cycle repeat mode |
| `P` | Toggle playlist panel |
| `O` | Open file dialog |

---

## ✦ Installation

### Requirements

- Python **3.10+**
- PySide6
- A `MaterialSymbolsRounded.ttf` font file in the project root
- An `icon.ico` file in the project root

### Setup

```bash
# Clone the repository
git clone https://github.com/DevNexe/NoxPlayer.git
cd NoxPlayer

# Install dependencies
pip install PySide6

# Run the player
python main.py
```

---

## ✦ Build (Standalone Executable)

Uses **PyInstaller** with the included spec file:

```bash
pip install pyinstaller
pyinstaller main.spec
```

The compiled binary will be in `dist/main.exe`. The spec is pre-configured to bundle the font and icon, and to suppress the console window.

---

## ✦ Supported Formats

```
MP3  ·  WAV  ·  FLAC  ·  OGG  ·  M4A
```

---

## ✦ Project Structure

```
NoxPlayer/
├── main.py                    # Application entry point & all UI logic
├── main.spec                  # PyInstaller build spec
├── icon.ico                   # Application icon
└── MaterialSymbolsRounded.ttf # Icon font (Material Symbols)
```

---

## ✦ Architecture

NoxPlayer is organized around a handful of key classes:

```
NoxPlayer (QMainWindow)
├── TitleBar           — Custom frameless title bar with drag & window controls
├── AlbumCover         — Blurred background + centered artwork renderer
├── PlaylistItemWidget — Per-track row with lazy metadata loading
├── MarqueeLabel       — QPropertyAnimation-powered scrolling label
└── OutlineLabel       — QPainterPath text with outline & blur shadow
```

Metadata (title, artist, cover art) is loaded **asynchronously** via temporary `QMediaPlayer` instances, keeping the UI non-blocking even for large playlists.

---

## ✦ Author

<div align="center">

Made with obsessive attention to detail by **[DevNexe](https://github.com/DevNexe)**

*Also check out [Nox](https://github.com/DevNexe/nox) — a custom scripting language written in pure Python.*

<br/>

</div>

---

<div align="center">
<sub>© DevNexe · Built with Python & PySide6</sub>
</div>
