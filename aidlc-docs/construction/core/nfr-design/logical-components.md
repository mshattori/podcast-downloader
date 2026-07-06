# 論理コンポーネント設計 — Unit 1: core

## コンポーネント構成とNFR対応の対照

| コンポーネント | NFR対応 | 採用パターン |
|---|---|---|
| `models.py` | テスト容易性 | データクラス、列挙型（純粋な値オブジェクト） |
| `duration_parser.py` | テスト容易性・パフォーマンス | 純粋関数（副作用なし） |
| `rss_parser.py` | パフォーマンス・信頼性 | バックグラウンドスレッド、フェイルセーフ |
| `downloader.py` | パフォーマンス・信頼性 | スレッドプール（セマフォ）、キャンセルフラグ |
| `settings_manager.py` | 信頼性・移植性 | アトミック書き込み、フェイルセーフデフォルト |

---

## downloader.py の論理構造

```
DownloadManager
│
├── _semaphore: Semaphore(5)        # スロット制御
├── _queue: list[DownloadTask]      # 待機中タスク
├── _active: dict[str, Thread]      # 実行中スレッド（episode_id → Thread）
└── _cancel_flags: dict[str, Event] # キャンセルフラグ（episode_id → Event）

DownloadTask（内部データ）
│
├── episode: Episode
├── dest_dir: str
├── on_progress: Callable
├── on_complete: Callable
└── on_error: Callable
```

**エンキュー時の処理フロー**:
```
enqueue(episode, ...)
  → _queue に DownloadTask を追加
  → _try_start_next() を呼び出す

_try_start_next()
  → キューが空なら終了
  → セマフォ取得を試みる（non-blocking）
  → 取得成功 → Thread 起動 → _active に登録
  → 取得失敗 → そのまま待機（スレッド完了時に再試行）
```

---

## settings_manager.py の論理構造

```
SettingsManager
│
├── _config_dir: Path               # OS別設定ディレクトリ
│     Windows: %APPDATA%\podcast-downloader\
│     macOS:   ~/Library/Application Support/podcast-downloader/
│     Linux:   ~/.config/podcast-downloader/
│
├── _settings_path: Path            # settings.json
└── _cache_dir: Path                # cache/ サブディレクトリ

ファイル構造:
{config_dir}/
├── settings.json      # AppSettings（フィード一覧・ダウンロード先等）
├── app.log            # ログファイル
├── app.log.1          # ローテーション済みログ
└── cache/
    ├── {feed_id_1}.json   # フィード1のエピソードキャッシュ
    └── {feed_id_2}.json   # フィード2のエピソードキャッシュ
```

---

## rss_parser.py の論理構造

```
fetch_and_parse(url)
│
├── requests.get(url, timeout=30, stream=False)
│     └── ConnectionError / Timeout → RSSFetchError
│
├── feedparser.parse(response.text)
│     └── bozo=True（パースエラー） → RSSParseError
│
└── _entries_to_episodes(feed.entries) → list[Episode]
      └── _extract_episode(entry) → Episode | None
            ├── audio_url 欠損 → None（スキップ）
            ├── duration_parser.parse_duration(itunes_duration)
            └── Episode(**fields)
```

---

## エラー型定義

```python
class PodcastDownloaderError(Exception):
    """基底例外クラス"""

class RSSFetchError(PodcastDownloaderError):
    """RSS取得失敗（ネットワークエラー等）"""

class RSSParseError(PodcastDownloaderError):
    """RSSパース失敗（不正フォーマット）"""

class DownloadError(PodcastDownloaderError):
    """ダウンロード失敗"""

class SettingsError(PodcastDownloaderError):
    """設定ファイル読み書きエラー"""
```
