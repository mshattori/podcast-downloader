from __future__ import annotations

import json
import logging
import os
from pathlib import Path

from platformdirs import user_config_dir

from .models import AppSettings, Episode

logger = logging.getLogger(__name__)

APP_NAME = "podcast-downloader"


class SettingsError(Exception):
    pass


class SettingsManager:
    def __init__(self, config_dir: Path | None = None) -> None:
        self._config_dir = config_dir or Path(user_config_dir(APP_NAME))
        self._settings_path = self._config_dir / "settings.json"
        self._cache_dir = self._config_dir / "cache"

    def config_dir(self) -> Path:
        return self._config_dir

    def log_path(self) -> Path:
        return self._config_dir / "app.log"

    def _ensure_dirs(self) -> None:
        self._config_dir.mkdir(parents=True, exist_ok=True)
        self._cache_dir.mkdir(parents=True, exist_ok=True)

    def load(self) -> AppSettings:
        """Load settings from disk, returning defaults if the file is missing or corrupt."""
        if not self._settings_path.exists():
            logger.info("Settings file not found; using defaults")
            return AppSettings()

        try:
            data = json.loads(self._settings_path.read_text(encoding="utf-8"))
            settings = AppSettings.from_dict(data)
            logger.info("Settings loaded from %s", self._settings_path)
            return settings
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            logger.warning("Failed to load settings, using defaults: %s", e)
            return AppSettings()

    def save(self, settings: AppSettings) -> None:
        """Persist settings to disk using an atomic rename to avoid corruption."""
        try:
            self._ensure_dirs()
            tmp_path = self._settings_path.with_suffix(".json.tmp")
            tmp_path.write_text(
                json.dumps(settings.to_dict(), ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            os.replace(tmp_path, self._settings_path)
            logger.info("Settings saved to %s", self._settings_path)
        except OSError as e:
            logger.error("Failed to save settings: %s", e)
            raise SettingsError(f"Failed to save settings: {e}") from e

    def load_episode_cache(self, feed_id: str) -> list[Episode]:
        """Load the cached episode list for a feed, returning [] on any error."""
        cache_path = self._cache_dir / f"{feed_id}.json"
        if not cache_path.exists():
            return []

        try:
            data = json.loads(cache_path.read_text(encoding="utf-8"))
            episodes = [Episode.from_dict(e) for e in data]
            logger.debug("Episode cache loaded for %s (%d items)", feed_id, len(episodes))
            return episodes
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            logger.warning("Failed to load episode cache for %s: %s", feed_id, e)
            return []

    def save_episode_cache(self, feed_id: str, episodes: list[Episode]) -> None:
        """Persist the episode list for a feed using an atomic rename."""
        try:
            self._ensure_dirs()
            cache_path = self._cache_dir / f"{feed_id}.json"
            tmp_path = cache_path.with_suffix(".json.tmp")
            tmp_path.write_text(
                json.dumps([e.to_dict() for e in episodes], ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            os.replace(tmp_path, cache_path)
            logger.debug("Episode cache saved for %s (%d items)", feed_id, len(episodes))
        except OSError as e:
            logger.error("Failed to save episode cache for %s: %s", feed_id, e)
            raise SettingsError(f"Failed to save episode cache: {e}") from e
