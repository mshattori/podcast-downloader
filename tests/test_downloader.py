from __future__ import annotations

import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from podcast_downloader.core.downloader import DownloadManager, _build_dest_path
from podcast_downloader.core.models import DownloadStatus, Episode


def _make_episode(**kwargs) -> Episode:
    defaults = dict(
        feed_id="feed-1",
        guid="ep-guid-1",
        title="テストエピソード",
        audio_url="https://example.com/ep1.mp3",
        published=datetime(2024, 6, 21, tzinfo=timezone.utc),
    )
    defaults.update(kwargs)
    return Episode(**defaults)


class TestBuildDestPath:
    def test_basic_filename(self, tmp_path: Path) -> None:
        ep = _make_episode()
        path = _build_dest_path(ep, str(tmp_path))
        assert path.name == "20240621_テストエピソード.mp3"
        assert path.parent == tmp_path

    def test_no_published_date(self, tmp_path: Path) -> None:
        ep = _make_episode(published=None)
        path = _build_dest_path(ep, str(tmp_path))
        assert path.name.startswith("00000000_")

    def test_sanitizes_special_chars(self, tmp_path: Path) -> None:
        ep = _make_episode(title='エピソード: "特殊" <文字>')
        path = _build_dest_path(ep, str(tmp_path))
        assert "/" not in path.name
        assert ":" not in path.name
        assert '"' not in path.name
        assert "<" not in path.name
        assert ">" not in path.name

    def test_extension_from_url(self, tmp_path: Path) -> None:
        ep = _make_episode(audio_url="https://example.com/ep.m4a")
        path = _build_dest_path(ep, str(tmp_path))
        assert path.suffix == ".m4a"

    def test_fallback_extension_when_no_suffix(self, tmp_path: Path) -> None:
        ep = _make_episode(audio_url="https://example.com/episode")
        path = _build_dest_path(ep, str(tmp_path))
        assert path.suffix == ".mp3"

    def test_long_filename_truncated(self, tmp_path: Path) -> None:
        ep = _make_episode(title="あ" * 200)
        path = _build_dest_path(ep, str(tmp_path))
        assert len(path.name.encode("utf-8")) <= 255


class TestDownloadManager:
    def _make_response_mock(self, content: bytes = b"audio data") -> MagicMock:
        mock = MagicMock()
        mock.headers = {"content-length": str(len(content))}
        mock.iter_content.return_value = [content]
        mock.raise_for_status.return_value = None
        return mock

    def test_successful_download(self, tmp_path: Path) -> None:
        ep = _make_episode()
        completed = threading.Event()
        results: dict = {}

        def on_complete(episode, path):
            results["episode"] = episode
            results["path"] = path
            completed.set()

        with patch("podcast_downloader.core.downloader.requests.get") as mock_get:
            mock_get.return_value = self._make_response_mock()
            mgr = DownloadManager(max_workers=1)
            mgr.enqueue(ep, str(tmp_path), lambda e, p: None, on_complete, lambda e, m: None)
            completed.wait(timeout=5)

        assert results["episode"].status == DownloadStatus.DOWNLOADED
        assert Path(results["path"]).exists()

    def test_skip_if_file_exists(self, tmp_path: Path) -> None:
        ep = _make_episode()
        dest = _build_dest_path(ep, str(tmp_path))
        dest.write_bytes(b"already downloaded")

        completed = threading.Event()
        results: dict = {}

        def on_complete(episode, path):
            results["skipped"] = True
            completed.set()

        with patch("podcast_downloader.core.downloader.requests.get") as mock_get:
            mgr = DownloadManager(max_workers=1)
            mgr.enqueue(ep, str(tmp_path), lambda e, p: None, on_complete, lambda e, m: None)
            completed.wait(timeout=5)

        # HTTPリクエストは発生しない
        mock_get.assert_not_called()
        assert results.get("skipped")
        assert ep.status == DownloadStatus.DOWNLOADED

    def test_error_cleans_up_tmp_file(self, tmp_path: Path) -> None:
        ep = _make_episode()
        error_event = threading.Event()

        def on_error(episode, msg):
            error_event.set()

        with patch("podcast_downloader.core.downloader.requests.get") as mock_get:
            mock_get.side_effect = Exception("ネットワークエラー")
            mgr = DownloadManager(max_workers=1)
            mgr.enqueue(ep, str(tmp_path), lambda e, p: None, lambda e, p: None, on_error)
            error_event.wait(timeout=5)

        assert ep.status == DownloadStatus.ERROR
        # .tmp ファイルが残っていないこと
        tmp_files = list(tmp_path.glob("*.tmp"))
        assert tmp_files == []

    def test_cancel_sets_not_downloaded(self, tmp_path: Path) -> None:
        ep = _make_episode()
        cancelled = threading.Event()

        def slow_iter():
            # キャンセルを待つ
            time.sleep(0.05)
            yield b""

        mock_resp = MagicMock()
        mock_resp.headers = {"content-length": "1000"}
        mock_resp.iter_content.return_value = slow_iter()
        mock_resp.raise_for_status.return_value = None

        with patch("podcast_downloader.core.downloader.requests.get", return_value=mock_resp):
            mgr = DownloadManager(max_workers=1)
            mgr.enqueue(ep, str(tmp_path), lambda e, p: None, lambda e, p: None, lambda e, m: None)
            # 少し待ってからキャンセル
            time.sleep(0.01)
            mgr.cancel(ep.id)
            time.sleep(0.2)

        assert ep.status in (DownloadStatus.NOT_DOWNLOADED, DownloadStatus.ERROR)

    def test_progress_callback_called(self, tmp_path: Path) -> None:
        ep = _make_episode()
        progress_values: list[float] = []
        completed = threading.Event()

        mock_resp = MagicMock()
        mock_resp.headers = {"content-length": "20"}
        mock_resp.iter_content.return_value = [b"chunk1234567890abcde"]
        mock_resp.raise_for_status.return_value = None

        with patch("podcast_downloader.core.downloader.requests.get", return_value=mock_resp):
            mgr = DownloadManager(max_workers=1)
            mgr.enqueue(
                ep, str(tmp_path),
                lambda e, p: progress_values.append(p),
                lambda e, path: completed.set(),
                lambda e, m: completed.set(),
            )
            completed.wait(timeout=5)

        assert len(progress_values) > 0
        assert progress_values[-1] == pytest.approx(100.0)
