from fastapi import Depends
from app.core.config import Settings, get_settings
from app.core.database import Database, db_instance
from app.services.health_service import HealthService
from app.services.content_service import ContentService
from app.rag.ingestion import RAGIngestionService


def get_db() -> Database:
    """FastAPI Dependency supplying global Database manager."""
    return db_instance


def get_health_service(
    db: Database = Depends(get_db),
    settings: Settings = Depends(get_settings)
) -> HealthService:
    """FastAPI Dependency injecting HealthService."""
    return HealthService(db=db, settings=settings)


def get_content_service(
    db: Database = Depends(get_db),
    settings: Settings = Depends(get_settings)
) -> ContentService:
    """FastAPI Dependency injecting ContentService."""
    return ContentService(db=db, settings=settings)


def get_rag_ingestion_service() -> RAGIngestionService:
    """FastAPI Dependency injecting RAGIngestionService."""
    return RAGIngestionService()

