import re

import feedparser
import requests

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
