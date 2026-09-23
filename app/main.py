from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.database import db_instance
from app.core.logging import logger
from app.api.v1.router import api_v1_router
from app.models.common import StandardAPIResponse

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown lifespan context manager."""
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION} ({settings.APP_ENV})...")
    # Initialize MongoDB connection pool
    await db_instance.connect()
    yield
    # Shutdown MongoDB connection pool
    await db_instance.disconnect()
    logger.info("Application shutdown complete.")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Backend API Gateway for AI Personal Branding & Content Intelligence Platform",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API v1 Router
app.include_router(api_v1_router, prefix=settings.API_V1_PREFIX)


@app.get("/", response_model=StandardAPIResponse[dict])
async def root():
    return StandardAPIResponse(
        status="success",
        message=f"Welcome to {settings.APP_NAME}",
        data={
            "version": settings.APP_VERSION,
            "docs_url": "/docs",
            "health_url": f"{settings.API_V1_PREFIX}/health"
        }
    )
