# ユニット依存関係

## 依存関係マトリクス

| | Unit 1: core | Unit 2: gui |
|---|:---:|:---:|
| **Unit 1: core** | — | — |
| **Unit 2: gui** | ✅ 依存 | — |

- Unit 1 は他のユニットに依存しない（完全独立）
- Unit 2 は Unit 1 に依存する（Unit 1 完成後に着手）

## 開発シーケンス

```
[Unit 1: core]
  モデル定義 → RSS解析 → Duration解析 → ダウンロードエンジン → 設定管理
  → ユニットテスト全通過
        |
        v（Unit 1 完成後）
[Unit 2: gui]
  メインウィンドウ → フィードパネル → エピソード一覧 → ダウンロードパネル → 設定ダイアログ
  → 統合テスト・動作確認
```

## インターフェース境界

Unit 2 が Unit 1 から利用する公開インターフェース:

| Unit 1 モジュール | Unit 2 利用箇所 | 利用内容 |
|---|---|---|
| `models.py` | 全 GUI コンポーネント | Feed / Episode / AppSettings / DownloadStatus |
| `rss_parser.py` | `feed_panel.py` | `fetch_and_parse(url)` |
| `duration_parser.py` | `rss_parser.py` 内部（間接利用） | Unit 2 からの直接利用なし |
| `downloader.py` | `download_panel.py` | `DownloadManager` クラス全体 |
| `settings_manager.py` | `main_window.py`, `feed_panel.py`, `settings_dialog.py` | `load()`, `save()`, `load_episode_cache()`, `save_episode_cache()` |
