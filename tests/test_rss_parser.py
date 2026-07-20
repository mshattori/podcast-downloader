from pathlib import Path

import pytest

from podcast_downloader.core.models import DownloadStatus
from podcast_downloader.core.rss_parser import (
    RSSFetchError,
    RSSParseError,
    fetch_and_parse,
    merge_episodes,
    parse_feed_from_string,
)

VALID_RSS = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd">
  <channel>
    <title>テストポッドキャスト</title>
    <item>
      <title>エピソード1</title>
      <guid>ep-guid-1</guid>
      <pubDate>Mon, 21 Jun 2024 10:00:00 +0000</pubDate>
      <description>テストの概要</description>
      <itunes:duration>1:30:00</itunes:duration>
      <enclosure url="https://example.com/ep1.mp3" type="audio/mpeg" length="1000"/>
    </item>
    <item>
      <title>エピソード2</title>
      <guid>ep-guid-2</guid>
      <enclosure url="https://example.com/ep2.mp3" type="audio/mpeg" length="2000"/>
    </item>
  </channel>
</rss>"""

NO_AUDIO_RSS = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <item>
      <title>音声なしエピソード</title>
      <guid>ep-no-audio</guid>
    </item>
  </channel>
</rss>"""

DUPLICATE_GUID_RSS = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <item>
      <title>エピソードA</title>
      <guid>same-guid</guid>
      <enclosure url="https://example.com/a.mp3" type="audio/mpeg" length="100"/>
    </item>
    <item>
      <title>エピソードB</title>
      <guid>same-guid</guid>
      <enclosure url="https://example.com/b.mp3" type="audio/mpeg" length="200"/>
    </item>
  </channel>
</rss>"""


class TestParseFeedFromString:
    def test_parses_valid_feed(self) -> None:
        episodes = parse_feed_from_string(VALID_RSS)
        assert len(episodes) == 2

    def test_episode_fields(self) -> None:
        episodes = parse_feed_from_string(VALID_RSS)
        ep = episodes[0]
        assert ep.title == "エピソード1"
        assert ep.guid == "ep-guid-1"
        assert ep.audio_url == "https://example.com/ep1.mp3"
        assert ep.duration_seconds == 5400
        assert ep.duration_display == "1時間30分00秒"
        assert ep.description == "テストの概要"
        assert ep.podcast_title == "テストポッドキャスト"
        assert ep.published is not None

    def test_excludes_episodes_without_audio_url(self) -> None:
        episodes = parse_feed_from_string(NO_AUDIO_RSS)
        assert episodes == []

    def test_deduplicates_by_guid(self) -> None:
        episodes = parse_feed_from_string(DUPLICATE_GUID_RSS)
        assert len(episodes) == 1
        assert episodes[0].title == "エピソードA"

    def test_missing_title_uses_default(self) -> None:
        rss = """<rss version="2.0"><channel><item>
            <guid>g1</guid>
            <enclosure url="https://example.com/ep.mp3" type="audio/mpeg" length="100"/>
        </item></channel></rss>"""
        episodes = parse_feed_from_string(rss)
        assert episodes[0].title == "（タイトルなし）"

    def test_missing_description_uses_empty_string(self) -> None:
        episodes = parse_feed_from_string(VALID_RSS)
        ep = next(e for e in episodes if e.guid == "ep-guid-2")
        assert ep.description == ""

    def test_missing_published_is_none(self) -> None:
        episodes = parse_feed_from_string(VALID_RSS)
        ep = next(e for e in episodes if e.guid == "ep-guid-2")
        assert ep.published is None

    def test_missing_duration_shows_unknown(self) -> None:
        episodes = parse_feed_from_string(VALID_RSS)
        ep = next(e for e in episodes if e.guid == "ep-guid-2")
        assert ep.duration_seconds is None
        assert ep.duration_display == "不明"

    def test_initial_status_is_not_downloaded(self) -> None:
        episodes = parse_feed_from_string(VALID_RSS)
        for ep in episodes:
            assert ep.status == DownloadStatus.NOT_DOWNLOADED


class TestFetchAndParse:
    def test_network_error_raises_rss_fetch_error(self, mocker) -> None:
        import requests as req
        mocker.patch("podcast_downloader.core.rss_parser.requests.get",
                     side_effect=req.ConnectionError("connection failed"))
        with pytest.raises(RSSFetchError, match="Failed to fetch"):
            fetch_and_parse("https://example.com/feed.rss")

    def test_http_error_raises_rss_fetch_error(self, mocker) -> None:
        import requests as req
        mock_resp = mocker.MagicMock()
        mock_resp.raise_for_status.side_effect = req.HTTPError("404 Not Found")
        mocker.patch("podcast_downloader.core.rss_parser.requests.get", return_value=mock_resp)
        with pytest.raises(RSSFetchError):
            fetch_and_parse("https://example.com/feed.rss")

    def test_successful_fetch_returns_episodes(self, mocker) -> None:
        mock_resp = mocker.MagicMock()
        mock_resp.text = VALID_RSS
        mock_resp.raise_for_status.return_value = None
        mocker.patch("podcast_downloader.core.rss_parser.requests.get", return_value=mock_resp)
        episodes = fetch_and_parse("https://example.com/feed.rss")
        assert len(episodes) == 2


class TestMergeEpisodes:
    def _ep(self, guid: str, status=DownloadStatus.NOT_DOWNLOADED, title: str = "タイトル"):
        from podcast_downloader.core.models import Episode
        return Episode(feed_id="f1", guid=guid, title=title,
                       audio_url=f"https://example.com/{guid}.mp3", status=status)

    def test_new_episodes_added(self) -> None:
        merged = merge_episodes([], [self._ep("new-1")])
        assert len(merged) == 1

    def test_existing_status_preserved(self) -> None:
        cached = [self._ep("ep-1", status=DownloadStatus.DOWNLOADED)]
        fetched = [self._ep("ep-1", title="新しいタイトル")]
        fetched[0].podcast_title = "新しい番組名"
        merged = merge_episodes(cached, fetched)
        assert merged[0].status == DownloadStatus.DOWNLOADED
        assert merged[0].title == "新しいタイトル"
        assert merged[0].podcast_title == "新しい番組名"

    def test_all_fetched_episodes_in_result(self) -> None:
        cached = [self._ep("ep-1")]
        fetched = [self._ep("ep-1"), self._ep("ep-2")]
        merged = merge_episodes(cached, fetched)
        assert len(merged) == 2

    def test_retains_downloaded_episode_removed_from_feed(self, tmp_path: Path) -> None:
        downloaded_file = tmp_path / "ep-old.mp3"
        downloaded_file.write_bytes(b"audio")
        old = self._ep("ep-old", status=DownloadStatus.DOWNLOADED)
        old.local_path = str(downloaded_file)

        merged = merge_episodes([old], [self._ep("ep-new")])

        assert [ep.guid for ep in merged] == ["ep-new", "ep-old"]
        assert merged[1].status == DownloadStatus.DOWNLOADED
        assert merged[1].local_path == str(downloaded_file)

    def test_drops_cached_episode_removed_from_feed_when_file_missing(self) -> None:
        old = self._ep("ep-old", status=DownloadStatus.DOWNLOADED)
        old.local_path = "/path/to/missing.mp3"

        merged = merge_episodes([old], [self._ep("ep-new")])

        assert [ep.guid for ep in merged] == ["ep-new"]
