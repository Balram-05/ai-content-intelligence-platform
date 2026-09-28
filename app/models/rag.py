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


class KnowledgeSearchRequest(BaseModel):
    """Pydantic request model for RAG knowledge search endpoint."""
    query: str = Field(..., min_length=1, description="Natural language search query")
    top_k: Optional[int] = Field(default=4, ge=1, le=50, description="Number of top relevant chunks to retrieve (1-50)")


class RetrievedChunk(BaseModel):
    """Pydantic model representing a single retrieved text chunk with metadata and distance."""
    chunk_id: str = Field(..., description="Unique chunk identifier in vector store")
    text: str = Field(..., description="Text content of the retrieved chunk")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Chunk metadata including document_id, page_number, chunk_index, source")
    distance: float = Field(..., description="Raw vector distance from query vector (lower distance means higher semantic similarity)")


class KnowledgeSearchResponse(BaseModel):
    """Pydantic response model for RAG knowledge search endpoint."""
    query: str = Field(..., description="Echo of input natural language search query")
    total_results: int = Field(..., description="Total matching chunks retrieved")
    results: list[RetrievedChunk] = Field(default_factory=list, description="List of top-k retrieved text chunks")

