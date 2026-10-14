from fastapi import APIRouter
from app.api.v1.endpoints import health, content, knowledge, linkedin

api_v1_router = APIRouter()

api_v1_router.include_router(health.router, tags=["Health & Status"])
api_v1_router.include_router(content.router, tags=["Content Generation Stub"])
api_v1_router.include_router(knowledge.router, tags=["RAG Knowledge Ingestion"])
api_v1_router.include_router(linkedin.router, tags=["LinkedIn Integration"])


