import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from podcast_downloader.gui.main_window import MainWindow
from podcast_downloader.core.downloader import DownloadManager
from podcast_downloader.core.settings_manager import SettingsManager


def main() -> None:
    from PySide6.QtWidgets import QApplication
    import logging
    from logging.handlers import RotatingFileHandler

    app = QApplication(sys.argv)
    app.setApplicationName("Podcast Downloader")
    app.setOrganizationName("podcast-downloader")

    settings_manager = SettingsManager()

    log_path = settings_manager.log_path()
    log_path.parent.mkdir(parents=True, exist_ok=True)
    level = logging.DEBUG if os.getenv("PODCAST_DL_DEBUG") else logging.INFO
    fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    handler = RotatingFileHandler(log_path, maxBytes=5 * 1024 * 1024, backupCount=3)
    handler.setFormatter(fmt)
    root = logging.getLogger()
    root.setLevel(level)
    root.addHandler(handler)
    stderr_handler = logging.StreamHandler()
    stderr_handler.setLevel(logging.INFO)
    stderr_handler.setFormatter(fmt)
    root.addHandler(stderr_handler)

    settings = settings_manager.load()
    download_manager = DownloadManager()

    window = MainWindow(settings, settings_manager, download_manager)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
