import os
import requests
import feedparser
from datetime import datetime, timezone
from typing import List, Dict
from find_impact.config import Config
from find_impact.models import ContentItem
from find_impact.fetchers.base import BaseFetcher


class YouTubeFetcher(BaseFetcher):
    @property
    def name(self) -> str:
        return "YouTube"

    def fetch(self, config: Config) -> List[ContentItem]:
        channels = config.youtube_channels
        search_queries = config.youtube_search_queries
        custom_vids = config.youtube_custom_videos

        items: List[ContentItem] = []
        api_key = os.environ.get("YOUTUBE_API_KEY")

        # 1. Fetch channel videos (API or RSS)
        if channels:
            if api_key:
                print(
                    "YOUTUBE_API_KEY found. Fetching channel search results via YouTube Data API..."
                )
                items.extend(self._fetch_via_api(channels, search_queries, api_key))
            else:
                print("YOUTUBE_API_KEY not found. Falling back to public Channel RSS feeds...")
                items.extend(self._fetch_via_rss(channels, search_queries))
        else:
            print("No YouTube channels configured to monitor. Skipping channel sync.")

        # 2. Fetch specific custom videos if configured
        if custom_vids:
            if api_key:
                items.extend(self._fetch_custom_videos_via_api(custom_vids, api_key))
            else:
                items.extend(self._fetch_custom_videos_via_scraping(custom_vids))

        # 3. Deduplicate combined results by ID
        dedup_dict: Dict[str, ContentItem] = {item.id: item for item in items}
        return list(dedup_dict.values())

    def _fetch_custom_videos_via_api(self, video_ids: List[str], api_key: str) -> List[ContentItem]:
        if not video_ids:
            return []

        print(f"Fetching {len(video_ids)} custom videos via YouTube Data API...")
        items: List[ContentItem] = []
        base_url = "https://www.googleapis.com/youtube/v3/videos"

        for i in range(0, len(video_ids), 50):
            chunk = video_ids[i : i + 50]
            params = {"part": "snippet", "id": ",".join(chunk), "key": api_key}
            try:
                res = requests.get(base_url, params=params)
                if res.status_code == 200:
                    data = res.json()
                    for v in data.get("items", []):
                        video_id = v.get("id")
                        snippet = v.get("snippet", {})
                        title = snippet.get("title", "")
                        description = snippet.get("description", "")
                        publish_time = snippet.get("publishedAt", "")

                        thumbnails = snippet.get("thumbnails", {})
                        thumb_url = (
                            thumbnails.get("high", {}).get("url")
                            or thumbnails.get("medium", {}).get("url")
                            or thumbnails.get("default", {}).get("url")
                            or ""
                        )

                        items.append(
                            ContentItem(
                                id=f"youtube-video-{video_id}",
                                title=f"[YouTube] {title}",
                                url=f"https://www.youtube.com/watch?v={video_id}",
                                platform="youtube",
                                publish_date=publish_time,
                                summary=description,
                                extra_metadata={
                                    "video_id": video_id,
                                    "channel_id": snippet.get("channelId", ""),
                                    "channel_title": snippet.get("channelTitle", "YouTube"),
                                    "thumbnail_url": thumb_url,
                                },
                            )
                        )
                else:
                    print(f"Warning: YouTube API videos query failed: {res.text}")
            except Exception as e:
                print(f"Error fetching custom videos via API: {e}")

        return items

    def _fetch_custom_videos_via_scraping(self, video_ids: List[str]) -> List[ContentItem]:
        if not video_ids:
            return []

        print(f"Fetching {len(video_ids)} custom videos via direct HTML metadata scraping...")
        items: List[ContentItem] = []
        import html
        import re

        for video_id in video_ids:
            url = f"https://www.youtube.com/watch?v={video_id}"
            try:
                r = requests.get(
                    url,
                    headers={
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
                    },
                    timeout=10,
                )
                if r.status_code != 200:
                    print(
                        f"Warning: Failed to scrape metadata for video {video_id} (status {r.status_code})"
                    )
                    continue

                html_text = r.text

                # Extract Title
                title_match = re.search(r'itemprop="name" content="([^"]+)"', html_text)
                title = title_match.group(1) if title_match else f"YouTube Video {video_id}"
                title = html.unescape(title)

                # Extract Description
                desc_match = re.search(r'itemprop="description" content="([^"]+)"', html_text)
                description = desc_match.group(1) if desc_match else ""
                description = html.unescape(description)

                # Extract Publish Date
                date_match = re.search(r'itemprop="datePublished" content="([^"]+)"', html_text)
                publish_date = (
                    date_match.group(1) if date_match else datetime.now(timezone.utc).isoformat()
                )

                # Extract Channel Title
                channel_match = re.search(
                    r'itemprop="author".*?itemprop="name"\s+content="([^"]+)"',
                    html_text,
                    re.DOTALL,
                )
                channel_title = channel_match.group(1) if channel_match else "YouTube"
                channel_title = html.unescape(channel_title)

                # Default Thumbnail URL
                thumb_url = f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg"

                items.append(
                    ContentItem(
                        id=f"youtube-video-{video_id}",
                        title=f"[YouTube] {title}",
                        url=url,
                        platform="youtube",
                        publish_date=publish_date,
                        summary=description,
                        extra_metadata={
                            "video_id": video_id,
                            "channel_id": "",
                            "channel_title": channel_title,
                            "thumbnail_url": thumb_url,
                        },
                    )
                )
            except Exception as e:
                print(f"Error scraping metadata for YouTube video {video_id}: {e}")

        return items

    def _fetch_via_api(
        self, channels: List[Dict[str, str]], search_queries: List[str], api_key: str
    ) -> List[ContentItem]:
        items: List[ContentItem] = []
        base_url = "https://www.googleapis.com/youtube/v3/search"

        for chan in channels:
            channel_id = chan.get("id")
            channel_name = chan.get("name", channel_id)
            if not channel_id:
                continue

            for query in search_queries:
                print(f"Searching YouTube Channel '{channel_name}' for '{query}'...")
                params = {
                    "part": "snippet",
                    "channelId": channel_id,
                    "q": query,
                    "type": "video",
                    "maxResults": 50,
                    "key": api_key,
                }

                try:
                    res = requests.get(base_url, params=params)
                    if res.status_code == 200:
                        data = res.json()
                        for v in data.get("items", []):
                            video_id = v.get("id", {}).get("videoId")
                            snippet = v.get("snippet", {})
                            if not video_id:
                                continue

                            title = snippet.get("title", "")
                            description = snippet.get("description", "")
                            publish_time = snippet.get("publishedAt", "")

                            # Clean up title HTML entities
                            title = (
                                title.replace("&quot;", '"')
                                .replace("&#39;", "'")
                                .replace("&amp;", "&")
                                .replace("&lt;", "<")
                                .replace("&gt;", ">")
                            )

                            # Thumbnail URL (using medium or high resolution)
                            thumbnails = snippet.get("thumbnails", {})
                            thumb_url = (
                                thumbnails.get("high", {}).get("url")
                                or thumbnails.get("medium", {}).get("url")
                                or thumbnails.get("default", {}).get("url")
                                or ""
                            )

                            url = f"https://www.youtube.com/watch?v={video_id}"

                            items.append(
                                ContentItem(
                                    id=f"youtube-video-{video_id}",
                                    title=f"[YouTube] {title}",
                                    url=url,
                                    platform="youtube",
                                    publish_date=publish_time,
                                    summary=description,
                                    extra_metadata={
                                        "video_id": video_id,
                                        "channel_id": channel_id,
                                        "channel_title": snippet.get("channelTitle", channel_name),
                                        "thumbnail_url": thumb_url,
                                    },
                                )
                            )
                    else:
                        print(
                            f"Warning: YouTube API search failed (status {res.status_code}): {res.text}"
                        )
                except Exception as e:
                    print(f"Error calling YouTube API for channel '{channel_name}': {e}")

        return items

    def _fetch_via_rss(
        self, channels: List[Dict[str, str]], search_queries: List[str]
    ) -> List[ContentItem]:
        items: List[ContentItem] = []

        for chan in channels:
            channel_id = chan.get("id")
            channel_name = chan.get("name", channel_id)
            if not channel_id:
                continue

            rss_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
            print(f"Parsing YouTube RSS feed for '{channel_name}': {rss_url}...")

            try:
                feed = feedparser.parse(rss_url)
                if feed.get("bozo", 0) == 1 and not feed.entries:
                    print(f"Warning: Failed to parse YouTube RSS feed for {channel_name}")
                    continue

                for entry in feed.entries:
                    title = entry.get("title", "")
                    video_id = entry.get("yt_videoid", "") if hasattr(entry, "yt_videoid") else ""
                    if not video_id:
                        # Extract from link if yt_videoid is somehow missing
                        link = entry.get("link", "")
                        if "v=" in link:
                            video_id = link.split("v=")[1].split("&")[0]

                    # Extract description and thumbnail safely from Media RSS
                    description = ""
                    thumb_url = ""

                    if hasattr(entry, "media_group") and entry.media_group:
                        media = entry.media_group[0]
                        description = media.get("media_description", "")
                        thumbnails = media.get("media_thumbnail", [])
                        if thumbnails:
                            thumb_url = thumbnails[0].get("url", "")

                    if not description:
                        description = entry.get("summary", "") or entry.get("description", "")

                    # Check if the title or description matches any of our keywords (case-insensitive)
                    content_to_match = (title + " " + description).lower()
                    is_match = any(q.lower() in content_to_match for q in search_queries)

                    if is_match:
                        # Parse publish date
                        publish_date = ""
                        parsed_time = entry.get("published_parsed") or entry.get("updated_parsed")
                        if parsed_time:
                            dt = datetime(*parsed_time[:6], tzinfo=timezone.utc)
                            publish_date = dt.isoformat()
                        else:
                            publish_date = (
                                entry.get("published", "") or datetime.now(timezone.utc).isoformat()
                            )

                        url = entry.get("link", "") or f"https://www.youtube.com/watch?v={video_id}"

                        items.append(
                            ContentItem(
                                id=f"youtube-video-{video_id}",
                                title=f"[YouTube] {title}",
                                url=url,
                                platform="youtube",
                                publish_date=publish_date,
                                summary=description,
                                extra_metadata={
                                    "video_id": video_id,
                                    "channel_id": channel_id,
                                    "channel_title": channel_name,
                                    "thumbnail_url": thumb_url,
                                },
                            )
                        )
            except Exception as e:
                print(f"Error parsing YouTube feed for '{channel_name}': {e}")

        return items
