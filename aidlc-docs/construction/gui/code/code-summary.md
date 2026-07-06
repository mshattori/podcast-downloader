# Code Generation Summary — Unit 2: gui

## Generated Files

### Application Code

| File | Description |
|---|---|
| `main.py` | Entry point: QApplication, logging setup, MainWindow launch |
| `podcast_downloader/gui/main_window.py` | Root window, splitter layout, menu bar, cross-panel signal wiring |
| `podcast_downloader/gui/feed_panel.py` | Feed list, AddFeedDialog, FetchWorker (QThread), refresh logic |
| `podcast_downloader/gui/episode_list.py` | Episode table, checkbox/selection sync, description pane |
| `podcast_downloader/gui/download_panel.py` | Progress bars, thread-safe updates via invokeMethod, cancel |
| `podcast_downloader/gui/settings_dialog.py` | Download folder selection dialog |

### No GUI Tests in This Phase
GUI tests require a running QApplication and are deferred to the Build & Test phase (manual / integration testing).

## NFR Implementation Summary

| NFR Pattern | Implementation |
|---|---|
| Thread-safe GUI updates (Pattern 1) | `QMetaObject.invokeMethod(..., QueuedConnection)` in `DownloadPanel` |
| QThread RSS fetch (Pattern 2) | `_FetchWorker(QThread)` in `FeedPanel` |
| Indeterminate progress (Pattern 3) | `setRange(0, 0)` when `percent < 0` in `DownloadPanel` |
| Geometry guard (Pattern 4) | `_restore_geometry()` in `MainWindow` |
| Cache-first load (Pattern 5) | `load_episode_cache()` on feed selection; background fetch updates after |

## Business Rules Coverage

| Rule | Where |
|---|---|
| BR-GUI-01: Feed add validation | `AddFeedDialog.accept()` |
| BR-GUI-02: Feed delete confirmation | `FeedPanel._on_remove_clicked()` |
| BR-GUI-03: Checkbox/selection sync | `EpisodeList._on_item_changed()` / `_on_selection_changed()` |
| BR-GUI-04: Error dialogs | `QMessageBox.critical` in `FeedPanel`, `DownloadPanel` |
| BR-GUI-05: Window geometry persistence | `MainWindow.closeEvent()` / `_restore_geometry()` |
| BR-GUI-06: Download panel visibility | `DownloadPanel.start_downloads()` / `_handle_complete/error()` |
