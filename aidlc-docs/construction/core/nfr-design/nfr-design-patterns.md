# NFR設計パターン — Unit 1: core

## パターン1: バックグラウンドスレッドパターン（UIブロック防止）

**適用箇所**: `rss_parser.fetch_and_parse()` / `downloader.DownloadManager`

**設計**:
- RSS取得: `threading.Thread` で実行し、完了時にコールバックで結果を返す
- ダウンロード: `threading.Thread` × 最大5本のワーカースレッドでキュー処理
- スレッドからGUIへの通知: コールバック関数経由（Qt側で `QMetaObject.invokeMethod` に橋渡し）

```
メインスレッド（Qt イベントループ）
    │
    ├─ RSS取得スレッド ──→ on_fetched(episodes) コールバック
    │
    └─ ダウンロードスレッド × N
           ├─ on_progress(episode, percent) コールバック
           ├─ on_complete(episode, path) コールバック
           └─ on_error(episode, message) コールバック
```

**キャンセルフラグ**:
- 各ダウンロードスレッドは `threading.Event` のキャンセルフラグを参照する
- チャンク書き込みループごとにフラグを確認し、セットされていれば中断

---

## パターン2: スレッドプールパターン（同時ダウンロード制御）

**適用箇所**: `downloader.DownloadManager`

**設計**:
- `threading.Semaphore(5)` でスロットを制御する（`MAX_CONCURRENT_DOWNLOADS = 5`）
- キューに積まれたエピソードは、セマフォ取得後にスレッドを起動する
- スレッド完了時にセマフォを解放し、次のキュー項目を開始する

```python
# 概念コード
_semaphore = threading.Semaphore(MAX_CONCURRENT_DOWNLOADS)

def _worker(episode, ...):
    with _semaphore:          # スロット獲得（空き待ち）
        _download(episode)    # ダウンロード実行
                              # withブロック終了でスロット解放
```

---

## パターン3: アトミック書き込みパターン（設定ファイル破損防止）

**適用箇所**: `settings_manager.save()` / `save_episode_cache()`

**設計**:
- 直接ターゲットファイルに書き込まず、一時ファイルに書き込んでからリネームする
- ファイルシステムのアトミックなリネーム操作により、書き込み途中のクラッシュでファイルが破損しない

```
1. settings.json.tmp に書き込む
2. os.replace("settings.json.tmp", "settings.json")  # アトミック
```

---

## パターン4: フェイルセーフデフォルトパターン（設定破損耐性）

**適用箇所**: `settings_manager.load()`

**設計**:
- 設定ファイルが存在しない → デフォルト値で正常起動
- JSONパースエラー → デフォルト値で起動し、ログにWARNING記録、ユーザーに通知
- フィールド欠損（古いバージョンとの互換） → 欠損フィールドをデフォルト値で補完

---

## パターン5: ロギングパターン

**適用箇所**: 全 core モジュール

**設計**:
- 各モジュールは `logging.getLogger(__name__)` でロガーを取得する
- ルートロガーの設定は `main.py` で行う（core モジュールは設定しない）
- `RotatingFileHandler`: 最大5MB × 3世代

```python
# 各モジュール
logger = logging.getLogger(__name__)

# main.py で設定
handler = RotatingFileHandler(log_path, maxBytes=5*1024*1024, backupCount=3)
handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s"))
logging.getLogger().addHandler(handler)
logging.getLogger().setLevel(logging.DEBUG if os.getenv("PODCAST_DL_DEBUG") else logging.INFO)
```

**ログレベル指針**:
| レベル | 用途 |
|---|---|
| `DEBUG` | 詳細な処理ステップ（チャンク書き込み等） |
| `INFO` | フィード取得開始/完了、ダウンロード開始/完了 |
| `WARNING` | 設定ファイル破損、エピソードフィールド欠損 |
| `ERROR` | ネットワークエラー、ダウンロード失敗 |
