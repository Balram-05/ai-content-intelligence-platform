# AI Personal Branding & Content Intelligence Platform (Phase 0 Foundation)

An autonomous, multi-agent content intelligence system designed to automate the content lifecycle from topic/document research to multi-platform generation, fact-checking, editorial review, scheduling, and analytics.

> **Phase 0 Status**: Foundational slice implementation. Contains FastAPI gateway, async MongoDB database driver connection layer, centralized Pydantic settings, Streamlit frontend dashboard, structured logging, consistent API envelope, and automated test suite.

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