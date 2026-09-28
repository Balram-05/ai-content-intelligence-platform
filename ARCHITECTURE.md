# Architecture & System Map — AI Personal Branding & Content Intelligence Platform

This document serves as the authoritative interface contract map for the **AI Personal Branding & Content Intelligence Platform**. It details system layout, directory responsibilities, interface contracts, Pydantic schemas, and workflow state definitions without redundant line-by-line implementation code.

---

## 1. Directory Structure & Component Responsibilities

| Directory / File | Core Responsibility |
| :--- | :--- |
| `app/agents/` | Autonomous LangGraph agent nodes (`supervisor`, `research_agent`, `strategy_agent`, `content_generator`). |
| `app/api/` | FastAPI dependency injection providers (`dependencies.py`). |
| `app/api/v1/` | API v1 router (`router.py`) and REST endpoint handlers (`health.py`, `content.py`, `knowledge.py`). |
| `app/core/` | Centralized system configuration (`config.py`), async MongoDB client manager (`database.py`), LLM factory provider (`llm.py`), and logger (`logging.py`). |
| `app/models/` | Pydantic data schemas for API requests/responses, system health, and RAG ingestion. |
| `app/rag/` | RAG Knowledge Retrieval & Ingestion foundation (PDF loader, text chunker, sentence embeddings, ChromaDB vector store, and orchestration pipeline). |
| `app/services/` | Business logic services (`content_service.py`, `health_service.py`). |
| `app/workflows/` | LangGraph state graph definitions (`content_graph.py`) and shared state schema (`state.py`). |
| `frontend/` | Streamlit user interface (`streamlit_app.py`) and HTTP API client wrapper (`api_client.py`). |
| `tests/` | Pytest automated test suite covering unit components (`unit/`) and API routes (`api/`). |

---

## 2. Configuration & Infrastructure Interfaces

### `app/core/config.py` — Centralized Settings Schema
```python
class Settings(BaseSettings):
    APP_NAME: str = "AI Personal Branding & Content Intelligence Platform"
    APP_VERSION: str = "0.1.0"
    APP_ENV: str = "development"
    LOG_LEVEL: str = "INFO"
    DEBUG: bool = False
    
    FASTAPI_HOST: str = "127.0.0.1"
    FASTAPI_PORT: int = 8000
    API_V1_PREFIX: str = "/api/v1"
    
    MONGODB_URL: str = "mongodb://localhost:27017"
    MONGODB_DB_NAME: str = "content_intelligence_db"
    MONGODB_MAX_CONNECTIONS: int = 10
    MONGODB_MIN_CONNECTIONS: int = 1
    MONGODB_CONNECT_TIMEOUT_MS: int = 5000

    LLM_PROVIDER: str = "groq"  # "groq" | "openai"
    OPENAI_API_KEY: str | None = None
    OPENAI_MODEL: str = "gpt-4o-mini"
    GROQ_API_KEY: str | None = None
    GROQ_MODEL: str = "llama-3.3-70b-versatile"

    CHROMA_PERSIST_DIR: str = "./.chroma"
    CHROMA_COLLECTION_NAME: str = "knowledge_base"
    EMBEDDING_MODEL_NAME: str = "all-MiniLM-L6-v2"
    RAG_CHUNK_SIZE: int = 1000
    RAG_CHUNK_OVERLAP: int = 200

def get_settings() -> Settings
```

### `app/core/database.py` — Database Manager
```python
class Database:
    async def connect(self) -> None
    async def disconnect(self) -> None
    async def check_health(self) -> Dict[str, Any]
```

### `app/core/llm.py` — LLM Factory Provider
```python
def get_llm() -> BaseChatModel
# Factory supplying ChatGroq or ChatOpenAI based on LLM_PROVIDER settings,
# with fallback to keyless MockLLM when valid API keys are missing.
```

---

## 3. Data Transfer Models & Pydantic Schemas

### Standard API Envelope (`app/models/common.py`)
```python
class StandardAPIResponse(BaseModel, Generic[T]):
    status: str          # "success" | "error" | "degraded" | "unhealthy"
    message: str
    data: Optional[T] = None
    error: Optional[Dict[str, Any]] = None
    timestamp: datetime
```

### Content Generation Request & Response (`app/models/content.py`)
```python
class ContentGenerationRequest(BaseModel):
    topic: str
    campaign_id: Optional[str] = None
    source_url: Optional[str] = None
    audience: Optional[str] = "AI engineers"
    tone: Optional[str] = "technical"
    platforms: List[str] = ["linkedin", "twitter"]

class ContentGenerationResponse(BaseModel):
    run_id: str
    status: str          # "completed" | "failed"
    message: str
    requested_topic: str
    platforms: List[str]
    generated_content: Optional[Dict[str, Any]] = None
    research: Optional[Dict[str, Any]] = None
    strategy: Optional[Dict[str, Any]] = None
```

### RAG Knowledge Schemas (`app/models/rag.py`)
```python
class KnowledgeIngestionResponse(BaseModel):
    document_id: str
    source: str
    total_pages: int
    total_chunks: int
    collection_name: str
    status: str = "success"
    message: str
    metadata: Optional[Dict[str, Any]] = {}

class KnowledgeSearchRequest(BaseModel):
    query: str                       # min_length=1
    top_k: Optional[int] = 4          # 1 <= top_k <= 50

class RetrievedChunk(BaseModel):
    chunk_id: str
    text: str
    metadata: Dict[str, Any]
    distance: float                  # Raw ChromaDB vector distance

class KnowledgeSearchResponse(BaseModel):
    query: str
    total_results: int
    results: list[RetrievedChunk]
```

