import json
from pathlib import Path

import pytest

from podcast_downloader.core.models import AppSettings, DownloadStatus, Episode, Feed
from podcast_downloader.core.settings_manager import SettingsError, SettingsManager


@pytest.fixture
def tmp_settings(tmp_path: Path) -> SettingsManager:
    return SettingsManager(config_dir=tmp_path)


class TestLoad:
    def test_returns_defaults_when_no_file(self, tmp_settings: SettingsManager) -> None:
        settings = tmp_settings.load()
        assert isinstance(settings, AppSettings)
        assert settings.feeds == []
        assert settings.download_dir != ""

    def test_roundtrip(self, tmp_settings: SettingsManager) -> None:
        feed = Feed(url="https://example.com/feed.rss", label="テストフィード")
        original = AppSettings(feeds=[feed], download_dir="/tmp/podcasts")
        tmp_settings.save(original)

        loaded = tmp_settings.load()
        assert len(loaded.feeds) == 1
        assert loaded.feeds[0].url == feed.url
        assert loaded.feeds[0].label == feed.label
        assert loaded.download_dir == "/tmp/podcasts"

    def test_returns_defaults_on_corrupt_json(self, tmp_settings: SettingsManager) -> None:
        settings_path = tmp_settings.config_dir() / "settings.json"
        settings_path.parent.mkdir(parents=True, exist_ok=True)
        settings_path.write_text("{ invalid json }", encoding="utf-8")

        settings = tmp_settings.load()
        assert isinstance(settings, AppSettings)
        assert settings.feeds == []

    def test_returns_defaults_on_missing_fields(self, tmp_settings: SettingsManager) -> None:
        settings_path = tmp_settings.config_dir() / "settings.json"
        settings_path.parent.mkdir(parents=True, exist_ok=True)
        settings_path.write_text(json.dumps({}), encoding="utf-8")

        settings = tmp_settings.load()
        assert isinstance(settings, AppSettings)


class TestSave:
    def test_creates_file(self, tmp_settings: SettingsManager) -> None:
        tmp_settings.save(AppSettings())
        assert (tmp_settings.config_dir() / "settings.json").exists()

    def test_atomic_write_no_tmp_leftover(self, tmp_settings: SettingsManager) -> None:
        tmp_settings.save(AppSettings())
        tmp_file = tmp_settings.config_dir() / "settings.json.tmp"
        assert not tmp_file.exists()

    def test_creates_parent_dirs(self, tmp_path: Path) -> None:
        nested = tmp_path / "a" / "b" / "c"
        mgr = SettingsManager(config_dir=nested)
        mgr.save(AppSettings())
        assert (nested / "settings.json").exists()


class TestEpisodeCache:
    def _make_episode(self, feed_id: str = "feed-1") -> Episode:
        return Episode(
            feed_id=feed_id,
            guid="ep-guid-1",
            title="テストエピソード",
            audio_url="https://example.com/ep1.mp3",
            duration_seconds=3600,
            duration_display="1時間00分00秒",
        )

    def test_returns_empty_when_no_cache(self, tmp_settings: SettingsManager) -> None:
        assert tmp_settings.load_episode_cache("nonexistent") == []

    def test_roundtrip(self, tmp_settings: SettingsManager) -> None:
        episode = self._make_episode()
        tmp_settings.save_episode_cache("feed-1", [episode])

        loaded = tmp_settings.load_episode_cache("feed-1")
        assert len(loaded) == 1
        assert loaded[0].guid == episode.guid
        assert loaded[0].title == episode.title
        assert loaded[0].duration_seconds == 3600
        assert loaded[0].status == DownloadStatus.NOT_DOWNLOADED

    def test_returns_empty_on_corrupt_cache(self, tmp_settings: SettingsManager) -> None:
        tmp_settings._ensure_dirs()
        cache_path = tmp_settings._cache_dir / "feed-1.json"
        cache_path.write_text("not json", encoding="utf-8")

        result = tmp_settings.load_episode_cache("feed-1")
        assert result == []

    def test_no_tmp_leftover_after_save(self, tmp_settings: SettingsManager) -> None:
        tmp_settings.save_episode_cache("feed-1", [self._make_episode()])
        tmp_file = tmp_settings._cache_dir / "feed-1.json.tmp"
        assert not tmp_file.exists()
