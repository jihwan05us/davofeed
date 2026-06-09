import datetime
from pathlib import Path

import yaml
from tqdm import tqdm

from .utils.youtube import check_live_status, fetch_entries, get_channel_id

_CHANNELS_DIR = Path(__file__).parent.parent.parent / "channels"


def load_channels() -> dict[str, dict[str, dict[str, str]]]:
    """Returns {filename_stem: {category: {handle: display_name}}} for all channels/*.yaml.
    Supports both list format (handle only) and dict format (handle: display_name).
    """
    result = {}
    for path in sorted(_CHANNELS_DIR.glob("*.yaml")):
        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        categories = {}
        for k, v in data.items():
            if isinstance(v, dict):
                categories[k] = {handle: name for handle, name in v.items()}
            elif isinstance(v, list):
                categories[k] = {handle: handle for handle in v}
        result[path.stem] = categories
    return result


def _parse_dt(entry) -> datetime.datetime:
    pp = entry.get("published_parsed")
    if pp:
        return datetime.datetime(*pp[:6])
    return datetime.datetime.min


def _entry_to_video(entry, display_name: str) -> dict:
    thumbnail = ""
    if "media_thumbnail" in entry and entry.media_thumbnail:
        thumbnail = entry.media_thumbnail[0]["url"]
    link = entry.link
    return {
        "title": entry.title,
        "link": link,
        "video_id": entry.get("yt_videoid", ""),
        "author": entry.get("author", display_name),
        "published": _parse_dt(entry),
        "thumbnail": thumbnail,
        "is_short": "/shorts/" in link,
        "is_live": False,
    }


def collect_by_date(
    date: datetime.date,
) -> dict[str, dict[str, dict]]:
    """
    Returns {
        filename_stem: {
            category: {
                "videos": [video, ...],
                "all_handles": [handle, ...],
                "silent_handles": [handle, ...],
                "error_handles": [(handle, reason), ...],
            }
        }
    }
    Videos are filtered to those published on `date` (UTC date).
    Categories with no videos are still included in the result but
    flagged so the template can skip rendering them.
    """
    channels = load_channels()
    result = {}

    for stem, categories in channels.items():
        result[stem] = {}
        all_handles = [h for handles in categories.values() for h in handles.keys()]

        with tqdm(
            total=len(all_handles),
            desc=stem,
            ncols=70,
            leave=True,
        ) as bar:
            for category, handles in categories.items():
                videos = []
                silent = []
                errors = []

                for handle, display_name in handles.items():
                    bar.set_postfix_str(handle[:20], refresh=True)
                    channel_id, err = get_channel_id(handle)

                    if not channel_id:
                        errors.append((display_name, err))
                        bar.update(1)
                        continue

                    entries = fetch_entries(channel_id)
                    day_videos = [
                        _entry_to_video(e, display_name)
                        for e in entries
                        if _parse_dt(e).date() == date
                    ]

                    if day_videos:
                        videos.extend(day_videos)
                    else:
                        silent.append(display_name)

                    bar.update(1)

                if videos:
                    live_ids = check_live_status([v["video_id"] for v in videos if v["video_id"]])
                    for v in videos:
                        v["is_live"] = v["video_id"] in live_ids

                videos.sort(key=lambda v: v["published"], reverse=True)
                result[stem][category] = {
                    "videos": videos,
                    "all_handles": handles,
                    "silent_handles": silent,
                    "error_handles": errors,
                }

    return result
