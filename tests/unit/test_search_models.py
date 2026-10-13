import pytest
from app.search.models import SearchType, SearchResult, SearchResponse


def test_search_type_enum():
    assert SearchType.WEB == "web"
    assert SearchType.NEWS == "news"
    assert SearchType.TRENDS == "trends"
    assert SearchType.PAPERS == "papers"


def test_search_result_model_defaults():
    result = SearchResult(
        title="Test Title",
        url="https://example.com/test",
    )
    assert result.title == "Test Title"
    assert result.url == "https://example.com/test"
    assert result.snippet is None
    assert result.source is None
    assert result.published_at is None
    assert result.result_type == SearchType.WEB
    assert result.metadata == {}


def test_search_response_model():
    res1 = SearchResult(title="T1", url="https://example.com/1", snippet="Snippet 1")
    res2 = SearchResult(title="T2", url="https://example.com/2", snippet="Snippet 2")
    
    response = SearchResponse(
        query="python testing",
        search_type=SearchType.WEB,
        results=[res1, res2],
        total_results=2,
        provider="mock_provider",
        metadata={"search_time": 0.05}
    )
    
    assert response.query == "python testing"
    assert response.search_type == SearchType.WEB
    assert len(response.results) == 2
    assert response.total_results == 2
    assert response.provider == "mock_provider"
    
    dumped = response.model_dump()
    assert dumped["query"] == "python testing"
    assert dumped["search_type"] == "web"
    assert len(dumped["results"]) == 2
