# アプリケーション設計計画

RSSポッドキャストダウンローダーの高レベルコンポーネント設計について確認します。
各 `[Answer]:` タグの後に回答を記入し、「完了しました」とお知らせください。

---

## 設計の前提（確認済み要件から）

- **技術スタック**: Python 3.11+ / PySide6
- **対応OS**: Windows / macOS / Linux
- **主要機能**: RSSフィード管理・エピソード一覧表示・一括ダウンロード・進捗表示・設定管理

---

## 質問 1 — コンポーネント構成

以下のコンポーネント分割を想定しています。追加・変更の要望はありますか？

**想定コンポーネント:**

```
podcast_downloader/
├── core/
│   ├── models.py          # Feed・Episode データモデル
│   ├── rss_parser.py      # RSSフィード解析
│   ├── duration_parser.py # 音声長さ文字列のパース
│   ├── downloader.py      # ダウンロードエンジン（バックグラウンド）
│   └── settings_manager.py# 設定の読み書き
├── gui/
│   ├── main_window.py     # メインウィンドウ
│   ├── feed_panel.py      # フィード管理パネル
│   ├── episode_list.py    # エピソード一覧ウィジェット
│   ├── download_panel.py  # ダウンロード進捗パネル
│   └── settings_dialog.py # 設定ダイアログ
└── main.py                # エントリーポイント
```

A) この構成でよい

B) コアとGUIをさらに分離したい（別パッケージ/別ディレクトリ）

C) もっとシンプルにしたい（ファイル数を減らす）

D) Other (以下に記述してください)

[Answer]: A

---

## 質問 2 — データモデル設計

エピソードとフィードのデータをどこに保存しますか？

A) メモリのみ（アプリ起動のたびにRSSを再取得する）

B) ローカルDB（SQLite）にキャッシュする（オフラインでも一覧を見られる）

C) JSONファイルにキャッシュする（シンプル、SQLiteより軽量）

D) Other (以下に記述してください)

[Answer]: C 

---

## 質問 3 — ダウンロードエンジンの並行処理

複数エピソードを同時ダウンロードする際の方式を選んでください。

A) `threading`（Pythonスレッド）— シンプルで標準的

B) `asyncio` + `aiohttp`（非同期IO）— モダンだが複雑

C) `concurrent.futures.ThreadPoolExecutor`（スレッドプール）— スレッド管理が容易

D) Other (以下に記述してください)

[Answer]: A

---

## 質問 4 — 設定ファイルの形式と保存場所

設定（登録フィードURLリスト・ダウンロード先フォルダ等）をどこに保存しますか？

A) `QSettings`（OS標準の設定ストレージ：Windowsはレジストリ、macOSはplist、LinuxはINI）

B) JSONファイル（`~/.config/podcast-downloader/settings.json` 等）

C) TOML/INIファイル

D) Other (以下に記述してください)

[Answer]: B

---

## 質問 5 — GUIのメインレイアウト

メインウィンドウのレイアウト構成を選んでください。

A) 左ペイン：フィード一覧 ／ 右ペイン：エピソード一覧（サイドバー型）

B) 上部：フィード選択タブ ／ 下部：エピソード一覧（タブ型）

C) シングルビュー（フィードを選ぶとエピソード一覧に切り替わる）

D) Other (以下に記述してください)

[Answer]: A

---

## 設計チェックリスト（実行予定）

- [x] `components.md` — コンポーネント定義と責務
- [x] `component-methods.md` — 各コンポーネントのメソッドシグネチャ
- [x] `services.md` — サービス定義とオーケストレーション
- [x] `component-dependency.md` — 依存関係とデータフロー
- [x] `application-design.md` — 上記の統合ドキュメント
