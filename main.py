import datetime
import re
import feedparser
import requests
import yaml


def get_channel_id_from_handle(handle):
    """채널 핸들(@username)에서 채널 ID 추출 (User-Agent 포함)"""
    if not handle.startswith("@"):
        handle = "@" + handle

    channel_url = f"https://www.youtube.com/{handle}"
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "Anonymously-Generated-UA/1.0"
        ),
        "Accept-Language": "ko-KR,ko;q=0.9",
    }

    try:
        response = requests.get(channel_url, headers=headers, timeout=10)
        response.raise_for_status()
    except Exception as e:
        print(f"❌ {handle} 페이지 접속 실패: {e}")
        return None

    # HTML 내에서 ID 패턴 검색
    for pattern in [
        r'"externalId"\s*:\s*"([^"]+)"',
        r'"browseId"\s*:\s*"(UC[^"]+)"',
        r'"channelId"\s*:\s*"([^"]+)"',
    ]:
        match = re.search(pattern, response.text)
        if match:
            return match.group(1)

    print(f"⚠️ {handle}의 채널 ID를 찾을 수 없습니다.")
    return None


def collect_all_videos():
    # 1. YAML 파일에서 채널 목록 읽기
    try:
        with open("channels.yaml", "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
            channels = config.get("channels", [])
    except FileNotFoundError:
        print("❌ 'channels.yaml' 파일이 존재하지 않습니다.")
        return []

    all_videos = []

    # 2. 각 채널 순회하며 영상 수집
    for handle in channels:
        print(f"\n🔍 {handle} 수집 중...")
        channel_id = get_channel_id_from_handle(handle)

        if not channel_id:
            continue

        rss_url = (
            f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
        )
        feed = feedparser.parse(rss_url)

        for entry in feed.entries:
            # 날짜 파싱 (struct_time -> datetime)
            published_parsed = entry.get("published_parsed")
            if published_parsed:
                dt = datetime.datetime(*published_parsed[:6])
            else:
                dt = datetime.datetime.min

            # 썸네일 URL 가져오기 (feedparser가 media_thumbnail 구조를 리스트로 매핑해줍니다)
            thumbnail_url = ""
            if "media_thumbnail" in entry and len(entry.media_thumbnail) > 0:
                thumbnail_url = entry.media_thumbnail[0]["url"]

            all_videos.append(
                {
                    "title": entry.title,
                    "link": entry.link,
                    "author": entry.author if "author" in entry else handle,
                    "published": dt,
                    "thumbnail": thumbnail_url,
                }
            )

    # 3. 날짜 기준 최신순 정렬 (내림차순)
    all_videos.sort(key=lambda x: x["published"], reverse=True)
    return all_videos


def generate_html(videos, output_filename="youtube_feeds.html"):
    """수집된 영상을 바탕으로 깔끔한 모던 스타일 HTML 생성"""

    # HTML 그리드 아이템 생성
    video_cards_html = ""
    for video in videos:
        formatted_date = video["published"].strftime("%Y-%m-%d %H:%M")
        video_cards_html += f"""
        <div class="video-card">
            <a href="{video['link']}" target="_blank" class="thumbnail-link">
                <img src="{video['thumbnail']}" alt="{video['title']}" class="thumbnail" loading="lazy">
            </a>
            <div class="video-info">
                <h3 class="video-title">
                    <a href="{video['link']}" target="_blank">{video['title']}</a>
                </h3>
                <p class="video-author">{video['author']}</p>
                <p class="video-date">{formatted_date}</p>
            </div>
        </div>
        """

    # 전체 HTML 템플릿
    html_template = f"""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>통합 유튜브 피드 대시보드</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background-color: #f9f9f9;
            color: #111;
            margin: 0;
            padding: 20px;
        }}
        header {{
            text-align: center;
            margin-bottom: 40px;
        }}
        h1 {{ color: #FF0000; }}
        .video-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
            gap: 24px;
            max-width: 1400px;
            margin: 0 auto;
        }}
        .video-card {{
            background: #fff;
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 4px 6px rgba(0,0,0,0.05);
            transition: transform 0.2s, box-shadow 0.2s;
        }}
        .video-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 8px 15px rgba(0,0,0,0.1);
        }}
        .thumbnail-link {{
            display: block;
            width: 100%;
            aspect-ratio: 16 / 9;
            background: #eee;
            overflow: hidden;
        }}
        .thumbnail {{
            width: 100%;
            height: 100%;
            object-fit: cover;
        }}
        .video-info {{
            padding: 15px;
        }}
        .video-title {{
            font-size: 15px;
            margin: 0 0 8px 0;
            line-height: 1.4;
            display: -webkit-box;
            -webkit-line-clamp: 2;
            -webkit-box-orient: vertical;
            overflow: hidden;
        }}
        .video-title a {{
            color: #0f0f0f;
            text-decoration: none;
        }}
        .video-title a:hover {{
            color: #065fd4;
        }}
        .video-author {{
            font-size: 13px;
            color: #606060;
            margin: 0 0 4px 0;
            font-weight: 500;
        }}
        .video-date {{
            font-size: 12px;
            color: #909090;
            margin: 0;
        }}
    </style>
</head>
<body>
    <header>
        <h1>📺 통합 유튜브 피드 대시보드</h1>
        <p>최근 업데이트: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    </header>
    <main class="video-grid">
        {video_cards_html}
    </main>
</body>
</html>
"""

    with open(output_filename, "w", encoding="utf-8") as f:
        f.write(html_template)
    print(f"\n🎉 성공! HTML 파일이 생성되었습니다: {output_filename}")


if __name__ == "__main__":
    # 1. 수집 및 정렬
    videos_list = collect_all_videos()

    # 2. HTML 빌드
    if videos_list:
        generate_html(videos_list)
    else:
        print("❌ 수집된 동영상이 없어 HTML을 생성하지 못했습니다.")