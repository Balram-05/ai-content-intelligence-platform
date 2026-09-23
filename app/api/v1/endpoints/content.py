from fastapi import APIRouter, Depends, status
from app.models.common import StandardAPIResponse
from app.models.content import ContentGenerationRequest, ContentGenerationResponse
from app.services.content_service import ContentService
from app.api.dependencies import get_content_service

router = APIRouter()


@router.post(
    "/content/generate",
    response_model=StandardAPIResponse[ContentGenerationResponse],
    status_code=status.HTTP_200_OK,
    summary="Trigger Phase 1A AI Content Generation Workflow",
    description="Triggers the Phase 1A agentic content generation pipeline (Supervisor -> Research -> Strategy -> Content Generator) and returns generated content."
)
async def generate_content(
    request: ContentGenerationRequest,
    content_service: ContentService = Depends(get_content_service)
) -> StandardAPIResponse[ContentGenerationResponse]:
    response_data = await content_service.generate_content(request)
    
    return StandardAPIResponse(
        status="success",
        message="Content generation workflow executed successfully",
        data=response_data
    )
