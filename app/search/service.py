import logging
import time
from typing import Any

from app.core.config import get_settings
from app.search.exceptions import (
    InvalidSearchRequestError,
    SearchError,
    SearchProviderNotFoundError,
)
from app.search.models import SearchResponse, SearchType
from app.search.providers import BaseSearchProvider
from app.search.providers.news import NewsSearchProvider
from app.search.providers.papers import PapersSearchProvider
from app.search.providers.trends import TrendsSearchProvider
from app.search.providers.web import WebSearchProvider

logger = logging.getLogger(__name__)


class SearchService:
    """Domain service responsible for executing and normalizing external search operations."""

    def __init__(self, providers: dict[SearchType, BaseSearchProvider] | None = None):
        self.settings = get_settings()
        
        # Default providers mapping if not custom provided
        if providers:
            self._providers = providers
        else:
            self._providers = {
                SearchType.WEB: WebSearchProvider(),
                SearchType.NEWS: NewsSearchProvider(),
                SearchType.TRENDS: TrendsSearchProvider(),
                SearchType.PAPERS: PapersSearchProvider(),
            }

    def register_provider(self, search_type: SearchType, provider: BaseSearchProvider) -> None:
        """Register or override a provider for a specific search type."""
        self._providers[search_type] = provider

    def get_provider(self, search_type: SearchType) -> BaseSearchProvider:
        """Retrieve the configured provider for the given search type."""
        if search_type not in self._providers:
            raise SearchProviderNotFoundError(f"No search provider registered for type '{search_type}'.")
        return self._providers[search_type]

    def _validate_request(self, query: str, limit: int) -> int:
        """Validate query and limit parameters."""
        if not query or not query.strip():
            raise InvalidSearchRequestError("Search query cannot be empty or blank.")
        if limit < 1:
            raise InvalidSearchRequestError(f"Search result limit must be at least 1, received: {limit}")
        
        # Enforce maximum result limit
        return min(limit, self.settings.SEARCH_MAX_LIMIT)

    async def search(
        self,
        query: str,
        search_type: SearchType | str = SearchType.WEB,
        limit: int = 5,
        **kwargs: Any
    ) -> SearchResponse:
        """Generic search execution dispatcher."""
        if isinstance(search_type, str):
            try:
                search_type = SearchType(search_type.lower())
            except ValueError:
                raise InvalidSearchRequestError(
                    f"Unsupported search_type '{search_type}'. Allowed types: {[t.value for t in SearchType]}"
                )

        validated_limit = self._validate_request(query, limit)
        provider = self.get_provider(search_type)

        start_time = time.perf_counter()
        logger.info(
            f"SearchService starting search: type='{search_type.value}', "
            f"provider='{provider.provider_name}', query_len={len(query)}, limit={validated_limit}"
        )

        try:
            response = await provider.search(query=query.strip(), limit=validated_limit, **kwargs)
            duration = time.perf_counter() - start_time
            
            logger.info(
                f"SearchService completed search: type='{search_type.value}', "
                f"provider='{response.provider}', total_results={response.total_results}, "
                f"duration={duration:.3f}s"
            )
            return response
        except SearchError as e:
            logger.error(f"SearchService domain error during '{search_type.value}' search: {e}")
            raise
        except Exception as e:
            logger.exception(f"SearchService unhandled failure during '{search_type.value}' search: {e}")
            raise SearchError(f"Unexpected error executing search for '{query}': {e}") from e

    async def search_web(self, query: str, limit: int = 5, **kwargs: Any) -> SearchResponse:
        """Execute web search capability."""
        return await self.search(query=query, search_type=SearchType.WEB, limit=limit, **kwargs)

    async def search_news(self, query: str, limit: int = 5, **kwargs: Any) -> SearchResponse:
        """Execute news search capability."""
        return await self.search(query=query, search_type=SearchType.NEWS, limit=limit, **kwargs)

    async def search_trends(self, query: str, limit: int = 5, **kwargs: Any) -> SearchResponse:
        """Execute trend search capability."""
        return await self.search(query=query, search_type=SearchType.TRENDS, limit=limit, **kwargs)

    async def search_research_papers(self, query: str, limit: int = 5, **kwargs: Any) -> SearchResponse:
        """Execute research paper search capability."""
        return await self.search(query=query, search_type=SearchType.PAPERS, limit=limit, **kwargs)
