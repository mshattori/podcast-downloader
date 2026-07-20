from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from PySide6.QtCore import Qt, QMetaObject, Slot, Q_ARG
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from podcast_downloader.core.downloader import DownloadManager
from podcast_downloader.core.models import DownloadStatus, Episode

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class DownloadPanel(QWidget):
    """Panel that shows download progress and a cancel button."""

    def __init__(self, download_manager: DownloadManager, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._manager = download_manager
        self._total = 0
        self._completed = 0
        self._episode_update_callback: callable | None = None  # set by MainWindow

        self._build_ui()
        self.hide()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def set_episode_status_callback(self, callback: callable) -> None:
        """Register a callback(episode_id, DownloadStatus, local_path) for status changes."""
        self._episode_update_callback = callback

    def start_downloads(
        self,
        episodes: list[Episode],
        dest_dir: str,
    ) -> None:
        """Begin downloading *episodes* into *dest_dir*."""
        if not episodes:
            return

        self._total = len(episodes)
        self._completed = 0
        self._overall_bar.setRange(0, self._total)
        self._overall_bar.setValue(0)
        self._overall_label.setText(f"0 / {self._total} 件")
        self._current_bar.setRange(0, 100)
        self._current_bar.setValue(0)
        self._current_label.setText("")
        self.show()

        for episode in episodes:
            self._manager.enqueue(
                episode,
                dest_dir,
                on_progress=self._on_progress_thread,
                on_complete=self._on_complete_thread,
                on_error=self._on_error_thread,
            )

    # ------------------------------------------------------------------
    # Worker-thread callbacks (must not touch widgets directly)
    # ------------------------------------------------------------------

    def _on_progress_thread(self, episode: Episode, percent: float) -> None:
        QMetaObject.invokeMethod(
            self,
            "_update_progress",
            Qt.ConnectionType.QueuedConnection,
            Q_ARG(str, episode.id),
            Q_ARG(str, episode.title),
            Q_ARG(float, percent),
        )

    def _on_complete_thread(self, episode: Episode, path: str) -> None:
        QMetaObject.invokeMethod(
            self,
            "_handle_complete",
            Qt.ConnectionType.QueuedConnection,
            Q_ARG(str, episode.id),
            Q_ARG(str, path),
        )

    def _on_error_thread(self, episode: Episode, message: str) -> None:
        QMetaObject.invokeMethod(
            self,
            "_handle_error",
            Qt.ConnectionType.QueuedConnection,
            Q_ARG(str, episode.id),
            Q_ARG(str, message),
        )

    # ------------------------------------------------------------------
    # Main-thread slots
    # ------------------------------------------------------------------

    @Slot(str, str, float)
    def _update_progress(self, episode_id: str, title: str, percent: float) -> None:
        self._current_label.setText(title)
        if percent < 0:
            # Content-Length unknown → indeterminate mode (NFR Pattern 3)
            self._current_bar.setRange(0, 0)
        else:
            self._current_bar.setRange(0, 100)
            self._current_bar.setValue(int(percent))

    @Slot(str, str)
    def _handle_complete(self, episode_id: str, path: str) -> None:
        self._completed += 1
        self._overall_bar.setValue(self._completed)
        self._overall_label.setText(f"{self._completed} / {self._total} 件")
        if self._episode_update_callback:
            self._episode_update_callback(episode_id, DownloadStatus.DOWNLOADED, path)
        if self._completed >= self._total:
            self.hide()

    @Slot(str, str)
    def _handle_error(self, episode_id: str, message: str) -> None:
        self._completed += 1
        self._overall_bar.setValue(self._completed)
        self._overall_label.setText(f"{self._completed} / {self._total} 件")
        if self._episode_update_callback:
            self._episode_update_callback(episode_id, DownloadStatus.ERROR, None)
        QMessageBox.critical(self, "ダウンロードエラー", message)
        if self._completed >= self._total:
            self.hide()

    def _on_cancel_clicked(self) -> None:
        self._manager.cancel_all()
        self.hide()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)

        # Overall progress row
        overall_row = QHBoxLayout()
        self._overall_label = QLabel("0 / 0 件")
        self._overall_bar = QProgressBar()
        self._overall_bar.setObjectName("download-panel-overall-progress")
        self._overall_label.setObjectName("download-panel-overall-label")
        overall_row.addWidget(self._overall_label)
        overall_row.addWidget(self._overall_bar, stretch=1)

        # Current file progress row
        current_row = QHBoxLayout()
        self._current_label = QLabel("")
        self._current_label.setObjectName("download-panel-current-label")
        self._current_bar = QProgressBar()
        self._current_bar.setObjectName("download-panel-current-progress")
        current_row.addWidget(self._current_label, stretch=1)
        current_row.addWidget(self._current_bar)

        # Cancel button
        self._cancel_btn = QPushButton("キャンセル")
        self._cancel_btn.setObjectName("download-panel-cancel-button")
        self._cancel_btn.clicked.connect(self._on_cancel_clicked)

        layout.addLayout(overall_row)
        layout.addLayout(current_row)
        layout.addWidget(self._cancel_btn, alignment=Qt.AlignmentFlag.AlignRight)
