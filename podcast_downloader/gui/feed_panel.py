from __future__ import annotations

import logging
from urllib.parse import urlparse

from PySide6.QtCore import Qt, QThread, Signal, Slot
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from podcast_downloader.core import rss_parser
from podcast_downloader.core.models import AppSettings, Episode, Feed
from podcast_downloader.core.settings_manager import SettingsManager

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Background worker for RSS fetch (NFR Pattern 2)
# ---------------------------------------------------------------------------

class _FetchWorker(QThread):
    finished = Signal(list, str)   # list[Episode], feed_id
    error = Signal(str, str)       # message, feed_id

    def __init__(self, feed: Feed, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._feed = feed

    def run(self) -> None:
        try:
            episodes = rss_parser.fetch_and_parse(self._feed.url)
            for ep in episodes:
                ep.feed_id = self._feed.id
            self.finished.emit(episodes, self._feed.id)
        except Exception as e:
            logger.error("RSS fetch failed for %s: %s", self._feed.url, e)
            self.error.emit(str(e), self._feed.id)


# ---------------------------------------------------------------------------
# Add Feed Dialog
# ---------------------------------------------------------------------------

class AddFeedDialog(QDialog):
    """Dialog for entering a new RSS feed URL and optional label."""

    def __init__(self, existing_urls: set[str], parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("フィードを追加")
        self._existing_urls = existing_urls
        self._build_ui()

    def get_url(self) -> str:
        return self._url_input.text().strip()

    def get_label(self) -> str:
        label = self._label_input.text().strip()
        if not label:
            # Default to hostname (BR-GUI-01-3)
            parsed = urlparse(self.get_url())
            label = parsed.netloc or self.get_url()
        return label

    def accept(self) -> None:
        url = self.get_url()
        self._error_label.setText("")

        if not url.startswith(("http://", "https://")):
            self._error_label.setText("URLは http:// または https:// で始まる必要があります")
            return
        if url in self._existing_urls:
            self._error_label.setText("このURLはすでに登録されています")
            return

        super().accept()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        form = QFormLayout()

        self._url_input = QLineEdit()
        self._url_input.setObjectName("add-feed-dialog-url-input")
        self._url_input.setPlaceholderText("https://example.com/feed.rss")

        self._label_input = QLineEdit()
        self._label_input.setObjectName("add-feed-dialog-label-input")
        self._label_input.setPlaceholderText("任意のフィード名")

        form.addRow("RSS URL:", self._url_input)
        form.addRow("ラベル (任意):", self._label_input)

        self._error_label = QLabel()
        self._error_label.setStyleSheet("color: red;")

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.button(QDialogButtonBox.StandardButton.Ok).setObjectName("add-feed-dialog-ok-button")
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setObjectName("add-feed-dialog-cancel-button")
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout.addLayout(form)
        layout.addWidget(self._error_label)
        layout.addWidget(buttons)


# ---------------------------------------------------------------------------
# FeedPanel
# ---------------------------------------------------------------------------

class FeedPanel(QWidget):
    """Left panel showing the registered feed list with add/remove/refresh."""

    feed_selected = Signal(object)  # Feed

    def __init__(
        self,
        settings: AppSettings,
        settings_manager: SettingsManager,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._settings = settings
        self._settings_manager = settings_manager
        self._workers: dict[str, _FetchWorker] = {}
        self._current_feed: Feed | None = None

        self.setMinimumWidth(180)
        self._build_ui()
        self.load_feeds()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def load_feeds(self) -> None:
        """Populate the list widget from settings."""
        self._list.clear()
        for feed in self._settings.feeds:
            item = QListWidgetItem(feed.label)
            item.setData(Qt.ItemDataRole.UserRole, feed)
            self._list.addItem(item)

    def refresh_all_feeds(self) -> None:
        """Start background refresh for every registered feed."""
        for feed in self._settings.feeds:
            self._start_fetch(feed)

    # ------------------------------------------------------------------
    # Slots
    # ------------------------------------------------------------------

    def _on_feed_clicked(self, item: QListWidgetItem) -> None:
        feed: Feed = item.data(Qt.ItemDataRole.UserRole)
        self._current_feed = feed
        self.feed_selected.emit(feed)

    def _on_add_clicked(self) -> None:
        existing = {f.url for f in self._settings.feeds}
        dlg = AddFeedDialog(existing, parent=self)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return

        feed = Feed(url=dlg.get_url(), label=dlg.get_label())
        self._settings.feeds.append(feed)
        self._settings_manager.save(self._settings)
        self.load_feeds()
        self._start_fetch(feed)

    def _on_remove_clicked(self) -> None:
        item = self._list.currentItem()
        if not item:
            return
        feed: Feed = item.data(Qt.ItemDataRole.UserRole)
        reply = QMessageBox.question(
            self,
            "フィードを削除",
            f'「{feed.label}」を削除しますか？',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        self._settings.feeds = [f for f in self._settings.feeds if f.id != feed.id]
        self._settings_manager.save(self._settings)
        # Remove episode cache
        cache_path = self._settings_manager._cache_dir / f"{feed.id}.json"
        if cache_path.exists():
            cache_path.unlink(missing_ok=True)

        if self._current_feed and self._current_feed.id == feed.id:
            self._current_feed = None
            self.feed_selected.emit(None)

        self.load_feeds()

    def _on_refresh_clicked(self) -> None:
        item = self._list.currentItem()
        if not item:
            return
        feed: Feed = item.data(Qt.ItemDataRole.UserRole)
        self._start_fetch(feed)

    # ------------------------------------------------------------------
    # Fetch worker management
    # ------------------------------------------------------------------

    def _start_fetch(self, feed: Feed) -> None:
        if feed.id in self._workers:
            return  # already running
        worker = _FetchWorker(feed, parent=self)
        worker.finished.connect(self._on_fetch_done)
        worker.error.connect(self._on_fetch_error)
        self._workers[feed.id] = worker
        worker.start()
        logger.info("Started RSS fetch for feed %s", feed.id)

    @Slot(list, str)
    def _on_fetch_done(self, fetched: list[Episode], feed_id: str) -> None:
        self._workers.pop(feed_id, None)
        cached = self._settings_manager.load_episode_cache(feed_id)
        merged = rss_parser.merge_episodes(cached, fetched)
        self._settings_manager.save_episode_cache(feed_id, merged)

        # Update last_fetched timestamp
        from datetime import datetime, timezone
        for feed in self._settings.feeds:
            if feed.id == feed_id:
                feed.last_fetched = datetime.now(timezone.utc)
                break
        self._settings_manager.save(self._settings)

        # Refresh episode list if this feed is currently selected
        if self._current_feed and self._current_feed.id == feed_id:
            self.feed_selected.emit(self._current_feed)

    @Slot(str, str)
    def _on_fetch_error(self, message: str, feed_id: str) -> None:
        self._workers.pop(feed_id, None)
        QMessageBox.critical(self, "RSSフィードの取得に失敗しました", message)

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)

        self._list = QListWidget()
        self._list.setObjectName("feed-panel-list")
        self._list.itemClicked.connect(self._on_feed_clicked)

        btn_row = QHBoxLayout()
        add_btn = QPushButton("追加")
        add_btn.setObjectName("feed-panel-add-button")
        add_btn.clicked.connect(self._on_add_clicked)

        remove_btn = QPushButton("削除")
        remove_btn.setObjectName("feed-panel-remove-button")
        remove_btn.clicked.connect(self._on_remove_clicked)

        refresh_btn = QPushButton("更新")
        refresh_btn.setObjectName("feed-panel-refresh-button")
        refresh_btn.clicked.connect(self._on_refresh_clicked)

        btn_row.addWidget(add_btn)
        btn_row.addWidget(remove_btn)
        btn_row.addWidget(refresh_btn)

        layout.addWidget(self._list)
        layout.addLayout(btn_row)
