import pytest
from unittest.mock import AsyncMock

from app.search.exceptions import InvalidSearchRequestError, SearchProviderNotFoundError
from app.search.models import SearchResponse, SearchResult, SearchType
from app.search.providers import BaseSearchProvider
from app.search.service import SearchService


class MockProvider(BaseSearchProvider):
    def __init__(self, name: str, s_type: SearchType):
        self._name = name
        self._s_type = s_type
        self.search_mock = AsyncMock()

    @property
    def provider_name(self) -> str:
        return self._name

    @property
    def search_type(self) -> SearchType:
        return self._s_type

    async def search(self, query: str, limit: int = 5, **kwargs) -> SearchResponse:
        await self.search_mock(query, limit)
        return SearchResponse(
            query=query,
            search_type=self._s_type,
            results=[
                SearchResult(title=f"Result for {query}", url="https://example.com")
            ],
            total_results=1,
            provider=self._name
        )


@pytest.mark.asyncio
async def test_search_service_validation_empty_query():
    service = SearchService()
    with pytest.raises(InvalidSearchRequestError, match="cannot be empty"):
        await service.search_web("")

    with pytest.raises(InvalidSearchRequestError, match="cannot be empty"):
        await service.search_news("   ")


@pytest.mark.asyncio
async def test_search_service_validation_invalid_limit():
    service = SearchService()
    with pytest.raises(InvalidSearchRequestError, match="at least 1"):
        await service.search_web("python", limit=0)


@pytest.mark.asyncio
async def test_search_service_mock_providers():
    web_mock = MockProvider("mock_web", SearchType.WEB)
    news_mock = MockProvider("mock_news", SearchType.NEWS)
    trends_mock = MockProvider("mock_trends", SearchType.TRENDS)
    papers_mock = MockProvider("mock_papers", SearchType.PAPERS)

    service = SearchService(providers={
        SearchType.WEB: web_mock,
        SearchType.NEWS: news_mock,
        SearchType.TRENDS: trends_mock,
        SearchType.PAPERS: papers_mock,
    })

    res_web = await service.search_web("AI news", limit=2)
    assert res_web.provider == "mock_web"
    assert res_web.search_type == SearchType.WEB
    web_mock.search_mock.assert_called_once_with("AI news", 2)

    res_news = await service.search_news("Tech news", limit=3)
    assert res_news.provider == "mock_news"
    assert res_news.search_type == SearchType.NEWS

    res_trends = await service.search_trends("Python trends", limit=1)
    assert res_trends.provider == "mock_trends"

    res_papers = await service.search_research_papers("Transformers", limit=5)
    assert res_papers.provider == "mock_papers"


@pytest.mark.asyncio
async def test_search_service_invalid_search_type():
    service = SearchService()
    with pytest.raises(InvalidSearchRequestError, match="Unsupported search_type"):
        await service.search("query", search_type="invalid_type")
