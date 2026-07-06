# Business Logic Model — Unit 2: gui

## 1. Application Startup Flow

```
main.py: main()
│
├── Setup logging (RotatingFileHandler via SettingsManager.log_path())
├── QApplication(sys.argv)
├── QTranslator → load locale (QLocale.system())
│
├── SettingsManager.load() → AppSettings
├── DownloadManager()
├── MainWindow(settings, settings_manager, download_manager)
│   ├── Restore window geometry
│   ├── FeedPanel.load_feeds(settings.feeds)
│   └── Trigger background RSS fetch for all feeds (QThread × N feeds)
│
└── sys.exit(app.exec())
```

---

## 2. Feed Selection → Episode List Load Flow

```
User clicks feed in FeedPanel
    │
    v
FeedPanel.feed_selected Signal(Feed)
    │
    v
EpisodeList.load_feed(feed: Feed)
    ├── Load cached episodes: SettingsManager.load_episode_cache(feed.id)
    ├── Populate table immediately from cache
    └── (Background refresh already triggered at startup or by refresh button)
```

---

## 3. Feed Refresh Flow

```
User clicks [↺ 更新] in FeedPanel (or triggered at startup)
    │
    v
FeedPanel._refresh_feed(feed: Feed)
    ├── Show spinner on feed list item
    └── QThread:
          rss_parser.fetch_and_parse(feed.url)
          │
          ├── Success:
          │     cached = SettingsManager.load_episode_cache(feed.id)
          │     merged = merge_episodes(cached, fetched)
          │     # Set feed_id on new episodes
          │     SettingsManager.save_episode_cache(feed.id, merged)
          │     feed.last_fetched = datetime.now(UTC)
          │     SettingsManager.save(settings)
          │     Signal → EpisodeList.set_episodes(merged)
          │
          └── Error:
                Signal → MainWindow._show_error(title, message)
                         → QMessageBox.critical(...)
```

---

## 4. Download Flow

```
User checks episodes → clicks [ダウンロード]
    │
    v
EpisodeList.download_requested Signal(list[Episode])
    │
    v
DownloadPanel.start_downloads(episodes, dest_dir)
    ├── Show DownloadPanel
    ├── _total = len(episodes), _completed = 0
    └── For each episode:
          DownloadManager.enqueue(episode, dest_dir,
              on_progress=_on_progress,
              on_complete=_on_complete,
              on_error=_on_error)

_on_progress(episode, percent)  ← worker thread
    └── QMetaObject.invokeMethod(self, "_update_progress", QueuedConnection,
            episode_id, percent)
        → Update per-file progress bar

_on_complete(episode, path)  ← worker thread
    └── QMetaObject.invokeMethod(self, "_handle_complete", QueuedConnection,
            episode_id, path)
        → _completed += 1
        → Update overall progress bar
        → EpisodeList.update_episode_status(episode.id, DOWNLOADED)
        → SettingsManager.save_episode_cache(feed.id, episodes)
        → If _completed == _total: hide DownloadPanel

_on_error(episode, message)  ← worker thread
    └── QMetaObject.invokeMethod(self, "_handle_error", QueuedConnection,
            episode_id, message)
        → _completed += 1
        → EpisodeList.update_episode_status(episode.id, ERROR)
        → QMessageBox.critical(error detail)
        → If _completed == _total: hide DownloadPanel
```

---

## 5. Settings Dialog Flow

```
User opens Settings (menu or button)
    │
    v
SettingsDialog(settings, settings_manager)
    ├── Shows current download_dir
    ├── [フォルダ選択] → QFileDialog.getExistingDirectory()
    │     └── Updates preview in dialog
    └── [OK]
          ├── settings.download_dir = selected_path
          └── settings_manager.save(settings)
```

---

## 6. Window Geometry Persistence

```
MainWindow.__init__:
    geom = settings.window_geometry
    if geom:
        self.setGeometry(geom["x"], geom["y"], geom["width"], geom["height"])
        # Clamp to visible screen area
        screen_rect = QApplication.primaryScreen().availableGeometry()
        self.setGeometry(self.geometry().intersected(screen_rect)
                         or QRect(100, 100, 1024, 768))
    else:
        self.resize(1024, 768)

MainWindow.closeEvent:
    rect = self.geometry()
    settings.window_geometry = {
        "x": rect.x(), "y": rect.y(),
        "width": rect.width(), "height": rect.height()
    }
    settings_manager.save(settings)
```

---

## 7. Locale / i18n Flow

```
main():
    translator = QTranslator()
    locale = QLocale.system().name()          # e.g. "ja_JP"
    qm_path = resources / "i18n" / f"{locale}.qm"
    if qm_path.exists():
        translator.load(str(qm_path))
        QApplication.installTranslator(translator)
    # Falls back to English source strings if no .qm file
```
