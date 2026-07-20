from __future__ import annotations

import logging
import os
import re
import threading
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urlparse

import requests

from .models import DownloadStatus, Episode

logger = logging.getLogger(__name__)

MAX_CONCURRENT_DOWNLOADS = 5
CHUNK_SIZE = 8192
MAX_COMMENT_CHARS = 500


class DownloadError(Exception):
    pass


@dataclass
class _DownloadTask:
    episode: Episode
    dest_dir: str
    on_progress: Callable[[Episode, float], None]
    on_complete: Callable[[Episode, str], None]
    on_error: Callable[[Episode, str], None]
    cancel_event: threading.Event = field(default_factory=threading.Event)


class DownloadManager:
    def __init__(self, max_workers: int = MAX_CONCURRENT_DOWNLOADS) -> None:
        self._semaphore = threading.Semaphore(max_workers)
        self._lock = threading.Lock()
        self._tasks: dict[str, _DownloadTask] = {}

    def enqueue(
        self,
        episode: Episode,
        dest_dir: str,
        on_progress: Callable[[Episode, float], None],
        on_complete: Callable[[Episode, str], None],
        on_error: Callable[[Episode, str], None],
    ) -> None:
        """Add an episode to the download queue and start a worker thread."""
        task = _DownloadTask(
            episode=episode,
            dest_dir=dest_dir,
            on_progress=on_progress,
            on_complete=on_complete,
            on_error=on_error,
        )
        with self._lock:
            self._tasks[episode.id] = task

        thread = threading.Thread(
            target=self._run,
            args=(task,),
            daemon=True,
            name=f"download-{episode.id[:8]}",
        )
        thread.start()

    def cancel(self, episode_id: str) -> None:
        """Signal the worker for *episode_id* to stop at the next chunk boundary."""
        with self._lock:
            task = self._tasks.get(episode_id)
        if task:
            task.cancel_event.set()
            logger.info("Cancellation requested for episode %s", episode_id)

    def cancel_all(self) -> None:
        """Signal all active workers to stop."""
        with self._lock:
            tasks = list(self._tasks.values())
        for task in tasks:
            task.cancel_event.set()
        logger.info("Cancellation requested for all downloads")

    def active_count(self) -> int:
        """Return the number of currently tracked download tasks."""
        with self._lock:
            return len(self._tasks)

    def _run(self, task: _DownloadTask) -> None:
        episode = task.episode
        with self._semaphore:  # blocks until a slot is free
            try:
                self._download(task)
            finally:
                with self._lock:
                    self._tasks.pop(episode.id, None)

    def _download(self, task: _DownloadTask) -> None:
        episode = task.episode
        dest_path = _build_dest_path(episode, task.dest_dir)

        # Skip if the file already exists (BR-05-x)
        if dest_path.exists():
            logger.info("File already exists, skipping: %s", dest_path)
            _tag_downloaded_file(dest_path, episode)
            episode.status = DownloadStatus.DOWNLOADED
            episode.local_path = str(dest_path)
            task.on_complete(episode, str(dest_path))
            return

        episode.status = DownloadStatus.DOWNLOADING
        tmp_path = dest_path.with_suffix(dest_path.suffix + ".tmp")

        try:
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            response = requests.get(episode.audio_url, stream=True, timeout=30)
            response.raise_for_status()

            total = int(response.headers.get("content-length", 0))
            downloaded = 0

            with tmp_path.open("wb") as f:
                for chunk in response.iter_content(chunk_size=CHUNK_SIZE):
                    if task.cancel_event.is_set():
                        logger.info("Download cancelled: %s", episode.id)
                        episode.status = DownloadStatus.NOT_DOWNLOADED
                        return

                    f.write(chunk)
                    downloaded += len(chunk)

                    if total > 0:
                        percent = downloaded / total * 100
                        task.on_progress(episode, percent)

            os.replace(tmp_path, dest_path)
            _tag_downloaded_file(dest_path, episode)
            episode.status = DownloadStatus.DOWNLOADED
            episode.local_path = str(dest_path)
            logger.info("Download complete: %s", dest_path)
            task.on_complete(episode, str(dest_path))

        except Exception as e:
            episode.status = DownloadStatus.ERROR
            logger.error("Download error for episode %s: %s", episode.id, e)
            task.on_error(episode, str(e))
        finally:
            # Remove the incomplete temp file on error or cancellation (BR-06-1)
            if tmp_path.exists():
                try:
                    tmp_path.unlink()
                except OSError:
                    pass


