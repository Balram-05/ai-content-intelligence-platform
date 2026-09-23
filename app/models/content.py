from typing import List, Optional
from pydantic import BaseModel, Field


class ContentGenerationRequest(BaseModel):
    """
    Schema for content generation requests (PRD Section 5.5).
    Note: Phase 0 provides a stub endpoint only.
    """
    topic: str = Field(..., min_length=1, description="Target topic for content generation")
    campaign_id: Optional[str] = Field(default=None, description="Optional associated campaign ID")
    source_url: Optional[str] = Field(default=None, description="Optional source URL for context")
    audience: Optional[str] = Field(default="AI engineers", description="Target audience demographic")
    tone: Optional[str] = Field(default="technical", description="Desired content tone")
    platforms: List[str] = Field(
        default=["linkedin", "twitter"],
        description="Target social media platforms (e.g. linkedin, twitter, instagram, blog)"
    )


class ContentGenerationResponse(BaseModel):
    """
    Schema for content generation stub response (PRD Section 5.5).
    """
    run_id: str = Field(..., description="Unique execution workflow identifier")
    status: str = Field(default="queued", description="Workflow state: queued, running, completed, failed")
    message: str = Field(..., description="Status summary or warning")
    requested_topic: str = Field(..., description="Echo of input topic")
    platforms: List[str] = Field(..., description="Target platforms acknowledged")
