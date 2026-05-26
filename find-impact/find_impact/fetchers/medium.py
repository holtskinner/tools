import feedparser
from datetime import datetime, timezone
from typing import List, Dict
from find_impact.config import Config
from find_impact.models import ContentItem
from find_impact.fetchers.base import BaseFetcher


class MediumFetcher(BaseFetcher):
    @property
    def name(self) -> str:
        return "Medium"

    def fetch(self, config: Config) -> List[ContentItem]:
        username = config.medium_username
        dev_name = config.developer_name
        items: List[ContentItem] = []

        # 1. Fetch user's direct feed (contains only posts written by the user)
        if username:
            user_feed_url = f"https://medium.com/feed/@{username}"
            print(f"Fetching Medium user feed: {user_feed_url}...")
            user_items = self._fetch_feed(user_feed_url)
            items.extend(user_items)

        # 2. Fetch publication feeds and filter by developer name
        publications = config.medium_publications
        if publications:
            for pub in publications:
                pub_feed_url = f"https://medium.com/feed/{pub}"
                print(
                    f"Fetching Medium publication feed: {pub_feed_url} (filtering for author: {dev_name})..."
                )
                pub_items = self._fetch_feed(pub_feed_url, author_filter=dev_name)
                items.extend(pub_items)

        # De-duplicate by URL/ID
        unique_items: Dict[str, ContentItem] = {}
        for item in items:
            unique_items[item.id] = item

        return list(unique_items.values())

    def _fetch_feed(self, feed_url: str, author_filter: str = None) -> List[ContentItem]:
        items: List[ContentItem] = []
        try:
            feed = feedparser.parse(feed_url)

            # Print warning if parsing failed
            if feed.get("bozo", 0) == 1 and not feed.entries:
                exception = feed.get("bozo_exception")
                print(f"Warning: XML parsing warning for '{feed_url}': {exception}")

            for entry in feed.entries:
                author = entry.get("author", "")
                creator = entry.get("creator", "")
                item_author = author or creator

                # If author filter is specified, check if author matches (case-insensitive)
                if author_filter and item_author:
                    if author_filter.lower() not in item_author.lower():
                        continue

                # Get publish date
                publish_date = ""
                parsed_time = entry.get("published_parsed") or entry.get("updated_parsed")
                if parsed_time:
                    # Convert feedparser time struct to UTC datetime then to ISO format
                    dt = datetime(*parsed_time[:6], tzinfo=timezone.utc)
                    publish_date = dt.isoformat()
                else:
                    # Fallback to parsing string directly or current time
                    publish_date = datetime.now(timezone.utc).isoformat()

                title = entry.get("title", "Untitled Medium Article")
                url = entry.get("link", "")

                # Medium URLs often have query parameters that we can strip to normalize
                if "?" in url:
                    url = url.split("?")[0]

                summary = entry.get("summary", "") or entry.get("description", "")
                # Clean up html tags for a brief summary text
                if summary:
                    # Very simple HTML strip
                    import re

                    clean_summary = re.sub(r"<[^>]+>", "", summary)
                    # Limit to 200 chars
                    if len(clean_summary) > 200:
                        clean_summary = clean_summary[:200] + "..."
                else:
                    clean_summary = ""

                # Categories/tags
                tags = [tag.get("term") for tag in entry.get("tags", []) if tag.get("term")]

                # ID creation
                item_id = f"medium-post-{url}"

                items.append(
                    ContentItem(
                        id=item_id,
                        title=f"[Medium] {title}",
                        url=url,
                        platform="medium",
                        publish_date=publish_date,
                        summary=clean_summary,
                        extra_metadata={"author": item_author, "tags": tags},
                    )
                )
        except Exception as e:
            print(f"Error fetching Medium feed '{feed_url}': {e}")

        return items
