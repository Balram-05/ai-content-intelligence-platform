import logging
import xml.etree.ElementTree as ET
import httpx
from typing import Any

from app.core.config import get_settings
from app.search.exceptions import SearchProviderAPIError, SearchProviderConfigError
from app.search.models import SearchResponse, SearchResult, SearchType
from app.search.providers import BaseSearchProvider

logger = logging.getLogger(__name__)


class TrendsSearchProvider(BaseSearchProvider):
    """Provider for trend search operations."""

    def __init__(self, provider_name: str | None = None, timeout: float | None = None):
        settings = get_settings()
        self._provider_name = provider_name or settings.SEARCH_TRENDS_PROVIDER
        self.timeout = timeout or settings.SEARCH_TIMEOUT_SECONDS

    @property
    def provider_name(self) -> str:
        return self._provider_name

    @property
    def search_type(self) -> SearchType:
        return SearchType.TRENDS

    async def search(self, query: str, limit: int = 5, **kwargs) -> SearchResponse:
        logger.info(f"Executing trend search with provider '{self._provider_name}' for query: '{query}'")

        if self._provider_name == "github_trends":
            return await self._search_github_trends(query, limit)
        elif self._provider_name == "google_trends":
            try:
                return await self._search_google_trends(query, limit)
            except SearchProviderAPIError as e:
                logger.warning(f"Google Trends failed ({e}), falling back to GitHub Trends.")
                return await self._search_github_trends(query, limit)
        else:
            try:
                return await self._search_github_trends(query, limit)
            except Exception:
                return await self._search_google_trends(query, limit)

    async def _search_github_trends(self, query: str, limit: int) -> SearchResponse:
        clean_query = query.replace(" ", "+") if query else "trending"
        url = f"https://api.github.com/search/repositories?q={clean_query}+sort:stars-desc&per_page={limit}"
        headers = {"User-Agent": "AI-Content-Intelligence-Platform", "Accept": "application/vnd.github.v3+json"}

        try:
            async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
                response = await client.get(url, headers=headers)
                response.raise_for_status()
                data = response.json()
        except httpx.TimeoutException as e:
            raise SearchProviderAPIError(f"GitHub Trends request timed out: {e}") from e
        except httpx.HTTPError as e:
            raise SearchProviderAPIError(f"GitHub Trends HTTP error: {e}") from e
        except Exception as e:
            raise SearchProviderAPIError(f"GitHub Trends search failed: {e}") from e

        results: list[SearchResult] = []
        items = data.get("items", [])
        for item in items[:limit]:
            results.append(
                SearchResult(
                    title=f"Trending Repository: {item.get('full_name')}",
                    url=item.get("html_url", ""),
                    snippet=item.get("description") or "No description provided.",
                    source="GitHub Trends",
                    published_at=item.get("created_at"),
                    result_type=SearchType.TRENDS,
                    metadata={"stargazers_count": item.get("stargazers_count"), "language": item.get("language")}
                )
            )

        return SearchResponse(
            query=query,
            search_type=SearchType.TRENDS,
            results=results,
            total_results=len(results),
            provider="github_trends"
        )

    async def _search_google_trends(self, query: str, limit: int) -> SearchResponse:
        url = f"https://news.google.com/rss/search?q={query}+trends&hl=en-US&gl=US&ceid=US:en"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

        try:
            async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
                response = await client.get(url, headers=headers)
                response.raise_for_status()
                xml_text = response.text
        except httpx.TimeoutException as e:
            raise SearchProviderAPIError(f"Google Trends request timed out: {e}") from e
        except httpx.HTTPError as e:
            raise SearchProviderAPIError(f"Google Trends HTTP error: {e}") from e
        except Exception as e:
            raise SearchProviderAPIError(f"Google Trends fetch failed: {e}") from e

        results: list[SearchResult] = []
        try:
            root = ET.fromstring(xml_text)
            channel = root.find("channel")
            if channel is not None:
                for item in channel.findall("item")[:limit]:
                    title = item.findtext("title", "Trending Topic")
                    link = item.findtext("link", "")
                    pub_date = item.findtext("pubDate")
                    description = item.findtext("description")

                    results.append(
                        SearchResult(
                            title=f"Trend: {title}",
                            url=link or "https://trends.google.com",
                            snippet=description or title,
                            source="Google News Trends",
                            published_at=pub_date,
                            result_type=SearchType.TRENDS,
                            metadata={}
                        )
                    )
        except Exception as e:
            logger.warning(f"Error parsing Google Trends XML: {e}")

        return SearchResponse(
            query=query,
            search_type=SearchType.TRENDS,
            results=results,
            total_results=len(results),
            provider="google_trends"
        )
