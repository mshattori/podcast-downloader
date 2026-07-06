# コンポーネント依存関係

## 依存関係マトリクス

| コンポーネント | models | rss_parser | duration_parser | downloader | settings_manager |
|---|:---:|:---:|:---:|:---:|:---:|
| **rss_parser** | ✅ | — | ✅ | — | — |
| **duration_parser** | — | — | — | — | — |
| **downloader** | ✅ | — | — | — | — |
| **settings_manager** | ✅ | — | — | — | — |
| **main_window** | ✅ | — | — | — | ✅ |
| **feed_panel** | ✅ | ✅ | — | — | ✅ |
| **episode_list** | ✅ | — | — | — | — |
| **download_panel** | ✅ | — | — | ✅ | — |
| **settings_dialog** | ✅ | — | — | — | ✅ |
| **main.py** | ✅ | — | — | — | ✅ |

凡例: ✅ = 依存あり、— = 依存なし

---

## 依存関係図

```
main.py
  ├── SettingsManager ──────────→ models (AppSettings, Feed)
  └── MainWindow
        ├── FeedPanel
        │     ├── RSSParser ───→ DurationParser
        │     │                └→ models (Episode)
        │     └── SettingsManager
        ├── EpisodeList ────────→ models (Episode, DownloadStatus)
        ├── DownloadPanel
        │     └── DownloadManager → models (Episode)
        └── SettingsDialog ──────→ SettingsManager
```

---

## データフロー

### フィード取得フロー

```
[ユーザー: フィード更新ボタン]
    |
    v
FeedPanel.refresh_feed()
    |
    v (QThread バックグラウンド)
RSSParser.fetch_and_parse(url)
    |
    v
DurationParser.parse_duration() / format_duration()  ← Episode 生成時に使用
    |
    v
[Episode リスト]
    |
    +──→ SettingsManager.save_episode_cache()  （キャッシュ保存）
    |
    v (Signal → メインスレッド)
EpisodeList.set_episodes()
    |
    v
[GUIに一覧表示]
```

### ダウンロードフロー

```
[ユーザー: エピソード選択 → ダウンロードボタン]
    |
    v
EpisodeList.download_requested Signal (list[Episode])
    |
    v
DownloadPanel.start_downloads(episodes, dest_dir)
    |
    v
DownloadManager.enqueue(episode, callbacks)  × N件
    |
    v (threading.Thread × max_workers)
HTTP ストリーミングダウンロード
    |
    +──→ on_progress(episode, percent)
    |         |
    |         v (QMetaObject.invokeMethod → メインスレッド)
    |     ProgressBar 更新
    |
    +──→ on_complete(episode, local_path)
    |         |
    |         v
    |     Episode.status = DOWNLOADED
    |     SettingsManager.save_episode_cache()
    |     EpisodeList.update_episode_status()
    |
    +──→ on_error(episode, message)
              |
              v
          Episode.status = ERROR
          エラーメッセージ表示
```

---

## レイヤー境界ルール

1. **`gui/` は `core/` にのみ依存する** — `core/` は `gui/` を知らない
2. **`core/` コンポーネント間の依存は最小限に** — `models.py` は共有するが、他の `core/` コンポーネントへの依存は避ける
3. **`duration_parser.py` は純粋関数のみ** — 副作用なし、外部依存なし（テスト容易性を確保）
4. **バックグラウンドスレッドからの GUI 更新は禁止** — Signal/Slot または `invokeMethod` 経由のみ
