import logging
import xml.etree.ElementTree as ET
import httpx
from typing import Any

from app.core.config import get_settings
from app.search.exceptions import SearchProviderAPIError, SearchProviderConfigError
from app.search.models import SearchResponse, SearchResult, SearchType
from app.search.providers import BaseSearchProvider

logger = logging.getLogger(__name__)


class NewsSearchProvider(BaseSearchProvider):
    """Provider for news search operations."""

    def __init__(self, provider_name: str | None = None, api_key: str | None = None, timeout: float | None = None):
        settings = get_settings()
        self._provider_name = provider_name or settings.SEARCH_NEWS_PROVIDER
        self.api_key = api_key or settings.NEWS_API_KEY
        self.timeout = timeout or settings.SEARCH_TIMEOUT_SECONDS

    @property
    def provider_name(self) -> str:
        return self._provider_name

    @property
    def search_type(self) -> SearchType:
        return SearchType.NEWS

    async def search(self, query: str, limit: int = 5, **kwargs) -> SearchResponse:
        logger.info(f"Executing news search with provider '{self._provider_name}' for query: '{query}'")

        if self._provider_name == "newsapi":
            return await self._search_newsapi(query, limit)
        elif self._provider_name == "googlenews":
            return await self._search_google_news_rss(query, limit)
        else:
            settings = get_settings()
            if settings.NEWS_API_KEY:
                return await self._search_newsapi(query, limit)
            return await self._search_google_news_rss(query, limit)

    async def _search_newsapi(self, query: str, limit: int) -> SearchResponse:
        settings = get_settings()
        api_key = settings.NEWS_API_KEY or self.api_key
        if not api_key:
            raise SearchProviderConfigError(
                "NewsAPI key is missing. Please configure NEWS_API_KEY in environment variables."
            )

        url = "https://newsapi.org/v2/everything"
        params = {
            "q": query,
            "pageSize": limit,
            "sortBy": "publishedAt",
            "apiKey": api_key,
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
                response = await client.get(url, params=params)
                if response.status_code in (401, 403):
                    raise SearchProviderConfigError(f"NewsAPI key is invalid or unauthorized (HTTP {response.status_code}).")
                response.raise_for_status()
                data = response.json()
        except httpx.TimeoutException as e:
            raise SearchProviderAPIError(f"NewsAPI request timed out: {e}") from e
        except httpx.HTTPError as e:
            raise SearchProviderAPIError(f"NewsAPI HTTP error occurred: {e}") from e
        except Exception as e:
            if isinstance(e, SearchProviderConfigError):
                raise
            raise SearchProviderAPIError(f"Unexpected error in NewsAPI search: {e}") from e

        results: list[SearchResult] = []
        articles = data.get("articles", [])
        for item in articles[:limit]:
            source_name = item.get("source", {}).get("name") if isinstance(item.get("source"), dict) else "NewsAPI"
            results.append(
                SearchResult(
                    title=item.get("title", "Untitled News"),
                    url=item.get("url", ""),
                    snippet=item.get("description", item.get("content")),
                    source=source_name,
                    published_at=item.get("publishedAt"),
                    result_type=SearchType.NEWS,
                    metadata={"author": item.get("author")}
                )
            )

        return SearchResponse(
            query=query,
            search_type=SearchType.NEWS,
            results=results,
            total_results=len(results),
            provider="newsapi"
        )

    async def _search_google_news_rss(self, query: str, limit: int) -> SearchResponse:
        url = f"https://news.google.com/rss/search?q={query}&hl=en-US&gl=US&ceid=US:en"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

        try:
            async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
                response = await client.get(url, headers=headers)
                response.raise_for_status()
                xml_text = response.text
        except httpx.TimeoutException as e:
            raise SearchProviderAPIError(f"Google News RSS request timed out: {e}") from e
        except httpx.HTTPError as e:
            raise SearchProviderAPIError(f"Google News RSS HTTP error: {e}") from e
        except Exception as e:
            raise SearchProviderAPIError(f"Google News RSS search failed: {e}") from e

        results: list[SearchResult] = []
        try:
            root = ET.fromstring(xml_text)
            channel = root.find("channel")
            if channel is not None:
                for item in channel.findall("item")[:limit]:
                    title = item.findtext("title", "Untitled News")
                    link = item.findtext("link", "")
                    pub_date = item.findtext("pubDate")
                    source_elem = item.find("source")
                    source_name = source_elem.text if source_elem is not None else "Google News"
                    description = item.findtext("description")

                    results.append(
                        SearchResult(
                            title=title,
                            url=link,
                            snippet=description,
                            source=source_name,
                            published_at=pub_date,
                            result_type=SearchType.NEWS,
                            metadata={}
                        )
                    )
        except Exception as e:
            logger.warning(f"Error parsing Google News RSS XML: {e}")

        return SearchResponse(
            query=query,
            search_type=SearchType.NEWS,
            results=results,
            total_results=len(results),
            provider="googlenews"
        )
