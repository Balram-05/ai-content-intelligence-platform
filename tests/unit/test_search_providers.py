import pytest
from unittest.mock import AsyncMock, patch
import httpx

from app.search.exceptions import SearchProviderConfigError, SearchProviderAPIError
from app.search.models import SearchType
from app.search.providers.web import WebSearchProvider
from app.search.providers.news import NewsSearchProvider
from app.search.providers.trends import TrendsSearchProvider
from app.search.providers.papers import PapersSearchProvider


@pytest.mark.asyncio
async def test_web_search_provider_missing_tavily_key(monkeypatch):
    monkeypatch.setattr("app.search.providers.web.get_settings", lambda: type("Settings", (), {
        "SEARCH_WEB_PROVIDER": "tavily",
        "TAVILY_API_KEY": None,
        "SERPER_API_KEY": None,
        "SEARCH_TIMEOUT_SECONDS": 5.0
    })())
    
    provider = WebSearchProvider(provider_name="tavily", api_key=None)
    with pytest.raises(SearchProviderConfigError, match="Tavily web search API key is missing"):
        await provider.search("python")


@pytest.mark.asyncio
async def test_news_search_provider_missing_newsapi_key(monkeypatch):
    monkeypatch.setattr("app.search.providers.news.get_settings", lambda: type("Settings", (), {
        "SEARCH_NEWS_PROVIDER": "newsapi",
        "NEWS_API_KEY": None,
        "SEARCH_TIMEOUT_SECONDS": 5.0
    })())

    provider = NewsSearchProvider(provider_name="newsapi", api_key=None)
    with pytest.raises(SearchProviderConfigError, match="NewsAPI key is missing"):
        await provider.search("latest tech news")


@pytest.mark.asyncio
async def test_papers_search_provider_arxiv_success():
    provider = PapersSearchProvider(provider_name="arxiv")
    mock_xml = """<?xml version="1.0" encoding="UTF-8"?>
    <feed xmlns="http://www.w3.org/2005/Atom">
        <entry>
            <title>Attention Is All You Need</title>
            <summary>Transformer paper summary text.</summary>
            <published>2017-06-12T00:00:00Z</published>
            <id>http://arxiv.org/abs/1706.03762v5</id>
            <author><name>Vaswani et al.</name></author>
            <link title="pdf" href="http://arxiv.org/pdf/1706.03762v5"/>
        </entry>
    </feed>
    """

    request = httpx.Request("GET", "http://export.arxiv.org/api/query")
    mock_response = httpx.Response(status_code=200, text=mock_xml, request=request)
    with patch.object(httpx.AsyncClient, "get", new_callable=AsyncMock, return_value=mock_response):
        response = await provider.search("transformers", limit=1)
        assert response.provider == "arxiv"
        assert response.search_type == SearchType.PAPERS
        assert len(response.results) == 1
        assert response.results[0].title == "Attention Is All You Need"
        assert response.results[0].url == "http://arxiv.org/pdf/1706.03762v5"


@pytest.mark.asyncio
async def test_trends_search_provider_github_success():
    provider = TrendsSearchProvider(provider_name="github_trends")
    mock_json = {
        "items": [
            {
                "full_name": "langchain-ai/langchain",
                "html_url": "https://github.com/langchain-ai/langchain",
                "description": "Building applications with LLMs through composability",
                "stargazers_count": 95000,
                "created_at": "2022-10-17T00:00:00Z",
                "language": "Python"
            }
        ]
    }

    request = httpx.Request("GET", "https://api.github.com/search/repositories")
    mock_response = httpx.Response(status_code=200, json=mock_json, request=request)
    with patch.object(httpx.AsyncClient, "get", new_callable=AsyncMock, return_value=mock_response):
        response = await provider.search("langchain", limit=1)
        assert response.provider == "github_trends"
        assert response.search_type == SearchType.TRENDS
        assert len(response.results) == 1
        assert "langchain-ai/langchain" in response.results[0].title
