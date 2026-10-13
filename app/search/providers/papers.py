import logging
import xml.etree.ElementTree as ET
import httpx
from typing import Any

from app.core.config import get_settings
from app.search.exceptions import SearchProviderAPIError, SearchProviderConfigError
from app.search.models import SearchResponse, SearchResult, SearchType
from app.search.providers import BaseSearchProvider

logger = logging.getLogger(__name__)


class PapersSearchProvider(BaseSearchProvider):
    """Provider for academic research paper search operations."""

    def __init__(self, provider_name: str | None = None, api_key: str | None = None, timeout: float | None = None):
        settings = get_settings()
        self._provider_name = provider_name or settings.SEARCH_PAPERS_PROVIDER
        self.api_key = api_key or settings.SEMANTIC_SCHOLAR_API_KEY
        self.timeout = timeout or settings.SEARCH_TIMEOUT_SECONDS

    @property
    def provider_name(self) -> str:
        return self._provider_name

    @property
    def search_type(self) -> SearchType:
        return SearchType.PAPERS

    async def search(self, query: str, limit: int = 5, **kwargs) -> SearchResponse:
        logger.info(f"Executing paper search with provider '{self._provider_name}' for query: '{query}'")

        if self._provider_name == "arxiv":
            return await self._search_arxiv(query, limit)
        elif self._provider_name == "semantic_scholar":
            try:
                return await self._search_semantic_scholar(query, limit)
            except (SearchProviderAPIError, SearchProviderConfigError) as e:
                logger.warning(f"Semantic Scholar paper search unavailable ({e}). Falling back to ArXiv API.")
                return await self._search_arxiv(query, limit)
        else:
            try:
                return await self._search_arxiv(query, limit)
            except Exception:
                return await self._search_semantic_scholar(query, limit)

    async def _search_semantic_scholar(self, query: str, limit: int) -> SearchResponse:
        url = "https://api.semanticscholar.org/graph/v1/paper/search"
        params = {
            "query": query,
            "limit": limit,
            "fields": "title,abstract,url,authors,publicationDate,venue,citationCount",
        }
        headers = {}
        settings = get_settings()
        api_key = settings.SEMANTIC_SCHOLAR_API_KEY or self.api_key
        if api_key:
            headers["x-api-key"] = api_key

        try:
            async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
                response = await client.get(url, params=params, headers=headers)
                if response.status_code in (401, 403) and api_key:
                    raise SearchProviderConfigError(f"Semantic Scholar API key is invalid (HTTP {response.status_code}).")
                response.raise_for_status()
                data = response.json()
        except httpx.TimeoutException as e:
            raise SearchProviderAPIError(f"Semantic Scholar API request timed out: {e}") from e
        except httpx.HTTPError as e:
            raise SearchProviderAPIError(f"Semantic Scholar API HTTP error occurred: {e}") from e
        except Exception as e:
            if isinstance(e, SearchProviderConfigError):
                raise
            raise SearchProviderAPIError(f"Unexpected error in Semantic Scholar search: {e}") from e

        results: list[SearchResult] = []
        papers = data.get("data", [])
        for paper in papers[:limit]:
            authors_list = [a.get("name") for a in paper.get("authors", []) if a.get("name")]
            authors_str = ", ".join(authors_list[:3]) if authors_list else "Unknown Authors"
            venue = paper.get("venue") or "Semantic Scholar"
            paper_url = paper.get("url") or f"https://www.semanticscholar.org/paper/{paper.get('paperId')}"

            results.append(
                SearchResult(
                    title=paper.get("title", "Untitled Paper"),
                    url=paper_url,
                    snippet=paper.get("abstract") or f"Authors: {authors_str}. Published in {venue}.",
                    source=f"Semantic Scholar ({venue})",
                    published_at=paper.get("publicationDate"),
                    result_type=SearchType.PAPERS,
                    metadata={
                        "authors": authors_list,
                        "citation_count": paper.get("citationCount"),
                        "paper_id": paper.get("paperId")
                    }
                )
            )

        return SearchResponse(
            query=query,
            search_type=SearchType.PAPERS,
            results=results,
            total_results=data.get("total", len(results)),
            provider="semantic_scholar"
        )

    async def _search_arxiv(self, query: str, limit: int) -> SearchResponse:
        clean_query = query.replace(" ", "+")
        url = f"http://export.arxiv.org/api/query?search_query=all:{clean_query}&start=0&max_results={limit}"

        try:
            async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
                response = await client.get(url)
                response.raise_for_status()
                xml_text = response.text
        except httpx.TimeoutException as e:
            raise SearchProviderAPIError(f"ArXiv API request timed out: {e}") from e
        except httpx.HTTPError as e:
            raise SearchProviderAPIError(f"ArXiv API HTTP error: {e}") from e
        except Exception as e:
            raise SearchProviderAPIError(f"ArXiv paper search failed: {e}") from e

        results: list[SearchResult] = []
        try:
            # Parse Atom XML feed
            namespace = {"atom": "http://www.w3.org/2005/Atom"}
            root = ET.fromstring(xml_text)
            entries = root.findall("atom:entry", namespace)
            for entry in entries[:limit]:
                title = entry.findtext("atom:title", default="Untitled Paper", namespaces=namespace).strip().replace("\n", " ")
                summary = entry.findtext("atom:summary", default="", namespaces=namespace).strip().replace("\n", " ")
                published = entry.findtext("atom:published", default=None, namespaces=namespace)
                paper_id = entry.findtext("atom:id", default="", namespaces=namespace)
                
                authors = [a.findtext("atom:name", default="", namespaces=namespace) for a in entry.findall("atom:author", namespace)]
                
                pdf_link = entry.find("atom:link[@title='pdf']", namespace)
                link_elem = pdf_link if pdf_link is not None else entry.find("atom:link", namespace)
                link_url = link_elem.attrib.get("href", paper_id) if link_elem is not None else paper_id

                results.append(
                    SearchResult(
                        title=title,
                        url=link_url,
                        snippet=summary,
                        source="ArXiv",
                        published_at=published,
                        result_type=SearchType.PAPERS,
                        metadata={"authors": authors, "arxiv_id": paper_id}
                    )
                )
        except Exception as e:
            logger.warning(f"Error parsing ArXiv XML response: {e}")

        return SearchResponse(
            query=query,
            search_type=SearchType.PAPERS,
            results=results,
            total_results=len(results),
            provider="arxiv"
        )
