from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class ContentGenerationRequest(BaseModel):
    """
    Schema for content generation requests (PRD Section 5.5).
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
    Schema for content generation workflow response (PRD Section 5.5).
    """
    run_id: str = Field(..., description="Unique execution workflow identifier")
    status: str = Field(default="completed", description="Workflow state: queued, running, completed, failed")
    message: str = Field(..., description="Status summary or warning")
    requested_topic: str = Field(..., description="Echo of input topic")
    platforms: List[str] = Field(..., description="Target platforms acknowledged")
    generated_content: Optional[Dict[str, Any]] = Field(default=None, description="Generated content payload by platform")
    research: Optional[Dict[str, Any]] = Field(default=None, description="Structured research output")
    strategy: Optional[Dict[str, Any]] = Field(default=None, description="Structured strategy output")
