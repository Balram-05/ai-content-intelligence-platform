from abc import ABC, abstractmethod
from app.search.models import SearchResponse, SearchType


class BaseSearchProvider(ABC):
    """Abstract base interface for external search provider implementations."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Identifier name of the search provider."""
        pass

    @property
    @abstractmethod
    def search_type(self) -> SearchType:
        """Search capability type supported by this provider."""
        pass

    @abstractmethod
    async def search(self, query: str, limit: int = 5, **kwargs) -> SearchResponse:
        """Execute external search and return normalized SearchResponse object."""
        pass
