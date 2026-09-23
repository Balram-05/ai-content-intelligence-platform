import uuid
from datetime import datetime, timezone
from typing import Optional

from app.models.content import ContentGenerationRequest, ContentGenerationResponse
from app.workflows.state import ContentState
from app.workflows.content_graph import run_content_generation_workflow
from app.core.database import Database
from app.core.config import Settings
from app.core.logging import logger


class ContentService:
    """Service handling Phase 1A agentic content generation pipeline."""

    def __init__(self, db: Optional[Database] = None, settings: Optional[Settings] = None):
        self.db = db
        self.settings = settings

    async def generate_content(
        self, request: ContentGenerationRequest
    ) -> ContentGenerationResponse:
        """
        Orchestrates Phase 1A LangGraph content generation workflow.
        1. Generates unique run_id
        2. Constructs initial ContentState
        3. Invokes LangGraph workflow (Supervisor -> Research -> Strategy -> Content Generator)
        4. Persists execution record to MongoDB
        5. Returns ContentGenerationResponse
        """
        run_id = f"run_{uuid.uuid4().hex[:8]}"
        logger.info(
            f"[CONTENT_SERVICE] Initializing generation workflow run_id='{run_id}' for topic='{request.topic}' "
            f"on platforms={request.platforms}"
        )

        initial_state: ContentState = {
            "topic": request.topic,
            "platforms": request.platforms,
            "audience": request.audience,
            "tone": request.tone,
            "source_url": request.source_url,
            "campaign_id": request.campaign_id,
            "research": None,
            "strategy": None,
            "generated_content": None,
            "next_step": None,
            "error": None
        }

        try:
            final_state = await run_content_generation_workflow(initial_state)
            status = "completed"
            message = "Content generation workflow completed successfully."
        except Exception as e:
            logger.error(f"[CONTENT_SERVICE] Error executing LangGraph workflow: {e}", exc_info=True)
            final_state = initial_state
            status = "failed"
            message = f"Content generation workflow failed: {str(e)}"

        # Prepare persistence record
        run_record = {
            "run_id": run_id,
            "topic": request.topic,
            "platforms": request.platforms,
            "audience": request.audience,
            "tone": request.tone,
            "source_url": request.source_url,
            "campaign_id": request.campaign_id,
            "status": status,
            "research": final_state.get("research"),
            "strategy": final_state.get("strategy"),
            "generated_content": final_state.get("generated_content"),
            "created_at": datetime.now(timezone.utc)
        }

        # Persist to MongoDB if database connection is available
        if self.db and self.db.db is not None:
            try:
                await self.db.db["content_generation_runs"].insert_one(run_record)
                logger.info(f"[CONTENT_SERVICE] Saved run_id='{run_id}' to MongoDB 'content_generation_runs'")
            except Exception as e:
                logger.warning(f"[CONTENT_SERVICE] Could not persist run_id='{run_id}' to MongoDB: {e}")
        else:
            logger.info(f"[CONTENT_SERVICE] MongoDB not connected; skipping DB persistence for run_id='{run_id}'")

        return ContentGenerationResponse(
            run_id=run_id,
            status=status,
            message=message,
            requested_topic=request.topic,
            platforms=request.platforms,
            generated_content=final_state.get("generated_content"),
            research=final_state.get("research"),
            strategy=final_state.get("strategy")
        )
