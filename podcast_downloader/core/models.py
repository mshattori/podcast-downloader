from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class DownloadStatus(Enum):
    NOT_DOWNLOADED = "not_downloaded"
    DOWNLOADING = "downloading"
    DOWNLOADED = "downloaded"
    ERROR = "error"


@dataclass
class Feed:
    url: str
    label: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    last_fetched: datetime | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "url": self.url,
            "label": self.label,
            "last_fetched": self.last_fetched.isoformat() if self.last_fetched else None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Feed:
        last_fetched = None
        if data.get("last_fetched"):
            last_fetched = datetime.fromisoformat(data["last_fetched"])
        return cls(
            id=data["id"],
            url=data["url"],
            label=data["label"],
            last_fetched=last_fetched,
        )


@dataclass
class Episode:
    feed_id: str
    guid: str
    title: str
    audio_url: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    published: datetime | None = None
    duration_seconds: int | None = None
    duration_display: str = "不明"
    description: str = ""
    podcast_title: str = ""
    status: DownloadStatus = DownloadStatus.NOT_DOWNLOADED
    local_path: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "feed_id": self.feed_id,
            "guid": self.guid,
            "title": self.title,
            "audio_url": self.audio_url,
            "published": self.published.isoformat() if self.published else None,
            "duration_seconds": self.duration_seconds,
            "duration_display": self.duration_display,
            "description": self.description,
            "podcast_title": self.podcast_title,
            "status": self.status.value,
            "local_path": self.local_path,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Episode:
        published = None
        if data.get("published"):
            published = datetime.fromisoformat(data["published"])
        return cls(
            id=data["id"],
            feed_id=data["feed_id"],
            guid=data["guid"],
            title=data["title"],
            audio_url=data["audio_url"],
            published=published,
            duration_seconds=data.get("duration_seconds"),
            duration_display=data.get("duration_display", "不明"),
            description=data.get("description", ""),
            podcast_title=data.get("podcast_title", ""),
            status=DownloadStatus(data.get("status", DownloadStatus.NOT_DOWNLOADED.value)),
            local_path=data.get("local_path"),
        )


@dataclass
class AppSettings:
    feeds: list[Feed] = field(default_factory=list)
    download_dir: str = ""
    window_geometry: dict[str, int] | None = None

    def __post_init__(self) -> None:
        if not self.download_dir:
            import os
            self.download_dir = os.path.expanduser("~/Downloads")

    def to_dict(self) -> dict[str, Any]:
        return {
            "feeds": [f.to_dict() for f in self.feeds],
            "download_dir": self.download_dir,
            "window_geometry": self.window_geometry,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AppSettings:
        feeds = [Feed.from_dict(f) for f in data.get("feeds", [])]
        return cls(
            feeds=feeds,
            download_dir=data.get("download_dir", ""),
            window_geometry=data.get("window_geometry"),
        )
