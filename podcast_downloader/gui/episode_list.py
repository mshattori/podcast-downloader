from __future__ import annotations

import logging

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QSizePolicy,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from podcast_downloader.core.models import DownloadStatus, Episode

logger = logging.getLogger(__name__)

# Column indices
_COL_CHECK = 0
_COL_TITLE = 1
_COL_DATE = 2
_COL_DURATION = 3
_COL_STATUS = 4

_STATUS_LABELS = {
    DownloadStatus.NOT_DOWNLOADED: "未ダウンロード",
    DownloadStatus.DOWNLOADING: "ダウンロード中",
    DownloadStatus.DOWNLOADED: "済",
    DownloadStatus.ERROR: "エラー",
}


class EpisodeList(QWidget):
    """Widget showing the episode table and a description pane below it."""

    download_requested = Signal(list)  # list[Episode]

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._episodes: list[Episode] = []
        self._build_ui()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def set_episodes(self, episodes: list[Episode]) -> None:
        """Populate the table with *episodes*, preserving sort order."""
        self._episodes = episodes
        self._table.setRowCount(0)
        self._description.clear()

        for row, ep in enumerate(episodes):
            self._table.insertRow(row)
            self._set_row(row, ep)

        self._sync_download_button()

    def episodes(self) -> list[Episode]:
        """Return the currently displayed episodes."""
        return self._episodes

    def update_episode_status(
        self,
        episode_id: str,
        status: DownloadStatus,
        local_path: str | None = None,
    ) -> None:
        """Update the status column of the episode matching *episode_id*."""
        for row, ep in enumerate(self._episodes):
            if ep.id == episode_id:
                ep.status = status
                if local_path is not None:
                    ep.local_path = local_path
                item = self._table.item(row, _COL_STATUS)
                if item:
                    item.setText(_STATUS_LABELS[status])
                return

    def get_checked_episodes(self) -> list[Episode]:
        """Return episodes whose checkbox is checked."""
        result = []
        for row in range(self._table.rowCount()):
            chk = self._table.item(row, _COL_CHECK)
            if chk and chk.checkState() == Qt.CheckState.Checked:
                result.append(self._episodes[row])
        return result

    # ------------------------------------------------------------------
    # Slots / event handlers
    # ------------------------------------------------------------------

    def _on_item_changed(self, item: QTableWidgetItem) -> None:
        """Sync row selection when a checkbox is toggled."""
        if item.column() != _COL_CHECK:
            return
        self._table.blockSignals(True)
        checked = item.checkState() == Qt.CheckState.Checked
        self._table.selectRow(item.row()) if checked else None
        self._table.blockSignals(False)
        self._sync_download_button()

    def _on_selection_changed(self) -> None:
        """Sync checkboxes with the current row selection and update description."""
        selected_rows = {idx.row() for idx in self._table.selectedIndexes()}

        self._table.blockSignals(True)
        for row in range(self._table.rowCount()):
            chk = self._table.item(row, _COL_CHECK)
            if chk:
                state = Qt.CheckState.Checked if row in selected_rows else Qt.CheckState.Unchecked
                chk.setCheckState(state)
        self._table.blockSignals(False)

        # Update description pane
        if len(selected_rows) == 1:
            row = next(iter(selected_rows))
            if row < len(self._episodes):
                self._description.setPlainText(self._episodes[row].description)
        else:
            self._description.clear()

        self._sync_download_button()

    def _on_select_all(self) -> None:
        self._table.blockSignals(True)
        for row in range(self._table.rowCount()):
            chk = self._table.item(row, _COL_CHECK)
            if chk:
                chk.setCheckState(Qt.CheckState.Checked)
        self._table.selectAll()
        self._table.blockSignals(False)
        self._sync_download_button()

    def _on_deselect_all(self) -> None:
        self._table.blockSignals(True)
        for row in range(self._table.rowCount()):
            chk = self._table.item(row, _COL_CHECK)
            if chk:
                chk.setCheckState(Qt.CheckState.Unchecked)
        self._table.clearSelection()
        self._table.blockSignals(False)
        self._description.clear()
        self._sync_download_button()

    def _on_download_clicked(self) -> None:
        episodes = self.get_checked_episodes()
        if episodes:
            self.download_requested.emit(episodes)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _set_row(self, row: int, ep: Episode) -> None:
        # Checkbox column
        chk_item = QTableWidgetItem()
        chk_item.setFlags(Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled)
        chk_item.setCheckState(Qt.CheckState.Unchecked)
        self._table.setItem(row, _COL_CHECK, chk_item)

        # Title
        title_item = QTableWidgetItem(ep.title)
        title_item.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)
        self._table.setItem(row, _COL_TITLE, title_item)

        # Published date
        date_str = ep.published.strftime("%Y-%m-%d %H:%M") if ep.published else "日時不明"
        date_item = QTableWidgetItem(date_str)
        date_item.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)
        self._table.setItem(row, _COL_DATE, date_item)

        # Duration
        dur_item = QTableWidgetItem(ep.duration_display)
        dur_item.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)
        self._table.setItem(row, _COL_DURATION, dur_item)

        # Status
        status_item = QTableWidgetItem(_STATUS_LABELS[ep.status])
        status_item.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)
        self._table.setItem(row, _COL_STATUS, status_item)

    def _sync_download_button(self) -> None:
        self._download_btn.setEnabled(bool(self.get_checked_episodes()))

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Toolbar
        toolbar = QHBoxLayout()
        self._download_btn = QPushButton("ダウンロード")
        self._download_btn.setObjectName("episode-list-download-button")
        self._download_btn.setEnabled(False)
        self._download_btn.clicked.connect(self._on_download_clicked)

        select_all_btn = QPushButton("全選択")
        select_all_btn.setObjectName("episode-list-select-all-button")
        select_all_btn.clicked.connect(self._on_select_all)

        deselect_btn = QPushButton("選択解除")
        deselect_btn.setObjectName("episode-list-deselect-button")
        deselect_btn.clicked.connect(self._on_deselect_all)

        toolbar.addWidget(self._download_btn)
        toolbar.addWidget(select_all_btn)
        toolbar.addWidget(deselect_btn)
        toolbar.addStretch()

        # Episode table
        self._table = QTableWidget(0, 5)
        self._table.setObjectName("episode-list-table")
        self._table.setHorizontalHeaderLabels(["", "タイトル", "公開日", "長さ", "状態"])
        self._table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self._table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self._table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        self._table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        self._table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        self._table.setColumnWidth(0, 30)
        self._table.setColumnWidth(2, 130)
        self._table.setColumnWidth(3, 100)
        self._table.setColumnWidth(4, 110)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.setSelectionMode(QTableWidget.SelectionMode.ExtendedSelection)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.verticalHeader().setVisible(False)
        self._table.itemChanged.connect(self._on_item_changed)
        self._table.itemSelectionChanged.connect(self._on_selection_changed)

        # Description pane
        self._description = QTextEdit()
        self._description.setObjectName("episode-list-description-pane")
        self._description.setReadOnly(True)
        self._description.setPlaceholderText("エピソードを選択すると概要が表示されます")
        self._description.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self._description.setMaximumHeight(120)

        # Vertical splitter: table on top, description below
        splitter = QSplitter(Qt.Orientation.Vertical)
        splitter.addWidget(self._table)
        splitter.addWidget(self._description)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 1)

        layout.addLayout(toolbar)
        layout.addWidget(splitter)
