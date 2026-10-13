from enum import Enum
from typing import Any
from pydantic import BaseModel, Field


class SearchType(str, Enum):
    """Enumeration of supported search capabilities."""
    WEB = "web"
    NEWS = "news"
    TRENDS = "trends"
    PAPERS = "papers"


class SearchResult(BaseModel):
    """Normalized individual search result entry."""
    title: str
    url: str
    snippet: str | None = None
    source: str | None = None
    published_at: str | None = None
    result_type: SearchType = SearchType.WEB
    metadata: dict[str, Any] = Field(default_factory=dict)


class SearchResponse(BaseModel):
    """Normalized response payload for a search operation."""
    query: str
    search_type: SearchType
    results: list[SearchResult] = Field(default_factory=list)
    total_results: int = 0
    provider: str
    metadata: dict[str, Any] = Field(default_factory=dict)