---

## 4. LangGraph Multi-Agent Workflow Architecture

### Workflow State Schema (`app/workflows/state.py`)
```python
class ContentState(TypedDict, total=False):
    topic: str
    platforms: List[str]
    audience: Optional[str]
    tone: Optional[str]
    source_url: Optional[str]
    campaign_id: Optional[str]
    research: Optional[Dict[str, Any]]
    strategy: Optional[Dict[str, Any]]
    generated_content: Optional[Dict[str, Any]]
    next_step: Optional[str]
    error: Optional[str]
```

### LangGraph Workflow Topology (`app/workflows/content_graph.py`)
```
[START] ──► Supervisor
                 │
      ┌──────────┼──────────┐
      ▼          ▼          ▼
  Research    Strategy   Content Generator
      │          │          │
      └──────────┴──────────┘
                 │
                 ▼
             Supervisor ──► [END]
```

**Interface Contracts:**
```python
def build_content_workflow() -> CompiledStateGraph
async def run_content_generation_workflow(initial_state: ContentState) -> ContentState
```

**Agent Nodes (`app/agents/`):**
```python
async def supervisor_node(state: ContentState) -> Dict[str, Any]
def supervisor_router(state: ContentState) -> str
async def research_agent_node(state: ContentState) -> Dict[str, Any]
async def strategy_agent_node(state: ContentState) -> Dict[str, Any]
async def content_generator_node(state: ContentState) -> Dict[str, Any]
```

---

## 5. RAG Knowledge Ingestion & Retrieval Contracts (`app/rag/`)

### PDF Document Loader (`app/rag/loader.py`)
```python
class PDFDocumentLoader:
    def load_pdf_bytes(self, content_bytes: bytes, source_name: str) -> ExtractedDocument
    def load_pdf_file(self, file_path: Union[str, Path]) -> ExtractedDocument
```

### Text Chunker (`app/rag/chunker.py`)
```python
class TextChunker:
    def chunk_document(self, doc: ExtractedDocument) -> List[DocumentChunk]
```

### Sentence Transformer Embeddings (`app/rag/embeddings.py`)
```python
class SentenceTransformerEmbeddings:
    def embed_documents(self, texts: List[str]) -> List[List[float]]
    def embed_query(self, text: str) -> List[float]
    @property
    def dimension(self) -> int
```

### ChromaDB Vector Store (`app/rag/vector_store.py`)
```python
class ChromaVectorStore:
    def add_chunks(self, chunks: List[DocumentChunk], embeddings: List[List[float]]) -> int
    def query_similar(self, query_embedding: List[float], top_k: int = 4, where_filter: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]
    def get_collection_stats(self) -> Dict[str, Any]
    def delete_document(self, document_id: str) -> int
```

### End-to-End Ingestion Service (`app/rag/ingestion.py`)
```python
class RAGIngestionService:
    def ingest_pdf_bytes(self, content_bytes: bytes, source_name: str) -> IngestionResult
    def ingest_pdf_file(self, file_path: Union[str, Path]) -> IngestionResult
```

### Retrieval Service (`app/rag/retrieval.py`)
```python
class RAGRetrievalService:
    def search(self, query: str, top_k: int = 4, where_filter: Optional[Dict[str, Any]] = None, distance_threshold: Optional[float] = None) -> RetrievalResultPayload
```
*Applies configurable cosine distance threshold filtering (`RAG_DISTANCE_THRESHOLD`, default `0.6`) to discard irrelevant nearest-neighbor matches.*

---

## 6. REST API Endpoint Specifications (`app/api/v1/`)

| Method | Endpoint Route | Request Payload | Response Model | Description |
| :--- | :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/health` | None | `StandardAPIResponse[SystemHealthData]` | Returns backend app health and MongoDB ping status. |
| `POST` | `/api/v1/content/generate` | `ContentGenerationRequest` (JSON) | `StandardAPIResponse[ContentGenerationResponse]` | Triggers LangGraph multi-agent content generation pipeline. |
| `POST` | `/api/v1/knowledge/ingest` | `file: UploadFile` (Multipart PDF) | `StandardAPIResponse[KnowledgeIngestionResponse]` | Extracts, chunks, embeds, and indexes PDF into ChromaDB. |
| `POST` | `/api/v1/knowledge/search` | `KnowledgeSearchRequest` (JSON) | `StandardAPIResponse[KnowledgeSearchResponse]` | Performs vector similarity search against ChromaDB knowledge chunks. |

---

## 7. Frontend Interface Contract (`frontend/`)

### API Client Wrapper (`frontend/api_client.py`)
```python
class APIClient:
    def check_health(self) -> Dict[str, Any]
    def generate_content(
        self,
        topic: str,
        platforms: List[str],
        audience: Optional[str] = None,
        tone: Optional[str] = None,
        source_url: Optional[str] = None,
        campaign_id: Optional[str] = None
    ) -> Dict[str, Any]
    def ingest_knowledge_document(self, file_name: str, file_bytes: bytes) -> Dict[str, Any]
    def search_knowledge_base(self, query: str, top_k: int = 4) -> Dict[str, Any]
```

