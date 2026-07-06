# コンポーネントメソッド定義

詳細なビジネスロジックは CONSTRUCTION フェーズの機能設計で定義します。  
ここでは各コンポーネントのインターフェース（シグネチャ・入出力）を定義します。

---

## core/models.py

```python
@dataclass
class Feed:
    id: str                    # UUID
    url: str
    label: str
    last_fetched: datetime | None

@dataclass
class Episode:
    id: str                    # UUID (feedid + guid ハッシュ)
    feed_id: str
    title: str
    published: datetime | None
    duration_seconds: int | None   # None = 不明
    duration_display: str          # 例: "1時間30分00秒"
    description: str
    audio_url: str
    status: DownloadStatus
    local_path: str | None         # ダウンロード済みの場合のみ

class DownloadStatus(Enum):
    NOT_DOWNLOADED = "not_downloaded"
    DOWNLOADING    = "downloading"
    DOWNLOADED     = "downloaded"
    ERROR          = "error"

@dataclass
class AppSettings:
    feeds: list[Feed]
    download_dir: str
    window_geometry: dict | None   # x, y, width, height
    # max_concurrent_downloads は定数5（変更不可のため設定項目から除外）
```

---

## core/rss_parser.py

```python
def fetch_and_parse(url: str) -> list[Episode]:
    """
    指定URLのRSSフィードを取得してEpisodeリストを返す。
    ネットワークエラー時は RSSFetchError を送出。
    不正フォーマット時は RSSParseError を送出。
    """

def parse_feed_from_string(content: str) -> list[Episode]:
    """
    フィードコンテンツ文字列からEpisodeリストを返す（テスト用）。
    """
```

---

## core/duration_parser.py

```python
def parse_duration(raw: str) -> int | None:
    """
    RSSのduration文字列を秒数(int)に変換する。
    対応フォーマット: "3600"（秒）、"60:00"（MM:SS）、"1:00:00"（HH:MM:SS）
    解析不能な場合は None を返す。
    """

def format_duration(seconds: int | None) -> str:
    """
    秒数を表示文字列に変換する。
    例: 5400 → "1時間30分00秒"、2730 → "45分30秒"、45 → "45秒"
    None の場合は "不明" を返す。
    """
```

---

## core/downloader.py

```python
MAX_CONCURRENT_DOWNLOADS = 5  # 固定値

class DownloadManager:
    def __init__(self, max_workers: int = MAX_CONCURRENT_DOWNLOADS): ...

    def enqueue(
        self,
        episode: Episode,
        dest_dir: str,
        on_progress: Callable[[Episode, float], None],  # episode, percent(0-100)
        on_complete: Callable[[Episode, str], None],    # episode, local_path
        on_error: Callable[[Episode, str], None],       # episode, error_message
    ) -> None:
        """ダウンロードキューに追加する。"""

    def cancel(self, episode_id: str) -> None:
        """指定エピソードのダウンロードをキャンセルする。"""

    def cancel_all(self) -> None:
        """すべてのダウンロードをキャンセルする。"""

    def active_count(self) -> int:
        """実行中のダウンロード数を返す。"""
```

---

## core/settings_manager.py

```python
class SettingsManager:
    def load(self) -> AppSettings:
        """設定ファイルを読み込む。存在しない場合はデフォルト値を返す。"""

    def save(self, settings: AppSettings) -> None:
        """設定ファイルに書き込む。"""

    def load_episode_cache(self, feed_id: str) -> list[Episode]:
        """指定フィードのエピソードキャッシュを読み込む。"""

    def save_episode_cache(self, feed_id: str, episodes: list[Episode]) -> None:
        """指定フィードのエピソードキャッシュを書き込む。"""

    def config_dir(self) -> Path:
        """設定ディレクトリのパスを返す（OS依存）。"""
```

---

## gui/main_window.py

```python
class MainWindow(QMainWindow):
    def __init__(self, settings: AppSettings): ...
    def closeEvent(self, event) -> None:
        """ウィンドウ終了時に設定を保存する。"""
    def open_settings_dialog(self) -> None: ...
```

---

## gui/feed_panel.py

```python
class FeedPanel(QWidget):
    feed_selected = Signal(Feed)     # フィード選択時に発行

    def __init__(self, settings_manager: SettingsManager): ...
    def add_feed(self) -> None:      # URLとラベルを入力するダイアログを開く
    def remove_feed(self) -> None:   # 選択中のフィードを削除
    def refresh_feed(self) -> None:  # 選択中のフィードのRSSを再取得
    def load_feeds(self) -> None:    # 設定からフィード一覧を読み込んで表示
```

---

## gui/episode_list.py

```python
class EpisodeList(QWidget):
    download_requested = Signal(list)  # list[Episode]

    def __init__(self): ...
    def set_episodes(self, episodes: list[Episode]) -> None:
        """表示するエピソードを更新する。"""
    def update_episode_status(self, episode_id: str, status: DownloadStatus) -> None:
        """指定エピソードのステータス表示を更新する。"""
    def get_selected_episodes(self) -> list[Episode]: ...
```

---

## gui/download_panel.py

```python
class DownloadPanel(QWidget):
    def __init__(self, download_manager: DownloadManager): ...
    def start_downloads(self, episodes: list[Episode], dest_dir: str) -> None:
        """指定エピソードのダウンロードを開始する。"""
    def on_progress(self, episode: Episode, percent: float) -> None:
        """進捗更新を受け取りUIを更新する。"""
    def on_complete(self, episode: Episode, local_path: str) -> None: ...
    def on_error(self, episode: Episode, message: str) -> None: ...
```

---

## gui/settings_dialog.py

```python
class SettingsDialog(QDialog):
    def __init__(self, settings: AppSettings, settings_manager: SettingsManager): ...
    def accept(self) -> None:
        """OKボタン押下時に設定を保存する。"""
    def browse_download_dir(self) -> None:
        """フォルダ選択ダイアログを開く。"""
```
