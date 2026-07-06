from __future__ import annotations

import logging

from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from podcast_downloader.core.models import AppSettings
from podcast_downloader.core.settings_manager import SettingsManager

logger = logging.getLogger(__name__)


class SettingsDialog(QDialog):
    """Dialog for editing application settings (download folder, etc.)."""

    def __init__(
        self,
        settings: AppSettings,
        settings_manager: SettingsManager,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("設定")
        self._settings = settings
        self._settings_manager = settings_manager
        self._build_ui()

    def accept(self) -> None:
        self._settings.download_dir = self._dir_input.text().strip()
        self._settings_manager.save(self._settings)
        logger.info("Settings saved: download_dir=%s", self._settings.download_dir)
        super().accept()

    def _on_browse_clicked(self) -> None:
        path = QFileDialog.getExistingDirectory(
            self,
            "ダウンロード先フォルダを選択",
            self._dir_input.text(),
        )
        if path:
            self._dir_input.setText(path)

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        form = QFormLayout()

        dir_row = QHBoxLayout()
        self._dir_input = QLineEdit(self._settings.download_dir)
        self._dir_input.setObjectName("settings-dialog-download-dir-input")
        self._dir_input.setReadOnly(True)
        self._dir_input.setMinimumWidth(300)

        browse_btn = QPushButton("参照...")
        browse_btn.setObjectName("settings-dialog-browse-button")
        browse_btn.clicked.connect(self._on_browse_clicked)

        dir_row.addWidget(self._dir_input, stretch=1)
        dir_row.addWidget(browse_btn)

        form.addRow("ダウンロード先:", dir_row)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.button(QDialogButtonBox.StandardButton.Ok).setObjectName("settings-dialog-ok-button")
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setObjectName("settings-dialog-cancel-button")
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout.addLayout(form)
        layout.addWidget(buttons)
