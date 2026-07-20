from __future__ import annotations

import logging

from PySide6.QtCore import QRect
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from podcast_downloader.core.downloader import DownloadManager
from podcast_downloader.core.models import AppSettings, DownloadStatus, Feed
from podcast_downloader.core.settings_manager import SettingsManager

from .download_panel import DownloadPanel
from .episode_list import EpisodeList
from .feed_panel import FeedPanel
from .settings_dialog import SettingsDialog

logger = logging.getLogger(__name__)

_DEFAULT_WIDTH = 1024
_DEFAULT_HEIGHT = 768


class MainWindow(QMainWindow):
    """Root application window with feed panel, episode list, and download panel."""

    def __init__(
        self,
        settings: AppSettings,
        settings_manager: SettingsManager,
        download_manager: DownloadManager,
    ) -> None:
        super().__init__()
        self._settings = settings
        self._settings_manager = settings_manager
        self._download_manager = download_manager

        self.setWindowTitle("Podcast Downloader")
        self._build_ui()
        self._connect_signals()
        self._restore_geometry()

        # Trigger background RSS refresh for all feeds at startup (NFR Pattern 5)
        self._feed_panel.refresh_all_feeds()

    # ------------------------------------------------------------------
    # Qt event overrides
    # ------------------------------------------------------------------

    def closeEvent(self, event) -> None:  # noqa: N802
        """Save window geometry and settings before closing."""
        rect = self.geometry()
        self._settings.window_geometry = {
            "x": rect.x(),
            "y": rect.y(),
            "width": rect.width(),
            "height": rect.height(),
        }
        self._settings_manager.save(self._settings)
        logger.info("Window closed; settings saved")
        super().closeEvent(event)

    # ------------------------------------------------------------------
    # Internal slots
    # ------------------------------------------------------------------

    def _on_feed_selected(self, feed: Feed | None) -> None:
        if feed is None:
            self._episode_list.set_episodes([])
            return
        episodes = self._settings_manager.load_episode_cache(feed.id)
        self._episode_list.set_episodes(episodes)

    def _on_download_requested(self, episodes: list) -> None:
        current_feed = self._feed_panel.current_feed()
        if current_feed:
            for episode in episodes:
                if not episode.podcast_title:
                    episode.podcast_title = current_feed.label
        self._download_panel.start_downloads(episodes, self._settings.download_dir)

    def _on_episode_status_changed(
        self,
        episode_id: str,
        status: DownloadStatus,
        local_path: str | None = None,
    ) -> None:
        self._episode_list.update_episode_status(episode_id, status, local_path)
        current_feed = self._feed_panel.current_feed()
        if current_feed:
            self._settings_manager.save_episode_cache(
                current_feed.id,
                self._episode_list.episodes(),
            )

    def _open_settings(self) -> None:
        dlg = SettingsDialog(self._settings, self._settings_manager, parent=self)
        dlg.exec()

    # ------------------------------------------------------------------
    # Geometry helpers
    # ------------------------------------------------------------------

    def _restore_geometry(self) -> None:
        """Restore window position/size, clamping to visible screen area (NFR Pattern 4)."""
        geom = self._settings.window_geometry
        if geom:
            rect = QRect(geom["x"], geom["y"], geom["width"], geom["height"])
            screen = QApplication.primaryScreen().availableGeometry()
            visible = rect.intersected(screen)
            if visible.width() > 100 and visible.height() > 100:
                self.setGeometry(rect)
                return
        self.resize(_DEFAULT_WIDTH, _DEFAULT_HEIGHT)

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        # Menu bar
        menu_bar = self.menuBar()

        file_menu = menu_bar.addMenu("ファイル")
        quit_action = QAction("終了", self)
        quit_action.triggered.connect(self.close)
        file_menu.addAction(quit_action)

        settings_menu = menu_bar.addMenu("設定")
        settings_action = QAction("設定...", self)
        settings_action.triggered.connect(self._open_settings)
        settings_menu.addAction(settings_action)

        # Panels
        self._feed_panel = FeedPanel(self._settings, self._settings_manager, parent=self)
        self._episode_list = EpisodeList(parent=self)
        self._download_panel = DownloadPanel(self._download_manager, parent=self)
        self._download_panel.set_episode_status_callback(self._on_episode_status_changed)

        # Right pane: episode list + download panel
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.addWidget(self._episode_list, stretch=1)
        right_layout.addWidget(self._download_panel)

        # Horizontal splitter: feed panel | right pane
        splitter = QSplitter()
        splitter.addWidget(self._feed_panel)
        splitter.addWidget(right_widget)
        splitter.setSizes([220, _DEFAULT_WIDTH - 220])

        self.setCentralWidget(splitter)

    def _connect_signals(self) -> None:
        self._feed_panel.feed_selected.connect(self._on_feed_selected)
        self._episode_list.download_requested.connect(self._on_download_requested)
