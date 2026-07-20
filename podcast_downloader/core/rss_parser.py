from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path

import feedparser
import requests

from .duration_parser import format_duration, parse_duration
from .models import DownloadStatus, Episode

logger = logging.getLogger(__name__)

RSS_FETCH_TIMEOUT = 30


class RSSFetchError(Exception):
    pass


class RSSParseError(Exception):
    pass


def fetch_and_parse(url: str) -> list[Episode]:
    """Fetch an RSS feed from *url* and return a list of Episodes."""
    logger.info("Fetching RSS feed: %s", url)
    try:
        response = requests.get(url, timeout=RSS_FETCH_TIMEOUT)
        response.raise_for_status()
    except requests.RequestException as e:
        logger.error("Failed to fetch RSS feed (%s): %s", url, e)
        raise RSSFetchError(f"Failed to fetch RSS feed: {e}") from e

    return parse_feed_from_string(response.text)


def parse_feed_from_string(content: str) -> list[Episode]:
    """Parse a feed from a raw string and return a deduplicated list of Episodes."""
    feed = feedparser.parse(content)

    if feed.bozo and not feed.entries:
        raise RSSParseError(f"Failed to parse RSS feed: {feed.bozo_exception}")

    episodes: list[Episode] = []
    seen_guids: set[str] = set()
    podcast_title = getattr(feed.feed, "title", "") or ""

    for entry in feed.entries:
        episode = _entry_to_episode(entry, podcast_title=podcast_title)
        if episode is None:
            continue
        if episode.guid in seen_guids:
            logger.debug("Skipping duplicate guid: %s", episode.guid)
            continue
        seen_guids.add(episode.guid)
        episodes.append(episode)

    logger.info("Parsed %d episodes", len(episodes))
    return episodes


def _entry_to_episode(
    entry: feedparser.FeedParserDict,
    podcast_title: str = "",
) -> Episode | None:
    # Exclude entries with no audio enclosure (BR-02-1)
    audio_url = _extract_audio_url(entry)
    if not audio_url:
        return None

    guid = getattr(entry, "id", None) or audio_url
    title = getattr(entry, "title", None) or "（タイトルなし）"  # BR-02-2: default when missing
    description = getattr(entry, "summary", None) or getattr(entry, "description", None) or ""  # BR-02-4
    published = _parse_published(entry)  # BR-02-3: None when missing

    raw_duration = _extract_duration_raw(entry)
    duration_seconds = parse_duration(raw_duration)

    return Episode(
        feed_id="",  # set by the caller after associating with a Feed
        guid=guid,
        title=title,
        audio_url=audio_url,
        published=published,
        duration_seconds=duration_seconds,
        duration_display=format_duration(duration_seconds),
        description=description,
        podcast_title=podcast_title,
    )


def _extract_audio_url(entry: feedparser.FeedParserDict) -> str | None:
    for enclosure in getattr(entry, "enclosures", []):
        url = getattr(enclosure, "url", None) or enclosure.get("url", "")
        if url:
            return url
    # Fall back to links with an audio/* MIME type
    for link in getattr(entry, "links", []):
        mime = link.get("type", "")
        if mime.startswith("audio/"):
            href = link.get("href", "")
            if href:
                return href
    return None


def _parse_published(entry: feedparser.FeedParserDict) -> datetime | None:
    published_parsed = getattr(entry, "published_parsed", None)
    if published_parsed is None:
        published_parsed = getattr(entry, "updated_parsed", None)
    if published_parsed is None:
        return None
    try:
        return datetime(*published_parsed[:6], tzinfo=timezone.utc)
    except (TypeError, ValueError):
        return None


def _extract_duration_raw(entry: feedparser.FeedParserDict) -> str | None:
    # Prefer itunes:duration; fall back to the generic duration field
    itunes_duration = getattr(entry, "itunes_duration", None)
    if itunes_duration:
        return str(itunes_duration)
    duration = getattr(entry, "duration", None)
    if duration:
        return str(duration)
    return None


def merge_episodes(
    cached: list[Episode],
    fetched: list[Episode],
) -> list[Episode]:
    """Merge freshly fetched episodes into the cached list using guid as the key.

    Existing episodes retain their *status* and *local_path*; all other
    metadata fields are updated from the newly fetched data.
    New episodes (not in cache) are appended with NOT_DOWNLOADED status.
    Cached downloaded episodes whose files still exist are retained even when
    they are no longer present in the current feed window.
    """
    cached_by_guid = {ep.guid: ep for ep in cached}
    fetched_guids = {ep.guid for ep in fetched}
    merged: list[Episode] = []

    for new_ep in fetched:
        if new_ep.guid in cached_by_guid:
            existing = cached_by_guid[new_ep.guid]
            # Update metadata while preserving download state
            existing.title = new_ep.title
            existing.published = new_ep.published
            existing.duration_seconds = new_ep.duration_seconds
            existing.duration_display = new_ep.duration_display
            existing.description = new_ep.description
            existing.podcast_title = new_ep.podcast_title
            existing.audio_url = new_ep.audio_url
            merged.append(existing)
        else:
            merged.append(new_ep)

    for existing in cached:
        if existing.guid in fetched_guids:
            continue
        if _has_downloaded_file(existing):
            existing.status = DownloadStatus.DOWNLOADED
            merged.append(existing)

    return merged


def _has_downloaded_file(episode: Episode) -> bool:
    if not episode.local_path:
        return False
    return Path(episode.local_path).is_file()
