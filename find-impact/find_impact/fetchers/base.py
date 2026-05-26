from abc import ABC, abstractmethod
from typing import List
from find_impact.config import Config
from find_impact.models import ContentItem


class BaseFetcher(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        """Name of the platform being fetched (e.g. 'GitHub', 'Medium')."""
        pass

    @abstractmethod
    def fetch(self, config: Config) -> List[ContentItem]:
        """Fetches content from the platform and returns a list of ContentItems."""
        pass
