import re
import secrets
import urllib.parse
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any, List, Tuple

import httpx
from fastapi import HTTPException, status

from app.core.config import Settings, get_settings
from app.core.database import Database
from app.core.logging import logger
from app.models.content import ContentGenerationRequest
from app.models.linkedin import (
    LinkedInAuthUrlResponse,
    LinkedInAccountProfile,
    LinkedInStatusResponse,
    LinkedInPublishRequest,
    LinkedInPublishResponse,
    LinkedInPublishFromTopicRequest,
    LinkedInTopicPublishResponse,
)


class LinkedInService:
    """
    Service managing LinkedIn personal-profile OAuth 2.0 authorization,
    account metadata persistence, and text-only post publishing.
    """

    # In-memory fallbacks for development/testing when MongoDB is disconnected
    _in_memory_states: Dict[str, datetime] = {}
    _in_memory_accounts: Dict[str, Dict[str, Any]] = {}
    _in_memory_published_posts: List[Dict[str, Any]] = []

    def __init__(self, db: Optional[Database] = None, settings: Optional[Settings] = None):
        self.db = db
        self.settings = settings or get_settings()

    async def get_authorization_url(self) -> LinkedInAuthUrlResponse:
        """
        Generates a secure LinkedIn OAuth 2.0 authorization URL and saves
        a cryptographically random state token in the server-side state store.
        """
        if not self.settings.LINKEDIN_CLIENT_ID:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="LinkedIn Client ID (LINKEDIN_CLIENT_ID) is not configured."
            )

        # Generate cryptographically secure state token (32 bytes url-safe)
        state = secrets.token_urlsafe(32)
        ttl = self.settings.LINKEDIN_OAUTH_STATE_TTL_SECONDS
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=ttl)

        # Persist state token server-side to prevent CSRF and replay attacks
        await self._store_oauth_state(state, expires_at)

        params = {
            "response_type": "code",
            "client_id": self.settings.LINKEDIN_CLIENT_ID,
            "redirect_uri": self.settings.LINKEDIN_REDIRECT_URI,
            "state": state,
            "scope": self.settings.LINKEDIN_SCOPE,
        }
        auth_url = f"https://www.linkedin.com/oauth/v2/authorization?{urllib.parse.urlencode(params)}"

        logger.info("[LINKEDIN_SERVICE] Generated OAuth authorization URL and registered state token.")
        return LinkedInAuthUrlResponse(authorization_url=auth_url, state=state)

    async def handle_oauth_callback(self, code: str, state: str) -> LinkedInStatusResponse:
        """
        Validates the incoming OAuth state token, exchanges the authorization code for an
        access token, fetches the member profile via OpenID Connect, and saves the account.
        """
        if not state:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing required OAuth state parameter."
            )
        if not code:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing required OAuth authorization code."
            )

        # 1. Validate and immediately consume state token to prevent replay
        is_valid_state = await self._validate_and_consume_state(state)
        if not is_valid_state:
            logger.warning("[LINKEDIN_SERVICE] OAuth callback rejected due to invalid, expired, or replayed state.")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid, expired, or replayed OAuth state parameter."
            )

        # 2. Server-side code exchange
        token_data = await self._exchange_code_for_token(code)
        access_token = token_data.get("access_token")
        if not access_token:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="LinkedIn token exchange succeeded but no access token was returned."
            )

        expires_in = token_data.get("expires_in", 5184000)  # Standard LinkedIn 60-day token
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=int(expires_in))

        # 3. Retrieve member identity via OpenID Connect userinfo
        userinfo = await self._fetch_userinfo(access_token)
        sub = userinfo.get("sub")
        if not sub:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Failed to retrieve member identifier from LinkedIn userinfo."
            )

        member_urn = f"urn:li:person:{sub}"

        # 4. Save account metadata and token in MongoDB
        account_doc = {
            "account_id": member_urn,
            "member_urn": member_urn,
            "member_id": sub,
            "name": userinfo.get("name"),
            "email": userinfo.get("email"),
            "picture": userinfo.get("picture"),
            "access_token": access_token,
            "expires_in": expires_in,
            "expires_at": expires_at,
            "scope": token_data.get("scope", self.settings.LINKEDIN_SCOPE),
            "is_active": True,
            "connected_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        }

        await self._save_account(account_doc)
        logger.info(f"[LINKEDIN_SERVICE] Successfully authorized and stored LinkedIn account for member '{member_urn}'.")

        profile = LinkedInAccountProfile(
            member_urn=member_urn,
            member_id=sub,
            name=userinfo.get("name"),
            email=userinfo.get("email"),
            picture=userinfo.get("picture"),
            connected_at=account_doc["connected_at"],
            expires_at=expires_at,
        )

        return LinkedInStatusResponse(connected=True, account=profile)

    async def get_account_status(self) -> LinkedInStatusResponse:
        """
        Retrieves current LinkedIn connection status without exposing access tokens.
        """
        account = await self._get_active_account()
        if not account:
            return LinkedInStatusResponse(connected=False, account=None)

        # Check if the token has expired
        expires_at = account.get("expires_at")
        now_utc = datetime.now(timezone.utc)
        if expires_at and expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)

        is_expired = expires_at and expires_at < now_utc
        if is_expired:
            logger.info("[LINKEDIN_SERVICE] Active LinkedIn account token has expired.")
            return LinkedInStatusResponse(
                connected=False,
                account=LinkedInAccountProfile(
                    member_urn=account["member_urn"],
                    member_id=account["member_id"],
                    name=account.get("name"),
                    email=account.get("email"),
                    picture=account.get("picture"),
                    connected_at=account["connected_at"],
                    expires_at=expires_at,
                )
            )

        return LinkedInStatusResponse(
            connected=True,
            account=LinkedInAccountProfile(
                member_urn=account["member_urn"],
                member_id=account["member_id"],
                name=account.get("name"),
                email=account.get("email"),
                picture=account.get("picture"),
                connected_at=account["connected_at"],
                expires_at=expires_at,
            )
        )

    async def publish_text_post(self, request: LinkedInPublishRequest) -> LinkedInPublishResponse:
        """
        Publishes a text post to the authenticated user's personal LinkedIn profile
        via LinkedIn's official Posts API and records the result in MongoDB.
        """
        # 1. Retrieve active account
        account = await self._get_active_account()
        if not account:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No connected LinkedIn account found. Please authorize your account via /api/v1/linkedin/auth-url first."
            )

        # 2. Check token expiration
        expires_at = account.get("expires_at")
        now_utc = datetime.now(timezone.utc)
        if expires_at and expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)

        if expires_at and expires_at < now_utc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="LinkedIn access token has expired. Please re-authorize via /api/v1/linkedin/auth-url."
            )

        access_token = account["access_token"]
        member_urn = account["member_urn"]

        # 3. Construct official LinkedIn Posts API request
        # Format commentary to comply with LinkedIn Little Text Format specification
        # and prevent silent post truncation on LinkedIn's Posts API
        formatted_commentary, truncation_warning = self._format_linkedin_commentary(request.text)

        posts_url = "https://api.linkedin.com/rest/posts"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "LinkedIn-Version": self.settings.LINKEDIN_API_VERSION,
            "X-Restli-Protocol-Version": "2.0.0",
            "Content-Type": "application/json",
        }
        payload = {
            "author": member_urn,
            "commentary": formatted_commentary,
            "visibility": "PUBLIC",
            "distribution": {
                "feedDistribution": "MAIN_FEED",
                "targetEntities": [],
                "thirdPartyDistributionChannels": []
            },
            "lifecycleState": "PUBLISHED",
            "isReshareDisabledByAuthor": False,
        }

        logger.info(f"[LINKEDIN_SERVICE] Dispatching text post to LinkedIn Posts API for author '{member_urn}'...")

        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                response = await client.post(posts_url, json=payload, headers=headers)
        except httpx.TimeoutException:
            logger.error("[LINKEDIN_SERVICE] Request to LinkedIn Posts API timed out.")
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail="Request to LinkedIn Posts API timed out."
            )
        except Exception as e:
            logger.error(f"[LINKEDIN_SERVICE] Network error connecting to LinkedIn Posts API: {e}")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Network connection error contacting LinkedIn API."
            )

        # 4. Handle non-2xx LinkedIn response
        if response.status_code not in (200, 201):
            error_detail = self._extract_sanitized_linkedin_error(response)
            logger.error(
                f"[LINKEDIN_SERVICE] LinkedIn Posts API returned HTTP {response.status_code}: {error_detail}"
            )
            # Map status code appropriately
            if response.status_code == 401:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=f"LinkedIn authorization failed: {error_detail}"
                )
            elif response.status_code == 403:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"LinkedIn permission denied (ensure 'w_member_social' scope is granted): {error_detail}"
                )
            elif response.status_code == 429:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="LinkedIn API rate limit reached. Please try again later."
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=f"LinkedIn API error (HTTP {response.status_code}): {error_detail}"
                )

        # 5. Extract post URN from response headers or body
        post_urn = (
            response.headers.get("x-restli-id")
            or response.headers.get("x-linkedin-id")
        )
        if not post_urn:
            try:
                resp_json = response.json()
                post_urn = resp_json.get("id") or resp_json.get("urn")
            except Exception:
                post_urn = None

        if not post_urn:
            post_urn = f"urn:li:post:unknown_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"

        logger.info(f"[LINKEDIN_SERVICE] Successfully published post. Post URN: '{post_urn}'")

        # 6. Persist publishing record to MongoDB
        published_record = {
            "post_id": post_urn,
            "author_urn": member_urn,
            "text": request.text,
            "run_id": request.run_id,
            "topic": request.topic,
            "platform": "linkedin",
            "status": "published",
            "published_at": datetime.now(timezone.utc),
        }

        warning_msg = truncation_warning
        try:
            if self.db and self.db.db is not None:
                await self.db.db["published_posts"].insert_one(published_record)
                logger.info(f"[LINKEDIN_SERVICE] Persisted post '{post_urn}' to MongoDB collection 'published_posts'.")
            else:
                self._in_memory_published_posts.append(published_record)
                logger.info("[LINKEDIN_SERVICE] MongoDB not connected; stored post in-memory.")
        except Exception as db_err:
            logger.error(f"[LINKEDIN_SERVICE] Failed to persist published post to MongoDB: {db_err}")
            db_warning = (
                "Post was successfully published to LinkedIn, but saving the publication record to MongoDB failed. "
                "DO NOT blindly retry this action to avoid creating duplicate posts on your profile."
            )
            warning_msg = f"{warning_msg} {db_warning}".strip() if warning_msg else db_warning

        return LinkedInPublishResponse(
            post_urn=post_urn,
            author_urn=member_urn,
            text=request.text,
            status="published",
            run_id=request.run_id,
            published_at=published_record["published_at"],
            warning=warning_msg,
        )

    async def publish_from_topic(
        self,
        request: LinkedInPublishFromTopicRequest,
        content_service: Any,
    ) -> LinkedInTopicPublishResponse:
        """
        Executes end-to-end AI-powered LinkedIn publishing:
        1. Pre-flight check: verifies active authorized LinkedIn profile exists and token is valid.
        2. Invokes ContentService / LangGraph workflow with topic, tone, audience, and platforms=['linkedin'].
        3. Extracts and validates the generated LinkedIn content.
        4. Publishes via LinkedIn Posts REST API and persists publication record.
        5. Returns structured publishing confirmation.
        """
        # 1. Pre-flight check: Ensure user is authorized before running AI pipeline
        account = await self._get_active_account()
        if not account:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No connected LinkedIn account found. Please authorize your account via /api/v1/linkedin/auth-url before generating and publishing content."
            )

        expires_at = account.get("expires_at")
        now_utc = datetime.now(timezone.utc)
        if expires_at and expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)

        if expires_at and expires_at < now_utc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="LinkedIn access token has expired. Please re-authorize via /api/v1/linkedin/auth-url."
            )

        # 2. Trigger existing ContentService / LangGraph workflow
        logger.info(
            f"[LINKEDIN_SERVICE] Initiating automated content generation for topic='{request.topic}' "
            f"audience='{request.audience}' tone='{request.tone}'..."
        )
        gen_request = ContentGenerationRequest(
            topic=request.topic,
            audience=request.audience,
            tone=request.tone,
            platforms=["linkedin"],
            run_id=request.run_id,
            campaign_id=request.run_id,
        )

        try:
            gen_response = await content_service.generate_content(gen_request)
        except Exception as e:
            logger.error(f"[LINKEDIN_SERVICE] Content generation execution failed: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Content generation workflow failed: {str(e)}"
            )

        if gen_response.status != "completed" or not gen_response.generated_content:
            logger.error(f"[LINKEDIN_SERVICE] Content generation returned failure state: {gen_response.message}")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Content generation workflow failed: {gen_response.message}"
            )

        # 3. Extract and validate generated LinkedIn post text
        post_text = self._extract_linkedin_post_text(gen_response.generated_content)
        if not post_text:
            logger.error("[LINKEDIN_SERVICE] Content generator returned empty text for LinkedIn.")
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Generated content for LinkedIn was empty or invalid."
            )

        if len(post_text) > 3000:
            logger.warning(
                f"[LINKEDIN_SERVICE] Generated post length ({len(post_text)}) exceeds 3000 chars. "
                "Truncating cleanly to 3000 characters while preserving full post structure."
            )
            cutoff = 2997
            last_space = post_text.rfind(" ", 0, cutoff)
            last_newline = post_text.rfind("\n", 0, cutoff)
            best_break = max(last_space, last_newline)
            if best_break > cutoff * 0.8:
                post_text = post_text[:best_break].rstrip() + "..."
            else:
                post_text = post_text[:cutoff].rstrip() + "..."

        run_id = gen_response.run_id or request.run_id or f"run_{secrets.token_hex(4)}"

        # 4. Dispatch to existing publish_text_post
        publish_req = LinkedInPublishRequest(
            text=post_text,
            run_id=run_id,
            topic=request.topic,
        )
        pub_result = await self.publish_text_post(publish_req)

        # 5. Return structured response
        return LinkedInTopicPublishResponse(
            status=pub_result.status,
            topic=request.topic,
            generated_text=post_text,
            post_urn=pub_result.post_urn,
            author_urn=pub_result.author_urn,
            run_id=run_id,
            published_at=pub_result.published_at,
            warning=pub_result.warning,
        )

    # -------------------------------------------------------------------------
    # Internal Helpers (Private)
    # -------------------------------------------------------------------------

    @classmethod
    def _format_linkedin_commentary(cls, text: str, max_chars: int = 3000) -> Tuple[str, Optional[str]]:
        """
        Formats and escapes text for LinkedIn Posts API (Little Text Format),
        preventing silent post truncation caused by unescaped markup delimiters.

        Official reserved characters per LinkedIn Posts API (little format):
          | { } @ [ ] ( ) < > # \\ * _ ~

        Rules:
        1. Valid hashtags (e.g. #PromptEngineering, #AIProduction) are preserved as HashtagElements.
           Stray hashes (e.g. '# ', '## Header', 'C#') are escaped as \\#.
        2. Other reserved characters (|, {, }, @, [, ], (, ), <, >, *, _, ~, \\) are escaped
           with a backslash unless already escaped.
        3. Enforces LinkedIn's 3,000-character limit cleanly without breaking words or escape sequences.
        """
        if not text:
            return "", None

        # Normalize line breaks to unix \n
        normalized = text.replace("\r\n", "\n").replace("\r", "\n").strip()
        warning: Optional[str] = None

        # Pre-escape length check at clean boundary if excessively long
        if len(normalized) > max_chars:
            warning = (
                f"Content length ({len(normalized)} chars) exceeded LinkedIn's {max_chars}-character limit; "
                "it was cleanly truncated while preserving the post body."
            )
            cutoff = max_chars - 3
            last_space = normalized.rfind(" ", 0, cutoff)
            last_newline = normalized.rfind("\n", 0, cutoff)
            best_break = max(last_space, last_newline)
            if best_break > cutoff * 0.8:
                normalized = normalized[:best_break].rstrip() + "..."
            else:
                normalized = normalized[:cutoff].rstrip() + "..."

        # Protect valid hashtags using an alphanumeric token without reserved characters
        hashtags: List[str] = []
        def save_hashtag(m: re.Match) -> str:
            prefix = m.group(1)
            tag = m.group(2)
            hashtags.append(tag)
            return f"{prefix}LINKEDINHTTOKEN{len(hashtags)-1}ENDHT"

        text_with_tokens = re.sub(r'(^|[\s\n])(#[a-zA-Z0-9_]+)', save_hashtag, normalized)

        # Escape stray '#' that are not hashtags (e.g. '## heading', '# ', 'C#')
        text_with_tokens = re.sub(r'(?<!\\)#', r'\#', text_with_tokens)

        # Escape unescaped backslashes that are not already part of a valid escape sequence
        text_with_tokens = re.sub(r'\\(?![|{}@\[\]()<>#\\*_~])', r'\\\\', text_with_tokens)

        # Escape unescaped reserved Little Text characters: | { } @ [ ] ( ) < > * _ ~
        reserved_pattern = r'(?<!\\)([|{}@\[\]()<>*_~])'
        text_with_tokens = re.sub(reserved_pattern, r'\\\1', text_with_tokens)

        # Restore valid hashtags
        for idx, ht in enumerate(hashtags):
            text_with_tokens = text_with_tokens.replace(f"LINKEDINHTTOKEN{idx}ENDHT", ht)

        # Post-escape length check: escaping adds backslashes, so ensure strictly within max_chars
        if len(text_with_tokens) > max_chars:
            warning = (
                f"Formatted content length ({len(text_with_tokens)} chars) exceeded LinkedIn's {max_chars}-character limit; "
                "it was cleanly truncated to fit LinkedIn's API limits."
            )
            cutoff = max_chars - 3
            trimmed = text_with_tokens[:cutoff]
            # Avoid leaving a dangling trailing escape backslash
            trailing_slashes = len(trimmed) - len(trimmed.rstrip('\\'))
            if trailing_slashes % 2 == 1:
                trimmed = trimmed[:-1]
            text_with_tokens = trimmed.rstrip() + "..."

        return text_with_tokens, warning

    @staticmethod
    def _extract_linkedin_post_text(generated_content: Any) -> str:
        """
        Safely extracts and formats the LinkedIn post text from the workflow's generated_content payload.
        Handles structured dicts (with title, content, call_to_action, hashtags) and raw string formats.
        """
        if not generated_content:
            return ""

        if isinstance(generated_content, str):
            return generated_content.strip()

        if not isinstance(generated_content, dict):
            return str(generated_content).strip()

        # Find linkedin platform data (case-insensitive key search)
        linkedin_data = None
        for k, v in generated_content.items():
            if k.lower() == "linkedin":
                linkedin_data = v
                break

        # Fallback to dictionary itself if 'linkedin' key isn't top-level
        if linkedin_data is None:
            if any(k in generated_content for k in ("content", "text", "body", "post")):
                linkedin_data = generated_content
            else:
                return ""

        if isinstance(linkedin_data, str):
            return linkedin_data.strip()

        if not isinstance(linkedin_data, dict):
            return str(linkedin_data).strip()

        # Safely extract body text from string, list, or dict structures
        raw_body = (
            linkedin_data.get("content")
            or linkedin_data.get("body")
            or linkedin_data.get("text")
            or linkedin_data.get("post")
            or linkedin_data.get("description")
            or linkedin_data.get("message")
            or ""
        )
        if isinstance(raw_body, list):
            body = "\n\n".join(str(item).strip() for item in raw_body if item).strip()
        elif isinstance(raw_body, dict):
            body = (raw_body.get("text") or raw_body.get("content") or raw_body.get("body") or str(raw_body)).strip()
        else:
            body = str(raw_body).strip()

        raw_title = linkedin_data.get("title") or linkedin_data.get("headline") or ""
        title = str(raw_title).strip()

        raw_cta = (
            linkedin_data.get("call_to_action")
            or linkedin_data.get("cta")
            or linkedin_data.get("closing")
            or ""
        )
        cta = str(raw_cta).strip()

        hashtags = linkedin_data.get("hashtags") or []

        # Format hashtags
        if isinstance(hashtags, list):
            tag_tokens = [
                h.strip() if h.strip().startswith("#") else f"#{h.strip()}"
                for h in hashtags
                if isinstance(h, str) and h.strip()
            ]
            hashtags_str = " ".join(tag_tokens)
        elif isinstance(hashtags, str):
            hashtags_str = hashtags.strip()
        else:
            hashtags_str = ""

        # Compose full post
        sections = []
        if title and title not in body:
            sections.append(f"📌 {title}")
        if body:
            sections.append(body)
        if cta and cta not in body:
            sections.append(cta)
        if hashtags_str and hashtags_str not in body:
            sections.append(hashtags_str)

        return "\n\n".join(sections).strip()


    async def _store_oauth_state(self, state: str, expires_at: datetime) -> None:
        """Stores OAuth state in MongoDB or in-memory fallback."""
        if self.db and self.db.db is not None:
            try:
                await self.db.db["oauth_states"].insert_one({
                    "state": state,
                    "created_at": datetime.now(timezone.utc),
                    "expires_at": expires_at,
                })
                return
            except Exception as e:
                logger.warning(f"[LINKEDIN_SERVICE] Could not persist OAuth state to MongoDB: {e}")

        self._in_memory_states[state] = expires_at

    async def _validate_and_consume_state(self, state: str) -> bool:
        """
        Validates whether state exists and has not expired.
        Immediately deletes it to prevent replay.
        """
        now = datetime.now(timezone.utc)

        # 1. Check MongoDB if active
        if self.db and self.db.db is not None:
            try:
                state_doc = await self.db.db["oauth_states"].find_one({"state": state})
                if state_doc:
                    await self.db.db["oauth_states"].delete_one({"state": state})
                    exp = state_doc.get("expires_at")
                    if exp:
                        if exp.tzinfo is None:
                            exp = exp.replace(tzinfo=timezone.utc)
                        if exp < now:
                            logger.warning("[LINKEDIN_SERVICE] Found expired OAuth state in MongoDB.")
                            return False
                    return True
            except Exception as e:
                logger.warning(f"[LINKEDIN_SERVICE] Error checking OAuth state in MongoDB: {e}")

        # 2. Check in-memory fallback
        if state in self._in_memory_states:
            exp = self._in_memory_states.pop(state)
            if exp < now:
                logger.warning("[LINKEDIN_SERVICE] In-memory OAuth state expired.")
                return False
            return True

        return False

    async def _exchange_code_for_token(self, code: str) -> Dict[str, Any]:
        """Exchanges authorization code for an OAuth access token via LinkedIn API."""
        if not self.settings.LINKEDIN_CLIENT_SECRET:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="LinkedIn Client Secret (LINKEDIN_CLIENT_SECRET) is not configured."
            )

        token_url = "https://www.linkedin.com/oauth/v2/accessToken"
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": self.settings.LINKEDIN_REDIRECT_URI,
            "client_id": self.settings.LINKEDIN_CLIENT_ID,
            "client_secret": self.settings.LINKEDIN_CLIENT_SECRET,
        }

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.post(
                    token_url,
                    data=data,
                    headers={"Content-Type": "application/x-www-form-urlencoded"}
                )
        except Exception as e:
            logger.error(f"[LINKEDIN_SERVICE] Network error during token exchange: {e}")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Network connection error communicating with LinkedIn OAuth server."
            )

        if resp.status_code != 200:
            error_detail = self._extract_sanitized_linkedin_error(resp)
            logger.error(f"[LINKEDIN_SERVICE] Token exchange failed with status {resp.status_code}: {error_detail}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"LinkedIn token exchange failed: {error_detail}"
            )

        return resp.json()

    async def _fetch_userinfo(self, access_token: str) -> Dict[str, Any]:
        """Fetches authenticated member details via OpenID Connect userinfo endpoint."""
        userinfo_url = "https://api.linkedin.com/v2/userinfo"
        headers = {"Authorization": f"Bearer {access_token}"}

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.get(userinfo_url, headers=headers)
        except Exception as e:
            logger.error(f"[LINKEDIN_SERVICE] Network error fetching userinfo: {e}")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Network connection error contacting LinkedIn userinfo endpoint."
            )

        if resp.status_code != 200:
            error_detail = self._extract_sanitized_linkedin_error(resp)
            logger.error(f"[LINKEDIN_SERVICE] Userinfo request failed with status {resp.status_code}: {error_detail}")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Failed to fetch LinkedIn profile userinfo: {error_detail}"
            )

        return resp.json()

    async def _save_account(self, account_doc: Dict[str, Any]) -> None:
        """Persists connected LinkedIn account document into MongoDB or in-memory fallback."""
        if self.db and self.db.db is not None:
            try:
                # Deactivate previously active accounts to ensure single active personal profile
                await self.db.db["linkedin_accounts"].update_many(
                    {"member_urn": {"$ne": account_doc["member_urn"]}},
                    {"$set": {"is_active": False}}
                )
                await self.db.db["linkedin_accounts"].update_one(
                    {"member_urn": account_doc["member_urn"]},
                    {"$set": account_doc},
                    upsert=True
                )
                return
            except Exception as e:
                logger.warning(f"[LINKEDIN_SERVICE] Could not persist LinkedIn account to MongoDB: {e}")

        # In-memory fallback
        for key in self._in_memory_accounts:
            self._in_memory_accounts[key]["is_active"] = False
        self._in_memory_accounts[account_doc["member_urn"]] = account_doc

    async def _get_active_account(self) -> Optional[Dict[str, Any]]:
        """Finds the most recently updated active LinkedIn account."""
        if self.db and self.db.db is not None:
            try:
                account = await self.db.db["linkedin_accounts"].find_one(
                    {"is_active": True},
                    sort=[("updated_at", -1)]
                )
                if account:
                    return account
            except Exception as e:
                logger.warning(f"[LINKEDIN_SERVICE] Error reading LinkedIn account from MongoDB: {e}")

        # In-memory fallback
        for acc in self._in_memory_accounts.values():
            if acc.get("is_active"):
                return acc
        return None

    def _extract_sanitized_linkedin_error(self, resp: httpx.Response) -> str:
        """Safely parses error detail from response body without exposing secrets or credentials."""
        try:
            body = resp.json()
            if isinstance(body, dict):
                # LinkedIn REST errors typically return {"message": "...", "status": ...}
                # OAuth token errors return {"error": "...", "error_description": "..."}
                msg = body.get("message") or body.get("error_description") or body.get("error")
                if msg:
                    return str(msg)
        except Exception:
            pass
        return resp.text[:200] if resp.text else f"HTTP {resp.status_code}"
