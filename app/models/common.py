from typing import Generic, TypeVar, Optional, Any, Dict
from datetime import datetime, timezone
from pydantic import BaseModel, Field

T = TypeVar('T')


class StandardAPIResponse(BaseModel, Generic[T]):
    """Standardized API Response envelope for consistent API outputs."""
    status: str = Field(..., description="Response status: 'success', 'error', 'degraded', or 'unhealthy'")
    message: str = Field(..., description="Human readable response summary")
    data: Optional[T] = Field(default=None, description="Response payload")
    error: Optional[Dict[str, Any]] = Field(default=None, description="Detailed error information if status is not success")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="UTC timestamp of response")


class DatabaseHealthDetails(BaseModel):
    """MongoDB health status model."""
    connected: bool = Field(..., description="Whether database connection is active and responsive")
    database_name: str = Field(..., description="Target database name")
    error: Optional[str] = Field(default=None, description="Error message if disconnected")


class SystemHealthData(BaseModel):
    """System health status payload."""
    app_name: str
    version: str
    environment: str
    status: str = Field(..., description="'healthy', 'degraded', or 'unhealthy'")
    database: DatabaseHealthDetails
