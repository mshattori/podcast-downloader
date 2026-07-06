# NFR Design Patterns — Unit 2: gui

## Pattern 1: Thread-Safe GUI Update (Qt Queued Connection)

**Applies to**: `DownloadPanel`, `FeedPanel`, `EpisodeList`

Worker threads (download, RSS fetch) must never touch Qt widgets directly.
All cross-thread GUI updates are dispatched via `QMetaObject.invokeMethod` with
`Qt.ConnectionType.QueuedConnection`, which posts the call to the main event loop.

```python
# Worker thread side (called from DownloadManager callback)
from PySide6.QtCore import QMetaObject, Qt, Q_ARG

def _on_progress_from_thread(self, episode: Episode, percent: float) -> None:
    QMetaObject.invokeMethod(
        self,
        "_update_progress",           # slot name (decorated with @Slot)
        Qt.ConnectionType.QueuedConnection,
        Q_ARG(str, episode.id),
        Q_ARG(float, percent),
    )

# Main thread side
@Slot(str, float)
def _update_progress(self, episode_id: str, percent: float) -> None:
    self._current_progress_bar.setValue(int(percent))
```

---

## Pattern 2: QThread Worker for RSS Fetch

**Applies to**: `FeedPanel`

RSS fetching runs in a `QThread` subclass that emits signals on completion.
Signals are automatically delivered to the main thread via Qt's event system.

```python
class FetchWorker(QThread):
    finished = Signal(list)   # list[Episode]
    error = Signal(str)

    def __init__(self, url: str, parent=None):
        super().__init__(parent)
        self._url = url

    def run(self) -> None:
        try:
            episodes = rss_parser.fetch_and_parse(self._url)
            self.finished.emit(episodes)
        except Exception as e:
            self.error.emit(str(e))

# Usage in FeedPanel
self._worker = FetchWorker(feed.url, parent=self)
self._worker.finished.connect(self._on_fetch_done)
self._worker.error.connect(self._on_fetch_error)
self._worker.start()
```

---

## Pattern 3: Indeterminate Progress for Unknown Content-Length

**Applies to**: `DownloadPanel`

When the server does not send `Content-Length`, the progress bar switches to
indeterminate (marquee) mode so the user sees activity rather than a stuck bar.

```python
def _update_progress(self, episode_id: str, percent: float) -> None:
    if percent < 0:                       # sentinel for unknown length
        self._current_bar.setRange(0, 0)  # indeterminate
    else:
        self._current_bar.setRange(0, 100)
        self._current_bar.setValue(int(percent))
```

`DownloadManager` passes `percent = -1.0` when `content-length` is absent.

---

## Pattern 4: Window Geometry Guard (Off-Screen Prevention)

**Applies to**: `MainWindow`

Restored geometry is intersected with the available screen rectangle.
If the intersection is empty (window fully off-screen), the default geometry
is used instead.

```python
def _restore_geometry(self, geom: dict) -> None:
    rect = QRect(geom["x"], geom["y"], geom["width"], geom["height"])
    screen = QApplication.primaryScreen().availableGeometry()
    visible = rect.intersected(screen)
    if visible.width() > 100 and visible.height() > 100:
        self.setGeometry(rect)
    else:
        self.resize(1024, 768)
```

---

## Pattern 5: Lazy Episode Load (Cache-First)

**Applies to**: `EpisodeList`, `FeedPanel`

When a feed is selected, the episode table is populated immediately from the
local JSON cache (fast, synchronous). The background RSS refresh that runs at
startup (or on manual refresh) updates the cache and re-populates the table
when done — without blocking the UI.

```
Feed selected
    │
    ├── [sync] load_episode_cache(feed.id) → populate table  (< 200 ms)
    │
    └── [async / already running] FetchWorker
            └── on finished → merge + save + repopulate table
```
