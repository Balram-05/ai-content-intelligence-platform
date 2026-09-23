from fastapi import APIRouter, Depends, status
from app.models.common import StandardAPIResponse
from app.models.content import ContentGenerationRequest, ContentGenerationResponse
from app.services.content_service import ContentService
from app.api.dependencies import get_content_service

router = APIRouter()


@router.post(
    "/content/generate",
    response_model=StandardAPIResponse[ContentGenerationResponse],
    status_code=status.HTTP_202_ACCEPTED,
    summary="[STUB] Trigger content generation workflow",
    description="Phase 0 stub endpoint accepting content generation request and returning run_id."
)
async def generate_content(
    request: ContentGenerationRequest,
    content_service: ContentService = Depends(get_content_service)
) -> StandardAPIResponse[ContentGenerationResponse]:
    stub_response = await content_service.create_generation_stub(request)
    
    return StandardAPIResponse(
        status="success",
        message="Content generation workflow queued (Phase 0 Stub)",
        data=stub_response
    )
