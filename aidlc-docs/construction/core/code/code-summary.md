# コード生成サマリー — Unit 1: core

## 生成ファイル一覧

### アプリケーションコード

| ファイル | 内容 |
|---|---|
| `pyproject.toml` | プロジェクト設定・依存関係定義 |
| `README.md` | プロジェクト説明・起動手順 |
| `podcast_downloader/__init__.py` | パッケージ初期化 |
| `podcast_downloader/core/__init__.py` | coreパッケージ初期化 |
| `podcast_downloader/gui/__init__.py` | guiパッケージ初期化（Unit 2用） |
| `podcast_downloader/core/models.py` | Feed・Episode・AppSettings・DownloadStatus |
| `podcast_downloader/core/duration_parser.py` | durationパース・フォーマット（純粋関数） |
| `podcast_downloader/core/settings_manager.py` | 設定・キャッシュのJSON読み書き |
| `podcast_downloader/core/rss_parser.py` | RSSフィード取得・解析・マージ |
| `podcast_downloader/core/downloader.py` | バックグラウンドダウンロードエンジン |

### テストコード

| ファイル | テスト数 | カバー範囲 |
|---|---|---|
| `tests/test_duration_parser.py` | 16 | parse_duration・format_duration 全フォーマット・境界値 |
| `tests/test_settings_manager.py` | 10 | 保存・読み込み・JSON破損・アトミック書き込み |
| `tests/test_rss_parser.py` | 13 | RSS解析・フィルタリング・重複排除・ネットワークエラー |
| `tests/test_downloader.py` | 6 | ファイル名生成・スキップ・エラー処理・キャンセル・進捗 |

## 実装サマリー

### 主要設計決定の反映

| 設計決定 | 実装箇所 |
|---|---|
| `audio_url` 欠損エピソードを除外（BR-02-1） | `rss_parser._entry_to_episode()` |
| duration 複数フォーマット正規化（BR-03-x） | `duration_parser.parse_duration()` |
| ファイル名: 日付+タイトル+拡張子（BR-04-x） | `downloader._build_dest_path()` |
| ファイル存在時スキップ（BR-05-x） | `downloader.DownloadManager._download()` |
| 中断時の一時ファイル削除（BR-06-x） | `downloader.DownloadManager._download()` finally節 |
| アトミック書き込み（NFR設計パターン3） | `settings_manager.save()` / `save_episode_cache()` |
| フェイルセーフデフォルト（NFR設計パターン4） | `settings_manager.load()` |
| セマフォによる同時実行制御（NFR設計パターン2） | `downloader.DownloadManager._semaphore` |
| RotatingFileHandler ログ設定 | `main.py`（Unit 2生成時に実装） |
