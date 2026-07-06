# Frontend Components — Unit 2: gui

## Component Hierarchy

```
MainWindow (QMainWindow)
├── MenuBar
│   ├── File menu  → Quit
│   └── Settings menu → Open SettingsDialog
├── Central Widget (QSplitter, horizontal)
│   ├── FeedPanel (QWidget) — left pane
│   │   ├── Feed list (QListWidget)
│   │   └── Button bar: [+ 追加] [- 削除] [↺ 更新]
│   └── Right pane (QWidget, vertical layout)
│       ├── EpisodeList (QWidget)
│       │   ├── Toolbar: [ダウンロード] [全選択] [選択解除]
│       │   ├── Episode table (QTableWidget)
│       │   │   Columns: checkbox | # | タイトル | 公開日 | 長さ | 状態
│       │   └── DescriptionPane (QTextEdit, read-only)
│       └── DownloadPanel (QWidget)
│           ├── Overall progress (QProgressBar + label "N/M件")
│           ├── Per-file progress (QProgressBar + filename label)
│           └── [キャンセル] button
└── StatusBar (QStatusBar)
```

---

## MainWindow

**責務**: ルートウィンドウ・レイアウト管理・パネル間シグナル接続

**State**:
- `settings: AppSettings`
- `settings_manager: SettingsManager`
- `download_manager: DownloadManager`

**Signals received**:
- `FeedPanel.feed_selected(Feed)` → `EpisodeList.load_feed(Feed)`
- `EpisodeList.download_requested(list[Episode])` → `DownloadPanel.start_downloads(...)`

**Key behaviors**:
- Saves window geometry on `closeEvent`
- Restores geometry from `AppSettings.window_geometry` on startup
- Triggers background RSS fetch for all feeds at startup

---

## FeedPanel

**責務**: 登録済みフィードの表示・追加・削除・更新

**Signals**:
- `feed_selected = Signal(Feed)` — emitted when user clicks a feed

**UI elements**:

| Element | Widget | data-testid |
|---|---|---|
| フィード一覧 | QListWidget | `feed-panel-list` |
| 追加ボタン | QPushButton | `feed-panel-add-button` |
| 削除ボタン | QPushButton | `feed-panel-remove-button` |
| 更新ボタン | QPushButton | `feed-panel-refresh-button` |

**Add feed flow**:
1. Open `AddFeedDialog` (URL + optional label)
2. Validate URL format
3. Show spinner while fetching feed to confirm it is valid RSS
4. On success: add to `AppSettings.feeds`, save, refresh list
5. On error: show `QMessageBox.critical` with error detail

**Delete feed flow**:
1. Show `QMessageBox.question` confirmation
2. On confirm: remove from settings, delete episode cache file, refresh list

**Refresh feed flow**:
1. Run `rss_parser.fetch_and_parse()` in a `QThread`
2. Merge with cached episodes via `merge_episodes()`
3. Save updated cache
4. Emit `feed_selected` to refresh `EpisodeList`

---

## AddFeedDialog

**責務**: 新規フィードURL・ラベルの入力

**UI elements**:

| Element | Widget | data-testid |
|---|---|---|
| URL入力フィールド | QLineEdit | `add-feed-dialog-url-input` |
| ラベル入力フィールド | QLineEdit | `add-feed-dialog-label-input` |
| OKボタン | QPushButton | `add-feed-dialog-ok-button` |
| キャンセルボタン | QPushButton | `add-feed-dialog-cancel-button` |

**Validation**:
- URL must start with `http://` or `https://` (inline error label, not dialog)
- Label is optional; defaults to URL hostname if empty

---

## EpisodeList

**責務**: エピソード一覧表示・複数選択・概要ペイン表示

**Signals**:
- `download_requested = Signal(list)` — list[Episode], emitted on download button click

**UI elements**:

| Element | Widget | data-testid |
|---|---|---|
| エピソードテーブル | QTableWidget | `episode-list-table` |
| ダウンロードボタン | QPushButton | `episode-list-download-button` |
| 全選択ボタン | QPushButton | `episode-list-select-all-button` |
| 選択解除ボタン | QPushButton | `episode-list-deselect-button` |
| 概要ペイン | QTextEdit (read-only) | `episode-list-description-pane` |

**Table columns**:

| # | Column | Width | Notes |
|---|---|---|---|
| 0 | チェックボックス | 30px | `Qt.ItemIsUserCheckable` |
| 1 | タイトル | stretch | truncated with ellipsis |
| 2 | 公開日 | 110px | `YYYY-MM-DD HH:MM` or `日時不明` |
| 3 | 長さ | 90px | `duration_display` |
| 4 | 状態 | 80px | icon + text |

**Selection**:
- Checkbox column: toggles check state independently
- Row click: selects row (Ctrl/Shift for multi-select) AND syncs checkbox
- "全選択" checks all rows; "選択解除" unchecks all
- Download button enabled only when ≥1 row is checked

**Description pane**:
- Updates when a single row is selected
- Shows plain text (HTML stripped)
- Clears when selection is empty or multiple rows are selected

**Status display**:

| DownloadStatus | 表示テキスト | アイコン |
|---|---|---|
| NOT_DOWNLOADED | 未ダウンロード | — |
| DOWNLOADING | ダウンロード中 | spinner |
| DOWNLOADED | 済 | ✓ |
| ERROR | エラー | ✗ |

---

## DownloadPanel

**責務**: ダウンロード進捗表示・キャンセル

**UI elements**:

| Element | Widget | data-testid |
|---|---|---|
| 全体プログレスバー | QProgressBar | `download-panel-overall-progress` |
| 全体ラベル | QLabel | `download-panel-overall-label` |
| 個別プログレスバー | QProgressBar | `download-panel-current-progress` |
| 個別ファイル名ラベル | QLabel | `download-panel-current-label` |
| キャンセルボタン | QPushButton | `download-panel-cancel-button` |

**State**:
- `_total: int` — total episodes in current batch
- `_completed: int` — completed (success or error) count
- `_current_episode: Episode | None`

**Visibility**: panel is hidden when no downloads are active; shown when `start_downloads()` is called.

**Thread safety**: `on_progress` / `on_complete` / `on_error` callbacks arrive from worker threads. Use `QMetaObject.invokeMethod(..., Qt.QueuedConnection)` to forward updates to the main thread.

---

## SettingsDialog

**責務**: ダウンロード先フォルダの設定

**UI elements**:

| Element | Widget | data-testid |
|---|---|---|
| フォルダパス表示 | QLineEdit (read-only) | `settings-dialog-download-dir-input` |
| フォルダ選択ボタン | QPushButton | `settings-dialog-browse-button` |
| OKボタン | QPushButton | `settings-dialog-ok-button` |
| キャンセルボタン | QPushButton | `settings-dialog-cancel-button` |

---

## Internationalisation (i18n)

- Use `QCoreApplication.translate()` (or `tr()`) for all user-visible strings
- Default locale: OS locale (`QLocale.system()`)
- Japanese translation file: `podcast_downloader/gui/i18n/ja.ts` → compiled to `ja.qm`
- Fallback: English string literals in source code
