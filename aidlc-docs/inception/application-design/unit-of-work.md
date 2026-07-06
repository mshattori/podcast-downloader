# ユニット定義

## 開発方針

- **開発順序**: Unit 1（core）完成後 → Unit 2（gui）
- **パッケージ構成**: 単一パッケージ（`podcast_downloader/`）、1つの `pyproject.toml`
- **依存方向**: Unit 2 は Unit 1 に依存。Unit 1 は Unit 2 を知らない。

---

## Unit 1: core — コアエンジン

**概要**: GUIに依存しないビジネスロジック層。単体でテスト可能。

**含まれるモジュール**:

| モジュール | 責務 |
|---|---|
| `core/models.py` | Feed・Episode・AppSettings・DownloadStatus データ定義 |
| `core/rss_parser.py` | RSSフィード取得・feedparser による解析・Episodeリスト生成 |
| `core/duration_parser.py` | durationメタデータのパース（秒/MM:SS/HH:MM:SS）と表示文字列生成 |
| `core/downloader.py` | threading を使ったバックグラウンドダウンロード管理 |
| `core/settings_manager.py` | JSON による設定・エピソードキャッシュの読み書き |

**成果物（コード）**:
```
podcast_downloader/
└── core/
    ├── __init__.py
    ├── models.py
    ├── rss_parser.py
    ├── duration_parser.py
    ├── downloader.py
    └── settings_manager.py
tests/
├── test_rss_parser.py
├── test_duration_parser.py
├── test_downloader.py
└── test_settings_manager.py
```

**完了基準**:
- 全モジュール実装済み
- 全ユニットテスト通過
- GUI なしで RSS 取得・解析・ダウンロードが動作すること

---

## Unit 2: gui — GUIアプリケーション

**概要**: PySide6 による GUI 層。Unit 1 のコアエンジンを組み合わせてユーザーに提供する。

**依存**: Unit 1（core）が完成していること

**含まれるモジュール**:

| モジュール | 責務 |
|---|---|
| `gui/main_window.py` | メインウィンドウ・左右ペインレイアウト・メニューバー |
| `gui/feed_panel.py` | 左ペイン：フィード一覧・追加・削除・更新 |
| `gui/episode_list.py` | 右ペイン：エピソード表形式一覧・複数選択 |
| `gui/download_panel.py` | ダウンロード進捗パネル・プログレスバー |
| `gui/settings_dialog.py` | 設定ダイアログ（ダウンロード先・同時数） |
| `main.py` | アプリエントリーポイント・QApplication 初期化 |

**成果物（コード）**:
```
podcast_downloader/
└── gui/
    ├── __init__.py
    ├── main_window.py
    ├── feed_panel.py
    ├── episode_list.py
    ├── download_panel.py
    └── settings_dialog.py
main.py
pyproject.toml
```

**完了基準**:
- 全 GUI コンポーネント実装済み
- アプリが起動し、RSS フィードの登録・一覧表示・ダウンロードが動作すること
- Windows / macOS / Linux で起動確認

---

## プロジェクト全体構成

```
podcast_downloader/          # リポジトリルート
├── podcast_downloader/      # メインパッケージ
│   ├── __init__.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── models.py
│   │   ├── rss_parser.py
│   │   ├── duration_parser.py
│   │   ├── downloader.py
│   │   └── settings_manager.py
│   └── gui/
│       ├── __init__.py
│       ├── main_window.py
│       ├── feed_panel.py
│       ├── episode_list.py
│       ├── download_panel.py
│       └── settings_dialog.py
├── tests/
│   ├── __init__.py
│   ├── test_rss_parser.py
│   ├── test_duration_parser.py
│   ├── test_downloader.py
│   └── test_settings_manager.py
├── main.py
└── pyproject.toml
```
