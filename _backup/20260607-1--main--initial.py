import re
import feedparser
import requests


def get_channel_id_from_handle(handle):
    """채널 핸들(@username)에서 채널 ID 추출"""
    if not handle.startswith("@"):
        handle = "@" + handle

    channel_url = f"https://www.youtube.com/{handle}"

    # ⭐ 핵심 1: 봇 차단을 막기 위해 브라우저인 척 속이는 헤더 추가
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "Anonymously-Generated-UA/1.0"
        ),
        "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
    }

    try:
        response = requests.get(channel_url, headers=headers, timeout=10)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"네트워크 오류 또는 잘못된 URL입니다: {e}")
        return None

    # ⭐ 핵심 2: 현재 유튜브 HTML 구조에서 가장 정확하게 채널ID를 찾는 패턴들
    # 1순위: externalId (가장 확실함)
    match = re.search(r'"externalId"\s*:\s*"([^"]+)"', response.text)
    if match:
        return match.group(1)

    # 2순위: browseId (채널 ID는 무조건 UC로 시작함)
    match = re.search(r'"browseId"\s*:\s*"(UC[^"]+)"', response.text)
    if match:
        return match.group(1)

    # 3순위: 기존 채널ID 패턴 보완
    match = re.search(r'"channelId"\s*:\s*"([^"]+)"', response.text)
    if match:
        return match.group(1)

    print("채널 ID를 찾을 수 없습니다. 유튜브 HTML 구조가 변경되었을 수 있습니다.")
    return None


def print_latest_videos(channel_id):
    """채널 ID를 이용해 최신 동영상 목록 출력"""
    if not channel_id:
        print("유효한 채널 ID가 없어 영상을 가져올 수 없습니다.")
        return

    rss_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
    feed = feedparser.parse(rss_url)

    if not feed.entries:
        print("영상을 찾을 수 없거나 올바르지 않은 RSS 피드입니다.")
        return

    print(f"\n📺 [최신 동영상 목록] (총 {len(feed.entries)}개)")
    print("-" * 50)
    for entry in feed.entries:
        print(f"▶ {entry.title}")
        print(f"🔗 링크: {entry.link}")
        print("-" * 50)


if __name__ == "__main__":
    target_handle = "@geguri9162"

    real_channel_id = get_channel_id_from_handle(target_handle)
    print(f"추출된 채널 ID: {real_channel_id}")

    print_latest_videos(real_channel_id)