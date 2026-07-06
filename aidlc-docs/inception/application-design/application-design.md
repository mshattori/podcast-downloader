# アプリケーション設計（統合ドキュメント）

## 概要

**アプリ名**: Podcast Downloader  
**技術スタック**: Python 3.11+ / PySide6 / feedparser / requests  
**対応OS**: Windows / macOS / Linux

---

## アーキテクチャ方針

- **2レイヤー構成**: `core/`（ビジネスロジック）＋ `gui/`（PySide6 UI）
- **core/ は GUI に依存しない** — テスト容易性を確保
- **バックグラウンドスレッド**: RSS取得・ファイルダウンロードはバックグラウンドで実行し、UIをブロックしない
- **データ永続化**: JSON ファイルキャッシュ（設定・エピソード一覧）

---

## ディレクトリ構造

```
podcast_downloader/          # アプリルート
├── core/
│   ├── models.py            # Feed・Episode・AppSettings データクラス
│   ├── rss_parser.py        # RSSフィード取得・解析
│   ├── duration_parser.py   # 音声長さ文字列のパース・フォーマット
│   ├── downloader.py        # ダウンロードエンジン（threading）
│   └── settings_manager.py  # 設定・キャッシュの読み書き（JSON）
├── gui/
│   ├── main_window.py       # メインウィンドウ（左右ペイン構成）
│   ├── feed_panel.py        # 左ペイン：フィード管理
│   ├── episode_list.py      # 右ペイン：エピソード一覧（表形式）
│   ├── download_panel.py    # 右ペイン下部：ダウンロード進捗
│   └── settings_dialog.py   # 設定ダイアログ
├── main.py                  # エントリーポイント
├── pyproject.toml           # プロジェクト設定・依存関係
└── tests/
    ├── test_rss_parser.py
    ├── test_duration_parser.py
    ├── test_downloader.py
    └── test_settings_manager.py
```

---

## メインウィンドウレイアウト

```
+--------------------------------------------------+
| [メニュー: ファイル | 設定 | ヘルプ]             |
+----------------+----------------------------------|
|                |  [更新] [ダウンロード]           |
| フィード一覧   |  +-----+------------+-----+----+ |
|                |  |  #  | タイトル   | 日付| 長さ| |
| [+ 追加]       |  +-----+------------+-----+----+ |
| [- 削除]       |  | [ ] | Episode 1  | ... | ... | |
| [↺ 更新]       |  | [ ] | Episode 2  | ... | ... | |
|                |  | [x] | Episode 3  | ... | ... | |
| > Feed A       |  +-----+------------+-----+----+ |
|   Feed B       |  概要: [選択中エピソードの概要]  |
|   Feed C       +----------------------------------+
|                |  ダウンロード進捗                |
|                |  全体: [=========>] 2/3件        |
|                |  現在: [=====>    ] Episode 3 45%|
+----------------+----------------------------------+
```

---

## コンポーネント一覧（詳細は各ファイル参照）

| コンポーネント | 責務 | レイヤー |
|---|---|---|
| `models.py` | Feed・Episode・AppSettings データ定義 | core |
| `rss_parser.py` | RSSフィード取得・解析 | core |
| `duration_parser.py` | 音声長さパース・フォーマット | core |
| `downloader.py` | バックグラウンドダウンロード管理 | core |
| `settings_manager.py` | 設定・キャッシュのJSON読み書き | core |
| `main_window.py` | メインウィンドウ・レイアウト管理 | gui |
| `feed_panel.py` | フィード一覧・追加・削除・更新 | gui |
| `episode_list.py` | エピソード一覧表示・複数選択 | gui |
| `download_panel.py` | ダウンロード進捗表示・キャンセル | gui |
| `settings_dialog.py` | 設定変更ダイアログ | gui |

詳細:
- コンポーネント責務 → `components.md`
- メソッドシグネチャ → `component-methods.md`
- サービス・オーケストレーション → `services.md`
- 依存関係・データフロー → `component-dependency.md`

---

## 主要設計決定

| 決定 | 選択 | 理由 |
|---|---|---|
| GUIフレームワーク | PySide6 | クロスプラットフォーム・リッチUI・LGPLライセンス |
| データキャッシュ | JSON ファイル | シンプル・デバッグ容易・SQLite不要 |
| 並行処理 | threading | 標準ライブラリ・シンプル・feedparser との互換性 |
| 設定保存 | JSON ファイル | 可搬性・人間が読めるフォーマット |
| レイアウト | 左右ペイン（サイドバー型） | フィードとエピソードを同時に確認しやすい |
