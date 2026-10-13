import logging
import httpx
from typing import Any

from app.core.config import get_settings
from app.search.exceptions import SearchProviderAPIError, SearchProviderConfigError
from app.search.models import SearchResponse, SearchResult, SearchType
from app.search.providers import BaseSearchProvider

logger = logging.getLogger(__name__)


class WebSearchProvider(BaseSearchProvider):
    """Provider for general web search operations."""

    def __init__(self, provider_name: str | None = None, api_key: str | None = None, timeout: float | None = None):
        settings = get_settings()
        self._provider_name = provider_name or settings.SEARCH_WEB_PROVIDER
        self.api_key = api_key or settings.TAVILY_API_KEY or settings.SERPER_API_KEY
        self.timeout = timeout or settings.SEARCH_TIMEOUT_SECONDS

    @property
    def provider_name(self) -> str:
        return self._provider_name

    @property
    def search_type(self) -> SearchType:
        return SearchType.WEB

    async def search(self, query: str, limit: int = 5, **kwargs) -> SearchResponse:
        logger.info(f"Executing web search with provider '{self._provider_name}' for query: '{query}'")
        
        if self._provider_name == "tavily":
            return await self._search_tavily(query, limit)
        elif self._provider_name == "serper":
            return await self._search_serper(query, limit)
        elif self._provider_name == "duckduckgo":
            return await self._search_duckduckgo(query, limit)
        else:
            # Default fallback logic: use tavily if key exists, else duckduckgo
            if settings := get_settings():
                if settings.TAVILY_API_KEY:
                    return await self._search_tavily(query, limit)
            return await self._search_duckduckgo(query, limit)

    async def _search_tavily(self, query: str, limit: int) -> SearchResponse:
        settings = get_settings()
        api_key = settings.TAVILY_API_KEY or self.api_key
        if not api_key:
            raise SearchProviderConfigError(
                "Tavily web search API key is missing. Please configure TAVILY_API_KEY in environment variables."
            )

        url = "https://api.tavily.com/search"
        payload = {
            "api_key": api_key,
            "query": query,
            "max_results": limit,
            "search_depth": "basic"
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
                response = await client.post(url, json=payload)
                if response.status_code == 401 or response.status_code == 403:
                    raise SearchProviderConfigError(f"Tavily API key is invalid (HTTP {response.status_code}).")
                response.raise_for_status()
                data = response.json()
        except httpx.TimeoutException as e:
            raise SearchProviderAPIError(f"Tavily API request timed out: {e}") from e
        except httpx.HTTPError as e:
            raise SearchProviderAPIError(f"Tavily API HTTP error occurred: {e}") from e
        except Exception as e:
            if isinstance(e, SearchProviderConfigError):
                raise
            raise SearchProviderAPIError(f"Unexpected failure during Tavily web search: {e}") from e

        results: list[SearchResult] = []
        raw_results = data.get("results", [])
        for item in raw_results[:limit]:
            results.append(
                SearchResult(
                    title=item.get("title", "Untitled"),
                    url=item.get("url", ""),
                    snippet=item.get("content", item.get("snippet", "")),
                    source="Tavily",
                    published_at=item.get("published_date"),
                    result_type=SearchType.WEB,
                    metadata={"score": item.get("score")}
                )
            )

        return SearchResponse(
            query=query,
            search_type=SearchType.WEB,
            results=results,
            total_results=len(results),
            provider="tavily"
        )

    async def _search_serper(self, query: str, limit: int) -> SearchResponse:
        settings = get_settings()
        api_key = settings.SERPER_API_KEY or self.api_key
        if not api_key:
            raise SearchProviderConfigError(
                "Serper API key is missing. Please configure SERPER_API_KEY in environment variables."
            )

        url = "https://google.serper.dev/search"
        headers = {"X-API-KEY": api_key, "Content-Type": "application/json"}
        payload = {"q": query, "num": limit}

        try:
            async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
                response = await client.post(url, headers=headers, json=payload)
                if response.status_code in (401, 403):
                    raise SearchProviderConfigError(f"Serper API key is invalid (HTTP {response.status_code}).")
                response.raise_for_status()
                data = response.json()
        except httpx.TimeoutException as e:
            raise SearchProviderAPIError(f"Serper API request timed out: {e}") from e
        except httpx.HTTPError as e:
            raise SearchProviderAPIError(f"Serper API HTTP error: {e}") from e
        except Exception as e:
            if isinstance(e, SearchProviderConfigError):
                raise
            raise SearchProviderAPIError(f"Unexpected error in Serper web search: {e}") from e

        results: list[SearchResult] = []
        organic = data.get("organic", [])
        for item in organic[:limit]:
            results.append(
                SearchResult(
                    title=item.get("title", "Untitled"),
                    url=item.get("link", ""),
                    snippet=item.get("snippet", ""),
                    source="Serper",
                    published_at=item.get("date"),
                    result_type=SearchType.WEB,
                    metadata={"position": item.get("position")}
                )
            )

        return SearchResponse(
            query=query,
            search_type=SearchType.WEB,
            results=results,
            total_results=len(results),
            provider="serper"
        )

    async def _search_duckduckgo(self, query: str, limit: int) -> SearchResponse:
        url = f"https://api.duckduckgo.com/?q={httpx.QueryParams({'q': query})['q']}&format=json&no_html=1&skip_disambig=1"
        try:
            async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
                response = await client.get(url)
                response.raise_for_status()
                data = response.json()
        except httpx.TimeoutException as e:
            raise SearchProviderAPIError(f"DuckDuckGo search request timed out: {e}") from e
        except httpx.HTTPError as e:
            raise SearchProviderAPIError(f"DuckDuckGo API error: {e}") from e
        except Exception as e:
            raise SearchProviderAPIError(f"DuckDuckGo web search failed: {e}") from e

        results: list[SearchResult] = []
        
        # Check Abstract or RelatedTopics
        abstract_url = data.get("AbstractURL", "")
        abstract_text = data.get("AbstractText", "")
        heading = data.get("Heading", query)
        
        if abstract_url and abstract_text:
            results.append(
                SearchResult(
                    title=heading,
                    url=abstract_url,
                    snippet=abstract_text,
                    source="DuckDuckGo Instant Answer",
                    result_type=SearchType.WEB,
                    metadata={"source": data.get("AbstractSource")}
                )
            )

        topics = data.get("RelatedTopics", [])
        for topic in topics:
            if len(results) >= limit:
                break
            if isinstance(topic, dict) and "FirstURL" in topic:
                results.append(
                    SearchResult(
                        title=topic.get("Text", "DuckDuckGo Result")[:60] + "...",
                        url=topic.get("FirstURL", ""),
                        snippet=topic.get("Text", ""),
                        source="DuckDuckGo",
                        result_type=SearchType.WEB,
                        metadata={}
                    )
                )

        return SearchResponse(
            query=query,
            search_type=SearchType.WEB,
            results=results[:limit],
            total_results=len(results[:limit]),
            provider="duckduckgo"
        )
