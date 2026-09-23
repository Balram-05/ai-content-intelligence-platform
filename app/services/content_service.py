import uuid
from app.models.content import ContentGenerationRequest, ContentGenerationResponse
from app.core.logging import logger


class ContentService:
    """Service handling content generation workflow stub."""

    async def create_generation_stub(
        self, request: ContentGenerationRequest
    ) -> ContentGenerationResponse:
        """
        Creates a temporary stub run_id acknowledging the request (Phase 0).
        Real agent orchestration will be attached in Phase 1+.
        """
        run_id = f"run_{uuid.uuid4().hex[:8]}"
        logger.info(
            f"[STUB] Generated content run_id='{run_id}' for topic='{request.topic}' "
            f"on platforms={request.platforms}"
        )
        
        return ContentGenerationResponse(
            run_id=run_id,
            status="queued",
            message="[STUB] Content generation request acknowledged. Phase 0 stub endpoint.",
            requested_topic=request.topic,
            platforms=request.platforms
        )
