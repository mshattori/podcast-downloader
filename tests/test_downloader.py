from __future__ import annotations

import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from podcast_downloader.core.downloader import (
    DownloadManager,
    _build_dest_path,
    _metadata_comment,
    _plain_text,
    _write_mp3_metadata,
)
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

        with (
            patch("podcast_downloader.core.downloader.requests.get") as mock_get,
            patch("podcast_downloader.core.downloader._tag_downloaded_file") as mock_tag,
        ):
            mock_get.return_value = self._make_response_mock()
            mgr = DownloadManager(max_workers=1)
            mgr.enqueue(ep, str(tmp_path), lambda e, p: None, on_complete, lambda e, m: None)
            completed.wait(timeout=5)

        assert results["episode"].status == DownloadStatus.DOWNLOADED
        assert Path(results["path"]).exists()
        mock_tag.assert_called_once_with(Path(results["path"]), ep)

    def test_skip_if_file_exists(self, tmp_path: Path) -> None:
        ep = _make_episode()
        dest = _build_dest_path(ep, str(tmp_path))
        dest.write_bytes(b"already downloaded")

        completed = threading.Event()
        results: dict = {}

        def on_complete(episode, path):
            results["skipped"] = True
            completed.set()

        with (
            patch("podcast_downloader.core.downloader.requests.get") as mock_get,
            patch("podcast_downloader.core.downloader._tag_downloaded_file") as mock_tag,
        ):
            mgr = DownloadManager(max_workers=1)
            mgr.enqueue(ep, str(tmp_path), lambda e, p: None, on_complete, lambda e, m: None)
            completed.wait(timeout=5)

        # HTTPリクエストは発生しない
        mock_get.assert_not_called()
        mock_tag.assert_called_once_with(dest, ep)
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


class TestMetadataHelpers:
    def test_plain_text_strips_html_tags(self) -> None:
        assert _plain_text("<p>説明<br>本文</p>") == "説明本文"

    def test_metadata_comment_collapses_and_truncates_text(self) -> None:
        comment = _metadata_comment(f"<p>{'長い説明 ' * 200}</p>")

        assert len(comment) == 500
        assert comment.endswith("...")
        assert "\n" not in comment

    def test_write_mp3_metadata(self, tmp_path: Path) -> None:
        pytest.importorskip("mutagen")
        from mutagen.id3 import ID3

        path = tmp_path / "episode.mp3"
        path.write_bytes(b"audio data")
        episode = _make_episode(
            title="エピソードタイトル",
            podcast_title="番組タイトル",
            description="<p>概要</p>",
        )

        _write_mp3_metadata(path, episode)

        tags = ID3(path)
        assert tags["TIT2"].text == ["エピソードタイトル"]
        assert tags["TALB"].text == ["番組タイトル"]
        assert tags["TPE1"].text == ["番組タイトル"]
        assert tags["TPE2"].text == ["番組タイトル"]
        assert tags["TCON"].text == ["Podcast"]
        assert tags["COMM::eng"].text == ["概要"]