def _build_dest_path(episode: Episode, dest_dir: str) -> Path:
    """Build the destination file path for an episode download (BR-04-x)."""
    date_str = episode.published.strftime("%Y%m%d") if episode.published else "00000000"

    parsed = urlparse(episode.audio_url)
    suffix = Path(parsed.path).suffix
    # When the URL path has no audio extension (e.g. ccdn.php?filename=...mp3),
    # try to derive the extension from a 'filename' query param.
    if not suffix or suffix.lower() not in {".mp3", ".ogg", ".opus", ".m4a", ".flac", ".wav", ".aac"}:
        from urllib.parse import parse_qs
        qs = parse_qs(parsed.query)
        fname_param = qs.get("filename", [None])[0]
        if fname_param:
            suffix = Path(fname_param).suffix
    if not suffix:
        suffix = ".mp3"

    raw_name = f"{date_str}_{episode.title}{suffix}"
    sanitized = re.sub(r'[/\\:*?"<>|]', "_", raw_name)

    # Enforce 255-byte filename limit (BR-04-4)
    encoded = sanitized.encode("utf-8")
    if len(encoded) > 255:
        max_title_bytes = 255 - len(date_str.encode()) - len(suffix.encode()) - 2
        title_bytes = episode.title.encode("utf-8")[:max_title_bytes]
        truncated_title = title_bytes.decode("utf-8", errors="ignore")
        sanitized = re.sub(r'[/\\:*?"<>|]', "_", f"{date_str}_{truncated_title}{suffix}")

    return Path(dest_dir) / sanitized


def _tag_downloaded_file(path: Path, episode: Episode) -> None:
    """Write audio metadata for supported downloaded files."""
    if path.suffix.lower() != ".mp3":
        return

    try:
        _write_mp3_metadata(path, episode)
    except Exception as e:
        logger.warning("Failed to write MP3 metadata for %s: %s", path, e)


def _write_mp3_metadata(path: Path, episode: Episode) -> None:
    from mutagen.id3 import COMM, TALB, TCON, TDRC, TIT2, TPE1, TPE2, ID3, ID3NoHeaderError

    try:
        tags = ID3(path)
    except ID3NoHeaderError:
        tags = ID3()

    tags.setall("TIT2", [TIT2(encoding=3, text=episode.title)])

    album = episode.podcast_title.strip()
    if album:
        tags.setall("TALB", [TALB(encoding=3, text=album)])
        tags.setall("TPE1", [TPE1(encoding=3, text=album)])
        tags.setall("TPE2", [TPE2(encoding=3, text=album)])

    if episode.published:
        tags.setall("TDRC", [TDRC(encoding=3, text=episode.published.date().isoformat())])

    tags.setall("TCON", [TCON(encoding=3, text="Podcast")])

    comment = _metadata_comment(episode.description)
    if comment:
        tags.delall("COMM")
        tags.add(COMM(encoding=3, lang="eng", desc="", text=comment))

    tags.save(path, v2_version=3)


def _plain_text(value: str) -> str:
    return re.sub(r"<[^>]+>", "", value)


def _metadata_comment(value: str) -> str:
    comment = re.sub(r"\s+", " ", _plain_text(value)).strip()
    if len(comment) <= MAX_COMMENT_CHARS:
        return comment
    return comment[: MAX_COMMENT_CHARS - 3].rstrip() + "..."
