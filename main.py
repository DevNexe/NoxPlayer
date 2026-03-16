import sys
import os
import platform

# WMF — нативная поддержка MP3/AAC на Windows без кодеков
if platform.system() == "Windows":
    os.environ["QT_MULTIMEDIA_PREFERRED_PLUGINS"] = "windowsmediafoundation"

from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QFontDatabase, QIcon

from utils import resource_path
from player import NoxPlayer


def main():
    if platform.system() == "Windows":
        try:
            import ctypes
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
                'devnexe.noxplayer.v1')
        except Exception:
            pass

    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(resource_path("icon.ico")))

    fp = resource_path("MaterialSymbolsRounded.ttf")
    if os.path.exists(fp):
        QFontDatabase.addApplicationFont(fp)

    window = NoxPlayer()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
