import os
import re

import feedparser
import requests
from dotenv import load_dotenv

load_dotenv()

_API_KEY = os.getenv("YOUTUBE_API_KEY")
_API_URL = "https://www.googleapis.com/youtube/v3/videos"

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "Anonymously-Generated-UA/1.0"
    ),
    "Accept-Language": "ko-KR,ko;q=0.9",
}

_ID_PATTERNS = [
    r'"externalId"\s*:\s*"([^"]+)"',
    r'"browseId"\s*:\s*"(UC[^"]+)"',
    r'"channelId"\s*:\s*"([^"]+)"',
]


def get_channel_id(handle: str) -> tuple[str | None, str | None]:
    if not handle.startswith("@"):
        handle = "@" + handle
    try:
        resp = requests.get(
            f"https://www.youtube.com/{handle}", headers=_HEADERS, timeout=10
        )
        resp.raise_for_status()
    except Exception as e:
        return None, str(e)

    for pattern in _ID_PATTERNS:
        m = re.search(pattern, resp.text)
        if m:
            return m.group(1), None

    return None, f"channel ID not found for {handle}"


def fetch_entries(channel_id: str) -> list[dict]:
    rss_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
    feed = feedparser.parse(rss_url)
    return feed.entries


def check_live_status(video_ids: list[str]) -> set[str]:
    """Returns set of video IDs that are live stream recordings."""
    if not _API_KEY or not video_ids:
        return set()

    live_ids = set()
    for i in range(0, len(video_ids), 50):
        batch = video_ids[i:i + 50]
        try:
            resp = requests.get(
                _API_URL,
                params={
                    "part": "liveStreamingDetails",
                    "id": ",".join(batch),
                    "key": _API_KEY,
                },
                timeout=10,
            )
            resp.raise_for_status()
            for item in resp.json().get("items", []):
                if "liveStreamingDetails" in item:
                    live_ids.add(item["id"])
        except Exception as e:
            print(f"  [warn] live status check failed: {e}")

    return live_ids
