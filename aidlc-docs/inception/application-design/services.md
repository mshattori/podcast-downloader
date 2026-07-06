# サービス定義

本アプリはシンプルなデスクトップツールのため、独立したサービスレイヤーは設けません。  
代わりに `core/` コンポーネントが直接サービス機能を担います。  
以下に各サービス相当の責務とオーケストレーションパターンを定義します。

---

## サービス1: フィード取得サービス（FeedFetchService）

**実装場所**: `core/rss_parser.py` + `gui/feed_panel.py`

**責務**:
- ユーザーがフィード更新を要求したとき、バックグラウンドスレッドでRSS取得を実行する
- 取得完了後、エピソードキャッシュを更新し、GUI に通知する

**オーケストレーションフロー**:
```
FeedPanel.refresh_feed()
  → QThread でバックグラウンド実行
  → rss_parser.fetch_and_parse(url)
  → settings_manager.save_episode_cache(feed_id, episodes)
  → Signal 発行 → EpisodeList.set_episodes(episodes)
```

---

## サービス2: ダウンロードサービス（DownloadService）

**実装場所**: `core/downloader.py` + `gui/download_panel.py`

**責務**:
- 選択されたエピソードをキューに追加し、同時実行数を制御しながらダウンロードする
- 進捗・完了・エラーを GUI へ通知する（スレッドセーフなシグナル経由）
- ダウンロード済みファイルの検出と上書き確認を行う

**オーケストレーションフロー**:
```
EpisodeList.download_requested Signal
  → DownloadPanel.start_downloads(episodes, dest_dir)
  → DownloadManager.enqueue(episode, callbacks...)
    → threading.Thread × max_workers
      → HTTP ストリーミングダウンロード
      → on_progress コールバック → ProgressBar 更新
      → on_complete コールバック → DownloadStatus.DOWNLOADED
      → on_error コールバック → DownloadStatus.ERROR
  → settings_manager.save_episode_cache() でステータス永続化
```

---

## サービス3: 設定管理サービス（SettingsService）

**実装場所**: `core/settings_manager.py`

**責務**:
- アプリ起動時に設定とキャッシュを読み込む
- 設定変更・ウィンドウ終了時に設定を保存する
- OS ごとの設定ディレクトリを解決する

**オーケストレーションフロー**:
```
main.py 起動
  → SettingsManager.load() → AppSettings
  → MainWindow(settings)
  → アプリ実行中...
MainWindow.closeEvent()
  → SettingsManager.save(current_settings)
```

---

## スレッド設計

| 処理 | スレッド | 通信方式 |
|---|---|---|
| UIイベント | メインスレッド（Qt） | — |
| RSSフィード取得 | QThread | Signal/Slot |
| ファイルダウンロード | threading.Thread × N | コールバック → QMetaObject.invokeMethod |
| ファイルI/O（設定保存） | メインスレッド | 同期 |

**注意**: バックグラウンドスレッドからGUIを直接更新することは禁止。  
必ずシグナル/スロットまたは `QMetaObject.invokeMethod` 経由で更新する。
