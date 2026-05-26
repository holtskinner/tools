import json
import os
from typing import List, Dict
from find_impact.models import ContentItem


class CacheManager:
    def __init__(self, cache_path: str = ".find_impact_cache.json"):
        self.cache_path = cache_path

    def load(self) -> List[ContentItem]:
        """Loads cached ContentItems from local JSON file."""
        if not os.path.exists(self.cache_path):
            return []

        try:
            with open(self.cache_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    return [ContentItem.from_dict(item) for item in data]
                elif isinstance(data, dict) and "items" in data:
                    return [ContentItem.from_dict(item) for item in data["items"]]
        except Exception as e:
            print(f"Warning: Failed to load cache file '{self.cache_path}': {e}. Starting fresh.")

        return []

    def save(self, items: List[ContentItem]):
        """Saves current ContentItems to local JSON file."""
        try:
            # Sort items by date descending before saving
            sorted_items = sorted(items, key=lambda x: x.parsed_date, reverse=True)
            serialized = [item.to_dict() for item in sorted_items]
            with open(self.cache_path, "w", encoding="utf-8") as f:
                json.dump(serialized, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error: Failed to write to cache file '{self.cache_path}': {e}")

    def merge_and_save(self, new_items: List[ContentItem]) -> List[ContentItem]:
        """Merges new items with existing cache, updates metrics/fields for existing items, and saves."""
        existing_items = self.load()
        items_dict: Dict[str, ContentItem] = {item.id: item for item in existing_items}

        for item in new_items:
            if item.id in items_dict:
                # Merge logic: keep the newer/better metrics but update if there are newer fields
                cached_item = items_dict[item.id]

                # Merge metrics
                merged_metrics = cached_item.metrics.copy()
                for key, val in item.metrics.items():
                    if val is not None:
                        # For counters, use the max value
                        if (
                            isinstance(val, (int, float))
                            and key in merged_metrics
                            and isinstance(merged_metrics[key], (int, float))
                        ):
                            merged_metrics[key] = max(merged_metrics[key], val)
                        else:
                            merged_metrics[key] = val

                # Update properties
                cached_item.title = item.title or cached_item.title
                cached_item.url = item.url or cached_item.url
                cached_item.summary = item.summary or cached_item.summary
                cached_item.metrics = merged_metrics
                cached_item.extra_metadata.update(item.extra_metadata)
            else:
                items_dict[item.id] = item

        all_items = list(items_dict.values())
        self.save(all_items)
        return all_items
