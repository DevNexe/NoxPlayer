import sys
import os
import platform


def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


def get_music_dir():
    if platform.system() == "Windows":
        try:
            import winreg
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders")
            music_dir, _ = winreg.QueryValueEx(key, "My Music")
            winreg.CloseKey(key)
            if music_dir and os.path.exists(music_dir):
                return music_dir
        except Exception:
            pass
    try:
        from PyQt5.QtCore import QStandardPaths
        d = QStandardPaths.writableLocation(QStandardPaths.MusicLocation)
        if d and os.path.exists(d):
            return d
    except Exception:
        pass
    return os.path.expanduser("~")


def get_artist_string(player):
    """Возвращает строку артиста из QMediaPlayer (PyQt5)."""
    for key in ("ContributingArtist", "AlbumArtist", "Author"):
        val = player.metaData(key)
        if val:
            if isinstance(val, list):
                return ", ".join(str(a) for a in val if a)
            return str(val)
    return ""
