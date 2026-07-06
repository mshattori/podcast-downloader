#!/usr/bin/env python3
"""CUI integration test: RSS fetch + episode listing + single MP3 download."""
from __future__ import annotations

import logging
import sys
import tempfile
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger("cui_test")

TEST_RSS_URL = "https://hackerpublicradio.org/hpr_mp3_rss.php?series=47"


def test_rss_fetch() -> list:
    from podcast_downloader.core.rss_parser import fetch_and_parse

    logger.info("=== RSS Fetch Test ===")
    logger.info("URL: %s", TEST_RSS_URL)
    episodes = fetch_and_parse(TEST_RSS_URL)
    logger.info("Episodes found: %d", len(episodes))

    for i, ep in enumerate(episodes[:5]):
        print(f"\n  [{i+1}] {ep.title}")
        print(f"       Published : {ep.published}")
        print(f"       Duration  : {ep.duration_display}")
        print(f"       Audio URL : {ep.audio_url}")

    return episodes


def test_download(episodes: list) -> None:
    import threading

    from podcast_downloader.core.downloader import DownloadManager

    if not episodes:
        logger.warning("No episodes to download — skipping download test")
        return

    ep = episodes[0]
    logger.info("\n=== Download Test ===")
    logger.info("Episode: %s", ep.title)
    logger.info("URL: %s", ep.audio_url)

    done_event = threading.Event()
    results: dict = {}

    last_reported = [0.0]

    def on_progress(episode, percent: float) -> None:
        if percent - last_reported[0] >= 10.0 or percent >= 99.9:
            print(f"  Downloading... {percent:.1f}%", flush=True)
            last_reported[0] = percent

    def on_complete(episode, path: str) -> None:
        print()
        logger.info("Download complete: %s", path)
        results["path"] = path
        results["status"] = "ok"
        done_event.set()

    def on_error(episode, error: str) -> None:
        print()
        logger.error("Download error: %s", error)
        results["status"] = "error"
        results["error"] = error
        done_event.set()

    with tempfile.TemporaryDirectory(prefix="podcast_dl_test_") as tmpdir:
        logger.info("Download dir: %s", tmpdir)
        dm = DownloadManager(max_workers=1)
        dm.enqueue(ep, tmpdir, on_progress, on_complete, on_error)

        finished = done_event.wait(timeout=120)
        if not finished:
            dm.cancel(ep.id)
            logger.error("Download timed out after 120 seconds")
            return

        if results.get("status") == "ok":
            path = Path(results["path"])
            size_mb = path.stat().st_size / (1024 * 1024) if path.exists() else 0
            logger.info("File size: %.2f MB", size_mb)
            logger.info("Download test PASSED")
        else:
            logger.error("Download test FAILED: %s", results.get("error"))


def main() -> None:
    print("=" * 60)
    print("Podcast Downloader — CUI Integration Test")
    print("=" * 60)

    try:
        episodes = test_rss_fetch()
    except Exception as e:
        logger.error("RSS fetch test FAILED: %s", e)
        sys.exit(1)

    if not episodes:
        logger.error("No episodes parsed — check RSS feed")
        sys.exit(1)

    logger.info("RSS fetch test PASSED")

    test_download(episodes)

    print("\n" + "=" * 60)
    print("Test complete")
    print("=" * 60)


if __name__ == "__main__":
    main()
