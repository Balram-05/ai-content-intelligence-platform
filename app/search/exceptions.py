class SearchError(Exception):
    """Base exception for search domain operations."""
    pass


class InvalidSearchRequestError(SearchError):
    """Raised when a search request parameter or query is invalid."""
    pass


class SearchProviderConfigError(SearchError):
    """Raised when provider configuration or credentials (API keys) are missing or invalid."""
    pass


class SearchProviderAPIError(SearchError):
    """Raised when external search provider service fails, errors out, or times out."""
    pass


class SearchProviderNotFoundError(SearchError):
    """Raised when a requested search provider or search type is not supported."""
    pass
