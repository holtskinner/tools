import feedparser
from datetime import datetime, timezone
from typing import List
from find_impact.config import Config
from find_impact.models import ContentItem
from find_impact.fetchers.base import BaseFetcher


class CustomRSSFetcher(BaseFetcher):
    @property
    def name(self) -> str:
        return "RSS"

    def fetch(self, config: Config) -> List[ContentItem]:
        feeds = config.custom_rss_feeds
        items: List[ContentItem] = []

        if not feeds:
            return []

        for feed_cfg in feeds:
            feed_name = feed_cfg.get("name", "Custom Feed")
            feed_url = feed_cfg.get("url")
            enabled = feed_cfg.get("enabled", True)

            if not feed_url or not enabled:
                continue

            print(f"Fetching custom RSS feed '{feed_name}': {feed_url}...")
            try:
                feed = feedparser.parse(feed_url)
                if feed.get("bozo", 0) == 1 and not feed.entries:
                    print(f"Warning: Failed to parse RSS feed '{feed_name}'")
                    continue

                for entry in feed.entries:
                    title = entry.get("title", "Untitled Post")
                    url = entry.get("link", "")

                    # Normalize URL (strip query parameters)
                    if "?" in url:
                        url = url.split("?")[0]

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

                    summary = entry.get("summary", "") or entry.get("description", "")
                    if summary:
                        import re

                        clean_summary = re.sub(r"<[^>]+>", "", summary)
                        if len(clean_summary) > 200:
                            clean_summary = clean_summary[:200] + "..."
                    else:
                        clean_summary = ""

                    # ID based on URL
                    item_id = f"custom-rss-{feed_name.lower().replace(' ', '-')}-{url}"

                    items.append(
                        ContentItem(
                            id=item_id,
                            title=f"[{feed_name}] {title}",
                            url=url,
                            platform="rss",
                            publish_date=publish_date,
                            summary=clean_summary,
                            extra_metadata={
                                "feed_name": feed_name,
                                "author": entry.get("author", ""),
                            },
                        )
                    )
            except Exception as e:
                print(f"Error parsing custom RSS feed '{feed_name}': {e}")

        return items
