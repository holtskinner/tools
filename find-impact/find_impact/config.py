import os
import yaml
from typing import Dict, Any, List, Optional


class Config:
    def __init__(self, config_path: str = "config.yaml"):
        self.config_path = config_path
        self.data: Dict[str, Any] = {}
        self.load()

    def load(self):
        """Loads configuration from YAML file, falling back to defaults if not found."""
        if os.path.exists(self.config_path):
            with open(self.config_path, "r", encoding="utf-8") as f:
                try:
                    self.data = yaml.safe_load(f) or {}
                except Exception as e:
                    print(
                        f"Warning: Failed to parse config file '{self.config_path}': {e}. Using defaults."
                    )
                    self.data = {}
        else:
            print(
                f"Warning: Configuration file '{self.config_path}' not found. Using default empty settings."
            )
            self.data = {}

    @property
    def developer_name(self) -> str:
        return self.data.get("developer", {}).get("name", "Holt Skinner")

    @property
    def developer_role(self) -> str:
        return self.data.get("developer", {}).get("role", "Staff Developer Relations Engineer")

    @property
    def developer_company(self) -> str:
        return self.data.get("developer", {}).get("company", "Google Cloud AI")

    @property
    def github_username(self) -> Optional[str]:
        return self.data.get("sources", {}).get("github", {}).get("username", "holtskinner")

    @property
    def github_orgs(self) -> List[str]:
        return self.data.get("sources", {}).get("github", {}).get("orgs", [])

    @property
    def stackoverflow_user_id(self) -> Optional[str]:
        val = self.data.get("sources", {}).get("stackoverflow", {}).get("user_id")
        return str(val) if val is not None else None

    @property
    def medium_username(self) -> Optional[str]:
        return self.data.get("sources", {}).get("medium", {}).get("username", "holtskinner")

    @property
    def medium_publications(self) -> List[str]:
        return self.data.get("sources", {}).get("medium", {}).get("publications", ["google-cloud"])

    @property
    def youtube_channels(self) -> List[Dict[str, str]]:
        return self.data.get("sources", {}).get("youtube", {}).get("channels", [])

    @property
    def youtube_search_queries(self) -> List[str]:
        return (
            self.data.get("sources", {})
            .get("youtube", {})
            .get("search_queries", [self.developer_name])
        )

    @property
    def youtube_custom_videos(self) -> List[str]:
        return self.data.get("sources", {}).get("youtube", {}).get("custom_videos", [])

    @property
    def custom_rss_feeds(self) -> List[Dict[str, Any]]:
        return self.data.get("sources", {}).get("custom_rss", [])

    @property
    def html_report_path(self) -> str:
        return self.data.get("export", {}).get("html_report_path", "dashboard.html")

    @property
    def markdown_report_path(self) -> str:
        return self.data.get("export", {}).get("markdown_report_path", "impact_report.md")

    @property
    def cache_path(self) -> str:
        return self.data.get("export", {}).get("cache_path", ".find_impact_cache.json")
