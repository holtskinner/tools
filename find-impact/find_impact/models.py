from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Dict, Any, Optional


@dataclass
class ContentItem:
    id: str
    title: str
    url: str
    platform: str  # "github" | "youtube" | "stackoverflow" | "medium" | "rss"
    publish_date: str  # ISO-8601 string (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SSZ)
    summary: Optional[str] = ""
    metrics: Dict[str, Any] = field(default_factory=dict)
    extra_metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert content item to dictionary for JSON caching."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ContentItem":
        """Reconstruct content item from cached dictionary."""
        return cls(
            id=data["id"],
            title=data["title"],
            url=data["url"],
            platform=data["platform"],
            publish_date=data["publish_date"],
            summary=data.get("summary", ""),
            metrics=data.get("metrics", {}),
            extra_metadata=data.get("extra_metadata", {}),
        )

    @property
    def parsed_date(self) -> datetime:
        """Parse the publish date string into a datetime object."""
        try:
            # Handle various ISO formats
            date_str = self.publish_date
            if date_str.endswith("Z"):
                date_str = date_str[:-1] + "+00:00"
            return datetime.fromisoformat(date_str)
        except ValueError:
            # Fallback to epoch if parsing fails
            try:
                # Try reading just YYYY-MM-DD
                return datetime.strptime(self.publish_date.split("T")[0], "%Y-%m-%d")
            except Exception:
                return datetime.min
