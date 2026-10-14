from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field, field_validator


class LinkedInAuthUrlResponse(BaseModel):
    """Payload returning LinkedIn OAuth authorization URL and state token."""
    authorization_url: str = Field(..., description="LinkedIn OAuth 2.0 authorization URL to redirect user")
    state: str = Field(..., description="Cryptographically random OAuth state token for CSRF protection")


class LinkedInAccountProfile(BaseModel):
    """Sanitized metadata representation of connected LinkedIn personal profile."""
    member_urn: str = Field(..., description="LinkedIn member URN, e.g. urn:li:person:abcdef1234")
    member_id: str = Field(..., description="LinkedIn member unique identifier (sub)")
    name: Optional[str] = Field(default=None, description="Member full display name")
    email: Optional[str] = Field(default=None, description="Member primary email address if available")
    picture: Optional[str] = Field(default=None, description="Profile picture URL if available")
    connected_at: datetime = Field(..., description="Timestamp when account was authorized")
    expires_at: Optional[datetime] = Field(default=None, description="Estimated access token expiration timestamp")


class LinkedInStatusResponse(BaseModel):
    """Response payload detailing LinkedIn connection status."""
    connected: bool = Field(..., description="True if an active, authorized LinkedIn personal profile is linked")
    account: Optional[LinkedInAccountProfile] = Field(default=None, description="Connected profile details if active")


class LinkedInPublishRequest(BaseModel):
    """Request payload to publish a text post to the connected personal LinkedIn profile."""
    text: str = Field(..., min_length=1, max_length=3000, description="Post commentary body text (1-3000 chars)")
    run_id: Optional[str] = Field(default=None, description="Optional workflow run ID linking generated content to post")
    topic: Optional[str] = Field(default=None, description="Optional topic for tracking generated content")

    @field_validator("text")
    @classmethod
    def validate_text_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Post text cannot be empty or contain only whitespace.")
        return v.strip()


class LinkedInPublishResponse(BaseModel):
    """Response payload confirming LinkedIn post publication."""
    post_urn: str = Field(..., description="Created LinkedIn post URN, e.g. urn:li:share:123456 or urn:li:rest:post:...")
    author_urn: str = Field(..., description="Author member URN representing the publisher")
    text: str = Field(..., description="Published text snippet")
    status: str = Field(default="published", description="Publishing status: 'published', 'failed', or 'partial_save'")
    run_id: Optional[str] = Field(default=None, description="Associated content generation run ID if provided")
    published_at: datetime = Field(..., description="UTC timestamp of post publication")
    warning: Optional[str] = Field(default=None, description="Warning message if post succeeded but persistence had issues")


class LinkedInPublishFromTopicRequest(BaseModel):
    """Request payload to generate and publish a LinkedIn post directly from a topic."""
    topic: str = Field(..., min_length=1, description="Target topic for AI research, content generation, and publishing")
    tone: Optional[str] = Field(default="professional", description="Desired content tone (e.g. professional, technical, conversational)")
    audience: Optional[str] = Field(default="software developers", description="Target audience demographic")
    run_id: Optional[str] = Field(default=None, description="Optional custom workflow run identifier")

    @field_validator("topic")
    @classmethod
    def validate_topic_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Topic cannot be empty or contain only whitespace.")
        return v.strip()

    @field_validator("tone", mode="before")
    @classmethod
    def default_tone_if_none(cls, v: Optional[str]) -> str:
        if v is None or not str(v).strip():
            return "professional"
        return str(v).strip()

    @field_validator("audience", mode="before")
    @classmethod
    def default_audience_if_none(cls, v: Optional[str]) -> str:
        if v is None or not str(v).strip():
            return "software developers"
        return str(v).strip()

    @field_validator("run_id", mode="before")
    @classmethod
    def clean_run_id(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        v_str = str(v).strip()
        return v_str if v_str else None


class LinkedInTopicPublishResponse(BaseModel):
    """Response payload returned when a post is generated from a topic and published to LinkedIn."""
    status: str = Field(default="published", description="Publishing status: 'published', 'failed', or 'partial_save'")
    topic: str = Field(..., description="Topic used for content generation")
    generated_text: str = Field(..., description="The AI-generated LinkedIn post text that was published")
    post_urn: str = Field(..., description="The LinkedIn post URN returned by the LinkedIn Posts API")
    author_urn: str = Field(..., description="Author member URN representing the publisher")
    run_id: str = Field(..., description="Workflow run ID associated with the content generation and publication")
    published_at: datetime = Field(..., description="UTC timestamp of post publication")
    warning: Optional[str] = Field(default=None, description="Warning message if post succeeded but persistence had issues")

