# Logical Components — Unit 2: gui

## Component Map and NFR Coverage

| Component | NFR addressed | Key pattern |
|---|---|---|
| `main_window.py` | Startup perf, geometry guard | Pattern 4 (geometry), Pattern 5 (lazy load) |
| `feed_panel.py` | UI responsiveness | Pattern 2 (QThread worker) |
| `episode_list.py` | Usability, accessibility | data-testid, checkbox sync |
| `download_panel.py` | Thread safety, indeterminate progress | Pattern 1 (invokeMethod), Pattern 3 |
| `settings_dialog.py` | Usability | QFileDialog, validation |

---

## FetchWorker lifecycle (FeedPanel)

```
FeedPanel
├── _workers: dict[str, FetchWorker]   # feed_id → active worker
│
├── _refresh_feed(feed)
│     ├── Guard: if feed.id in _workers → already running, skip
│     ├── Create FetchWorker(feed.url)
│     ├── Connect signals
│     └── worker.start()
│
├── _on_fetch_done(episodes, feed_id)   ← main thread (Qt signal)
│     ├── merge_episodes(cached, fetched)
│     ├── save_episode_cache()
│     ├── Update feed.last_fetched
│     ├── save settings
│     ├── Emit feed_selected if this feed is currently selected
│     └── _workers.pop(feed_id)
│
└── _on_fetch_error(message, feed_id)  ← main thread (Qt signal)
      ├── QMessageBox.critical(...)
      └── _workers.pop(feed_id)
```

---

## DownloadPanel internal state

```
DownloadPanel
├── _total: int              # episodes in current batch
├── _completed: int          # done (success + error)
├── _episode_bars: dict[str, QProgressBar]   # episode_id → bar widget
│
├── start_downloads(episodes, dest_dir)
│     ├── Reset state, show panel
│     └── For each episode: DownloadManager.enqueue(...)
│
├── _update_progress(episode_id, percent)    # @Slot, main thread
│     └── Update per-episode bar (indeterminate if percent < 0)
│
├── _handle_complete(episode_id, path)       # @Slot, main thread
│     ├── _completed += 1
│     ├── Update overall bar
│     ├── Signal EpisodeList to update status icon
│     └── If _completed == _total: hide panel
│
└── _handle_error(episode_id, message)       # @Slot, main thread
      ├── _completed += 1
      ├── QMessageBox.critical(...)
      └── If _completed == _total: hide panel
```

---

## Startup sequence (MainWindow)

```
1. SettingsManager.load()               → AppSettings
2. DownloadManager()
3. Build layout: FeedPanel + EpisodeList + DownloadPanel
4. Connect cross-panel signals
5. Restore window geometry (Pattern 4)
6. FeedPanel.load_feeds(settings.feeds) → populate list widget
7. For each feed: FeedPanel._refresh_feed(feed)  [background, Pattern 2]
8. window.show()
9. app.exec()
```

---

## Error types and GUI handling

| Source | Exception | GUI action |
|---|---|---|
| RSS fetch | `RSSFetchError` | `QMessageBox.critical` via `_on_fetch_error` slot |
| RSS parse | `RSSParseError` | Same as above |
| Download | Caught in `DownloadManager._download` | `on_error` callback → `_handle_error` slot → `QMessageBox.critical` |
| Settings save | `SettingsError` | `QMessageBox.critical` inline in the calling method |
| Feed add validation | URL format error | Inline label in `AddFeedDialog` (no dialog close) |
