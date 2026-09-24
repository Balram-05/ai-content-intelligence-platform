# AI Personal Branding & Content Intelligence Platform (Phase 0 Foundation)

An autonomous, multi-agent content intelligence system designed to automate the content lifecycle from topic/document research to multi-platform generation, fact-checking, editorial review, scheduling, and analytics.

> **Phase 0 & 1A Status**: Completed foundational architecture, FastAPI backend, MongoDB persistence, Streamlit UI, and LangGraph multi-agent orchestration (Supervisor, Research, Strategy, Content Generator) with Groq / OpenAI LLM support.
> **Phase 1B-1 Status**: RAG Knowledge Ingestion Foundation complete. Includes PDF document extraction, text chunking, Sentence Transformer embeddings, persistent local ChromaDB vector store, and document ingestion API.

---

## 📚 Phase 1B-1 RAG Knowledge Ingestion

The RAG ingestion pipeline processes PDF documents into vector embeddings for knowledge retrieval:

```
PDF Document ──► PDF Loader ──► Text Chunker ──► Sentence Transformer ──► Local ChromaDB
                 (pypdf)        (overlap)         (all-MiniLM-L6-v2)    (./.chroma)
```

### RAG Configuration Settings (`.env`)
- `CHROMA_PERSIST_DIR`: Local path for ChromaDB storage (default: `./.chroma`).
- `CHROMA_COLLECTION_NAME`: Target vector collection name (default: `knowledge_base`).
- `EMBEDDING_MODEL_NAME`: Sentence Transformer model (default: `all-MiniLM-L6-v2`).
- `RAG_CHUNK_SIZE`: Maximum characters per chunk (default: `1000`).
- `RAG_CHUNK_OVERLAP`: Overlapping characters between consecutive chunks (default: `200`).

### Ingestion API Endpoint
Upload a PDF document to store embeddings in ChromaDB:
- **URL**: `POST /api/v1/knowledge/ingest`
- **Content-Type**: `multipart/form-data`
- **Form Key**: `file` (PDF file)

#### Example Request (`cURL`):
```bash
curl -X POST "http://127.0.0.1:8000/api/v1/knowledge/ingest" \
     -H "accept: application/json" \
     -H "Content-Type: multipart/form-data" \
     -F "file=@sample_document.pdf;type=application/pdf"
```

#### Example Response:
```json
{
  "status": "success",
  "message": "PDF document 'sample_document.pdf' successfully ingested and indexed.",
  "data": {
    "document_id": "9f15b8b248c53a935885a6dfe8c8292c4c740c7cb70b413f6919651fe970d4af",
    "source": "sample_document.pdf",
    "total_pages": 4,
    "total_chunks": 12,
    "collection_name": "knowledge_base",
    "status": "success",
    "message": "Successfully ingested 'sample_document.pdf' into knowledge base.",
    "metadata": {
      "source": "sample_document.pdf",
      "total_pages": 4,
      "non_empty_pages": 4,
      "total_chunks": 12,
      "embedding_model": "all-MiniLM-L6-v2"
    }
  },
  "error": null,
  "timestamp": "2026-09-24T12:00:00Z"
}
```

---

## 📐 Target Architecture Breakdown

```
Streamlit Frontend UI (port 8501)
        │
        │ HTTP / JSON (httpx)
        ▼
FastAPI Backend Gateway (port 8000) [/api/v1]
        │
        ├─► Route Layer  (app/api/v1/endpoints/)
        │       │
        │       ▼
        ├─► Service Layer (app/services/)
        │       │
        │       ▼
        └─► Database Layer (app/core/database.py) ──► MongoDB (port 27017)
```

### Future Component Integration Points

- **`app/agents/`**: Future LangGraph agents (Supervisor, Research, Strategy, Content, Fact Verification, Critic, Publisher).
- **`app/workflows/`**: Future LangGraph workflow state graphs (`content_graph.py`).
- **`app/rag/`**: RAG knowledge retrieval pipeline (ChromaDB vector store, document loaders, chunking, BM25 + Vector hybrid retrieval).
- **`app/mcp/`**: Model Context Protocol (MCP) clients and tool servers (`search.py`, `linkedin.py`, `twitter.py`, etc.).
- **`app/workers/`**: Celery background task workers listening to Redis queues.

---

## 🛠️ Prerequisites & Installation

### 1. Prerequisites
- **Python 3.10+** (Tested on Python 3.13)
- **MongoDB** (Local instance running on `mongodb://localhost:27017` or via Docker)

### 2. Environment Setup & Dependency Installation

Create a Python virtual environment and install dependencies:

```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment (Windows PowerShell)
.venv\Scripts\activate

# Activate virtual environment (Linux/macOS)
# source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Environment Variables Configuration

Copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

Key environment variables:
- `MONGODB_URL`: MongoDB connection URI (default: `mongodb://localhost:27017`).
- `FASTAPI_HOST`: FastAPI binding host (default: `127.0.0.1`).
- `FASTAPI_PORT`: FastAPI binding port (default: `8000`).
- `FASTAPI_BASE_URL`: Base URL used by Streamlit to reach FastAPI (default: `http://127.0.0.1:8000`).

---

## 🚀 Running the Platform

### Step 1: Start MongoDB (If running locally)

Ensure MongoDB service is active locally or start a local container:

```bash
docker run -d --name mongodb -p 27017:27017 mongo:latest
```

### Step 2: Start FastAPI Backend Server

Run Uvicorn from the project root:

```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

- **Interactive API Docs (Swagger)**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **ReDoc Documentation**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)
- **Health Check Endpoint**: [http://127.0.0.1:8000/api/v1/health](http://127.0.0.1:8000/api/v1/health)

### Step 3: Start Streamlit Frontend Application

In a separate terminal window (with `.venv` activated):

```bash
streamlit run frontend/streamlit_app.py
```

- Access the Streamlit Dashboard at [http://localhost:8501](http://localhost:8501).

---

## 🧪 Running Automated Tests

Run pytest to verify configuration loading, health check schemas, database connection handling, and stub routes:

```bash
pytest -v
```

---

## 🐳 Docker Deployment (Optional / Secondary)

Orchestrate MongoDB, FastAPI, and Streamlit containers simultaneously using Docker Compose:

```bash
docker-compose up --build
```