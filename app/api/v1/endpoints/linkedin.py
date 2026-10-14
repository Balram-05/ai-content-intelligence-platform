from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException, status

from app.models.common import StandardAPIResponse
from app.models.linkedin import (
    LinkedInAuthUrlResponse,
    LinkedInStatusResponse,
    LinkedInPublishRequest,
    LinkedInPublishResponse,
    LinkedInPublishFromTopicRequest,
    LinkedInTopicPublishResponse,
)
from app.services.linkedin_service import LinkedInService
from app.services.content_service import ContentService
from app.api.dependencies import get_linkedin_service, get_content_service
from app.core.logging import logger

router = APIRouter()


@router.get(
    "/linkedin/auth-url",
    response_model=StandardAPIResponse[LinkedInAuthUrlResponse],
    status_code=status.HTTP_200_OK,
    summary="Generate LinkedIn OAuth 2.0 Authorization URL",
    description="Generates a cryptographically random OAuth state token, stores it server-side, and returns the authorization URL."
)
async def get_linkedin_auth_url(
    linkedin_service: LinkedInService = Depends(get_linkedin_service)
) -> StandardAPIResponse[LinkedInAuthUrlResponse]:
    """Generates an OAuth authorization URL with anti-CSRF state token."""
    response_data = await linkedin_service.get_authorization_url()
    return StandardAPIResponse(
        status="success",
        message="LinkedIn OAuth authorization URL generated successfully.",
        data=response_data
    )


@router.get(
    "/linkedin/callback",
    response_model=StandardAPIResponse[LinkedInStatusResponse],
    status_code=status.HTTP_200_OK,
    summary="Handle LinkedIn OAuth 2.0 Callback",
    description="Validates state token, exchanges authorization code for an access token, fetches member profile via OpenID Connect, and saves credentials."
)
async def linkedin_oauth_callback(
    code: Optional[str] = Query(default=None, description="LinkedIn OAuth authorization code"),
    state: Optional[str] = Query(default=None, description="Anti-CSRF state token to validate"),
    error: Optional[str] = Query(default=None, description="LinkedIn error code if access denied"),
    error_description: Optional[str] = Query(default=None, description="LinkedIn error description"),
    linkedin_service: LinkedInService = Depends(get_linkedin_service)
) -> StandardAPIResponse[LinkedInStatusResponse]:
    """Processes OAuth redirect callback from LinkedIn."""
    if error:
        logger.warning(f"[API LinkedIn] User or provider rejected authorization: {error} - {error_description}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"LinkedIn authorization denied: {error_description or error}"
        )

    if not code or not state:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing required 'code' or 'state' parameters in LinkedIn callback."
        )

    response_data = await linkedin_service.handle_oauth_callback(code=code, state=state)
    return StandardAPIResponse(
        status="success",
        message="LinkedIn account authorized and connected successfully.",
        data=response_data
    )


@router.get(
    "/linkedin/status",
    response_model=StandardAPIResponse[LinkedInStatusResponse],
    status_code=status.HTTP_200_OK,
    summary="Check LinkedIn Connection Status",
    description="Returns whether an active, valid LinkedIn personal profile is linked without exposing any sensitive tokens."
)
async def get_linkedin_status(
    linkedin_service: LinkedInService = Depends(get_linkedin_service)
) -> StandardAPIResponse[LinkedInStatusResponse]:
    """Retrieves current LinkedIn connection status and linked profile metadata."""
    response_data = await linkedin_service.get_account_status()
    status_label = "connected" if response_data.connected else "disconnected"
    return StandardAPIResponse(
        status="success",
        message=f"LinkedIn status retrieved: {status_label}",
        data=response_data
    )


@router.post(
    "/linkedin/publish",
    response_model=StandardAPIResponse[LinkedInPublishResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Publish Text Post to Personal LinkedIn Profile",
    description="Publishes a text commentary post to the authorized member's profile via official LinkedIn Posts REST API and records execution to MongoDB."
)
async def publish_to_linkedin(
    request: LinkedInPublishRequest,
    linkedin_service: LinkedInService = Depends(get_linkedin_service)
) -> StandardAPIResponse[LinkedInPublishResponse]:
    """Publishes a text post to the authenticated personal LinkedIn profile."""
    response_data = await linkedin_service.publish_text_post(request)
    message = (
        response_data.warning
        if response_data.warning
        else "Post successfully published to your personal LinkedIn profile."
    )
    return StandardAPIResponse(
        status="success",
        message=message,
        data=response_data
    )


@router.post(
    "/linkedin/publish-from-topic",
    response_model=StandardAPIResponse[LinkedInTopicPublishResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Generate and Publish LinkedIn Post from Topic",
    description="Researches a topic, retrieves context via RAG, synthesizes strategy, generates a tailored post via LangGraph, and publishes it to LinkedIn."
)
async def publish_from_topic(
    request: LinkedInPublishFromTopicRequest,
    linkedin_service: LinkedInService = Depends(get_linkedin_service),
    content_service: ContentService = Depends(get_content_service),
) -> StandardAPIResponse[LinkedInTopicPublishResponse]:
    """Researches, generates, and publishes a text post to LinkedIn from a topic."""
    response_data = await linkedin_service.publish_from_topic(request, content_service)
    message = (
        response_data.warning
        if response_data.warning
        else "Post successfully generated and published to your personal LinkedIn profile."
    )
    return StandardAPIResponse(
        status="success",
        message=message,
        data=response_data
    )

