# Unit 2: gui — コード生成計画

## ユニット情報

- **ユニット名**: gui
- **コード出力先**: `/home/mshattori/Dev/AI-DLC-work/podcast_downloader/gui/`
- **エントリーポイント**: `/home/mshattori/Dev/AI-DLC-work/main.py`
- **依存ユニット**: Unit 1: core（完了済み）

## 参照設計ドキュメント

- `aidlc-docs/construction/gui/functional-design/frontend-components.md`
- `aidlc-docs/construction/gui/functional-design/business-rules.md`
- `aidlc-docs/construction/gui/functional-design/business-logic-model.md`
- `aidlc-docs/construction/gui/nfr-design/nfr-design-patterns.md`
- `aidlc-docs/construction/gui/nfr-design/logical-components.md`

---

## 生成ステップ

### Step 1: データモデル（`core/models.py` 更新）
- [x] `Episode.duration_display` のデフォルト値を `"不明"` から英語コメント付きで確認（変更不要なら skip）

### Step 2: DownloadPanel（`gui/download_panel.py`）
- [x] `DownloadPanel` クラスを実装
- [x] `QMetaObject.invokeMethod` によるスレッドセーフ更新を実装（NFR Pattern 1）
- [x] 不定プログレスバーモードを実装（NFR Pattern 3）
- [x] `start_downloads()` / `_update_progress()` / `_handle_complete()` / `_handle_error()` を実装
- [x] キャンセルボタンで `DownloadManager.cancel_all()` を呼び出す

### Step 3: EpisodeList（`gui/episode_list.py`）
- [x] `EpisodeList` クラスを実装
- [x] `QTableWidget` でカラム（チェックボックス・タイトル・公開日・長さ・状態）を実装
- [x] チェックボックス ↔ 行選択の双方向同期を実装（BR-GUI-03-1）
- [x] 概要ペイン（`QTextEdit` read-only）を実装
- [x] `download_requested = Signal(list)` を実装
- [x] `set_episodes()` / `update_episode_status()` / `get_checked_episodes()` を実装
- [x] 全選択・選択解除ボタンを実装
- [x] `data-testid` 属性相当の `objectName` を各ウィジェットに設定

### Step 4: FeedPanel（`gui/feed_panel.py`）
- [x] `FeedPanel` クラスを実装
- [x] `QListWidget` でフィード一覧を表示
- [x] `FetchWorker(QThread)` クラスを実装（NFR Pattern 2）
- [x] 追加・削除・更新ボタンを実装
- [x] `AddFeedDialog` を実装（URL + ラベル入力、インラインバリデーション）
- [x] フィード削除確認ダイアログを実装（BR-GUI-02-1）
- [x] `feed_selected = Signal(Feed)` を実装
- [x] 起動時に全フィードのバックグラウンド更新を開始

### Step 5: SettingsDialog（`gui/settings_dialog.py`）
- [x] `SettingsDialog` クラスを実装
- [x] ダウンロード先フォルダ選択（`QFileDialog`）を実装
- [x] OK で `SettingsManager.save()` を呼び出す

### Step 6: MainWindow（`gui/main_window.py`）
- [x] `MainWindow` クラスを実装
- [x] `QSplitter` による左右ペインレイアウトを実装
- [x] メニューバー（ファイル→終了・設定→設定ダイアログ）を実装
- [x] パネル間シグナル接続を実装
- [x] ウィンドウジオメトリの保存・復元を実装（NFR Pattern 4）
- [x] `closeEvent` で設定を保存

### Step 7: エントリーポイント（`main.py`）
- [x] `QApplication` 初期化
- [x] `RotatingFileHandler` でログ設定
- [x] `SettingsManager.load()` → `MainWindow` 起動
- [x] `sys.exit(app.exec())`

### Step 8: コードサマリードキュメント生成
- [x] `aidlc-docs/construction/gui/code/code-summary.md` を作成

---

## 機能要件カバレッジ

| 機能要件 | 実装ステップ |
|---|---|
| FR-01: RSSフィード管理（UI） | Step 4（FeedPanel） |
| FR-02: エピソード一覧表示 | Step 3（EpisodeList） |
| FR-04: ダウンロード（UI） | Step 2（DownloadPanel）+ Step 3 |
| FR-05: 進捗表示 | Step 2（DownloadPanel） |
| FR-06: 設定管理（UI） | Step 5（SettingsDialog） |
