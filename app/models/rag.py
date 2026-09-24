from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class KnowledgeIngestionResponse(BaseModel):
    """Pydantic response model for RAG knowledge ingestion endpoint."""
    document_id: str = Field(..., description="Unique deterministic SHA-256 hash ID of the ingested document")
    source: str = Field(..., description="Original filename or document title")
    total_pages: int = Field(..., description="Total pages processed from the PDF document")
    total_chunks: int = Field(..., description="Total text chunks generated and indexed into ChromaDB")
    collection_name: str = Field(..., description="Target ChromaDB vector collection name")
    status: str = Field("success", description="Status of ingestion execution")
    message: str = Field(..., description="Summary response message")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional ingestion metadata")
