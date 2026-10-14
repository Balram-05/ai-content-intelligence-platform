import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime, timezone, timedelta
from httpx import AsyncClient, Response

from app.core.config import Settings
from app.api.dependencies import get_settings, get_db
from app.main import app
from app.services.linkedin_service import LinkedInService


@pytest.fixture(autouse=True)
def reset_service_in_memory_state():
    """Reset LinkedInService in-memory test states between tests."""
    LinkedInService._in_memory_states.clear()
    LinkedInService._in_memory_accounts.clear()
    LinkedInService._in_memory_published_posts.clear()
    yield
    LinkedInService._in_memory_states.clear()
    LinkedInService._in_memory_accounts.clear()
    LinkedInService._in_memory_published_posts.clear()


@pytest.fixture
def mock_linkedin_settings():
    """Provides test settings with configured LinkedIn client credentials."""
    return Settings(
        LINKEDIN_CLIENT_ID="test_client_id_123",
        LINKEDIN_CLIENT_SECRET="test_client_secret_xyz",
        LINKEDIN_REDIRECT_URI="http://127.0.0.1:8000/api/v1/linkedin/callback",
        LINKEDIN_SCOPE="openid profile w_member_social",
        LINKEDIN_API_VERSION="202502",
        LINKEDIN_OAUTH_STATE_TTL_SECONDS=600,
    )


@pytest.mark.asyncio
async def test_auth_url_missing_client_id(async_client: AsyncClient):
    """Test GET /api/v1/linkedin/auth-url fails when LINKEDIN_CLIENT_ID is not configured."""
    app.dependency_overrides[get_settings] = lambda: Settings(LINKEDIN_CLIENT_ID=None)
    try:
        response = await async_client.get("/api/v1/linkedin/auth-url")
        assert response.status_code == 500
        assert "LINKEDIN_CLIENT_ID" in response.json()["detail"]
    finally:
        app.dependency_overrides.pop(get_settings, None)


@pytest.mark.asyncio
async def test_auth_url_generation_success(async_client: AsyncClient, mock_linkedin_settings: Settings):
    """Test GET /api/v1/linkedin/auth-url generates valid authorization URL and stores state."""
    app.dependency_overrides[get_settings] = lambda: mock_linkedin_settings
    try:
        response = await async_client.get("/api/v1/linkedin/auth-url")
        assert response.status_code == 200

        body = response.json()
        assert body["status"] == "success"
        data = body["data"]
        assert "authorization_url" in data
        assert "state" in data

        auth_url = data["authorization_url"]
        assert "https://www.linkedin.com/oauth/v2/authorization" in auth_url
        assert "client_id=test_client_id_123" in auth_url
        assert "response_type=code" in auth_url
        assert "redirect_uri=http%3A%2F%2F127.0.0.1%3A8000%2Fapi%2Fv1%2Flinkedin%2Fcallback" in auth_url
        assert "publishing" not in auth_url
        assert f"state={data['state']}" in auth_url
        assert "w_member_social" in auth_url

        # Check state is saved in service
        assert data["state"] in LinkedInService._in_memory_states
    finally:
        app.dependency_overrides.pop(get_settings, None)


@pytest.mark.asyncio
async def test_auth_url_normalizes_legacy_redirect_uri(async_client: AsyncClient):
    """Test that any legacy /publishing/ path prefix is automatically normalized to canonical route."""
    legacy_settings = Settings(
        LINKEDIN_CLIENT_ID="test_client_id_123",
        LINKEDIN_REDIRECT_URI="http://127.0.0.1:8000/api/v1/publishing/linkedin/callback"
    )
    # Verify Pydantic validator normalized the setting
    assert legacy_settings.LINKEDIN_REDIRECT_URI == "http://127.0.0.1:8000/api/v1/linkedin/callback"

    app.dependency_overrides[get_settings] = lambda: legacy_settings
    try:
        response = await async_client.get("/api/v1/linkedin/auth-url")
        assert response.status_code == 200
        auth_url = response.json()["data"]["authorization_url"]
        assert "redirect_uri=http%3A%2F%2F127.0.0.1%3A8000%2Fapi%2Fv1%2Flinkedin%2Fcallback" in auth_url
        assert "publishing" not in auth_url
    finally:
        app.dependency_overrides.pop(get_settings, None)



@pytest.mark.asyncio
async def test_oauth_callback_user_denied(async_client: AsyncClient, mock_linkedin_settings: Settings):
    """Test GET /api/v1/linkedin/callback handles error parameter when user rejects authorization."""
    app.dependency_overrides[get_settings] = lambda: mock_linkedin_settings
    try:
        response = await async_client.get(
            "/api/v1/linkedin/callback?error=user_cancelled_login&error_description=The+user+cancelled+the+login"
        )
        assert response.status_code == 400
        assert "denied" in response.json()["detail"].lower()
    finally:
        app.dependency_overrides.pop(get_settings, None)


@pytest.mark.asyncio
async def test_oauth_callback_invalid_or_expired_state(async_client: AsyncClient, mock_linkedin_settings: Settings):
    """Test GET /api/v1/linkedin/callback rejects missing, forged, or expired state parameter."""
    app.dependency_overrides[get_settings] = lambda: mock_linkedin_settings
    try:
        # 1. State never registered
        response = await async_client.get("/api/v1/linkedin/callback?code=fake_code&state=non_existent_state")
        assert response.status_code == 400
        assert "invalid" in response.json()["detail"].lower()

        # 2. State registered but expired
        LinkedInService._in_memory_states["expired_token"] = datetime.now(timezone.utc) - timedelta(seconds=10)
        response_exp = await async_client.get("/api/v1/linkedin/callback?code=fake_code&state=expired_token")
        assert response_exp.status_code == 400
        assert "invalid" in response_exp.json()["detail"].lower()
    finally:
        app.dependency_overrides.pop(get_settings, None)


@pytest.mark.asyncio
async def test_oauth_callback_success_and_replay_prevention(async_client: AsyncClient, mock_linkedin_settings: Settings):
    """Test full successful OAuth code exchange and verify replay prevention."""
    app.dependency_overrides[get_settings] = lambda: mock_linkedin_settings
    try:
        test_state = "valid_secure_state_123"
        LinkedInService._in_memory_states[test_state] = datetime.now(timezone.utc) + timedelta(minutes=10)

        mock_token_resp = MagicMock(spec=Response)
        mock_token_resp.status_code = 200
        mock_token_resp.json.return_value = {
            "access_token": "secret_access_token_abc123",
            "expires_in": 5184000,
            "scope": "openid profile w_member_social"
        }

        mock_userinfo_resp = MagicMock(spec=Response)
        mock_userinfo_resp.status_code = 200
        mock_userinfo_resp.json.return_value = {
            "sub": "user_xyz_789",
            "name": "Jane Doe",
            "email": "jane@example.com",
            "picture": "https://example.com/avatar.jpg"
        }

        mock_client = AsyncMock()
        mock_client.post.return_value = mock_token_resp
        mock_client.get.return_value = mock_userinfo_resp

        with patch("app.services.linkedin_service.httpx.AsyncClient") as mock_async_client_cls:
            mock_async_client_cls.return_value.__aenter__.return_value = mock_client

            response = await async_client.get(f"/api/v1/linkedin/callback?code=valid_auth_code&state={test_state}")
            assert response.status_code == 200

            body = response.json()
            assert body["status"] == "success"
            data = body["data"]
            assert data["connected"] is True
            account = data["account"]
            assert account["member_urn"] == "urn:li:person:user_xyz_789"
            assert account["name"] == "Jane Doe"
            assert account["email"] == "jane@example.com"

            # Security check: Never return access token
            assert "access_token" not in str(body)
            assert "secret_access_token_abc123" not in str(body)

            # Replay check: attempting to re-use the exact same state must fail with 400
            replay_response = await async_client.get(f"/api/v1/linkedin/callback?code=valid_auth_code&state={test_state}")
            assert replay_response.status_code == 400
    finally:
        app.dependency_overrides.pop(get_settings, None)


@pytest.mark.asyncio
async def test_linkedin_status_endpoint(async_client: AsyncClient, mock_linkedin_settings: Settings):
    """Test GET /api/v1/linkedin/status when disconnected vs connected."""
    app.dependency_overrides[get_settings] = lambda: mock_linkedin_settings
    try:
        # Disconnected
        res_disconn = await async_client.get("/api/v1/linkedin/status")
        assert res_disconn.status_code == 200
        assert res_disconn.json()["data"]["connected"] is False
        assert res_disconn.json()["data"]["account"] is None

        # Seed connected account
        member_urn = "urn:li:person:test_author"
        LinkedInService._in_memory_accounts[member_urn] = {
            "account_id": member_urn,
            "member_urn": member_urn,
            "member_id": "test_author",
            "name": "Alex Tech",
            "access_token": "secret_token_123",
            "expires_at": datetime.now(timezone.utc) + timedelta(days=30),
            "is_active": True,
            "connected_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        }

        res_conn = await async_client.get("/api/v1/linkedin/status")
        assert res_conn.status_code == 200
        body = res_conn.json()
        assert body["data"]["connected"] is True
        assert body["data"]["account"]["name"] == "Alex Tech"
        assert "secret_token_123" not in str(body)
    finally:
        app.dependency_overrides.pop(get_settings, None)


@pytest.mark.asyncio
async def test_publish_validation_errors(async_client: AsyncClient, mock_linkedin_settings: Settings):
    """Test POST /api/v1/linkedin/publish validates empty strings and character limits."""
    app.dependency_overrides[get_settings] = lambda: mock_linkedin_settings
    try:
        # 1. Whitespace only
        res_empty = await async_client.post("/api/v1/linkedin/publish", json={"text": "   "})
        assert res_empty.status_code == 422

        # 2. Exceeds max length (3000 chars)
        res_long = await async_client.post("/api/v1/linkedin/publish", json={"text": "A" * 3001})
        assert res_long.status_code == 422
    finally:
        app.dependency_overrides.pop(get_settings, None)


@pytest.mark.asyncio
async def test_publish_without_connected_account(async_client: AsyncClient, mock_linkedin_settings: Settings):
    """Test POST /api/v1/linkedin/publish fails if user is not authorized."""
    app.dependency_overrides[get_settings] = lambda: mock_linkedin_settings
    try:
        res = await async_client.post("/api/v1/linkedin/publish", json={"text": "Hello world!"})
        assert res.status_code == 400
        assert "authorize" in res.json()["detail"].lower()
    finally:
        app.dependency_overrides.pop(get_settings, None)


@pytest.mark.asyncio
async def test_publish_success_flow(async_client: AsyncClient, mock_linkedin_settings: Settings):
    """Test successful post publication through official LinkedIn Posts REST API."""
    app.dependency_overrides[get_settings] = lambda: mock_linkedin_settings
    try:
        member_urn = "urn:li:person:author_123"
        LinkedInService._in_memory_accounts[member_urn] = {
            "member_urn": member_urn,
            "member_id": "author_123",
            "name": "Jane Author",
            "access_token": "secret_valid_token",
            "expires_at": datetime.now(timezone.utc) + timedelta(days=20),
            "is_active": True,
            "connected_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        }

        mock_post_resp = MagicMock(spec=Response)
        mock_post_resp.status_code = 201
        mock_post_resp.headers = {
            "x-restli-id": "urn:li:share:7245891234567890123"
        }
        mock_post_resp.json.return_value = {"id": "urn:li:share:7245891234567890123"}

        mock_client = AsyncMock()
        mock_client.post.return_value = mock_post_resp

        with patch("app.services.linkedin_service.httpx.AsyncClient") as mock_async_client_cls:
            mock_async_client_cls.return_value.__aenter__.return_value = mock_client

            res = await async_client.post(
                "/api/v1/linkedin/publish",
                json={"text": "Exciting AI architectural updates!", "run_id": "run_001"}
            )
            assert res.status_code == 201

            body = res.json()
            assert body["status"] == "success"
            data = body["data"]
            assert data["post_urn"] == "urn:li:share:7245891234567890123"
            assert data["author_urn"] == member_urn
            assert data["text"] == "Exciting AI architectural updates!"
            assert data["run_id"] == "run_001"
            assert data["status"] == "published"

            # Verify request headers sent to LinkedIn Posts API
            call_args = mock_client.post.call_args
            assert call_args is not None
            sent_headers = call_args.kwargs.get("headers", {})
            assert sent_headers.get("LinkedIn-Version") == "202502"
            assert sent_headers.get("X-Restli-Protocol-Version") == "2.0.0"
            assert sent_headers.get("Authorization") == "Bearer secret_valid_token"
    finally:
        app.dependency_overrides.pop(get_settings, None)


@pytest.mark.asyncio
async def test_publish_api_permission_denied(async_client: AsyncClient, mock_linkedin_settings: Settings):
    """Test POST /api/v1/linkedin/publish handles 403 Forbidden with sanitized detail."""
    app.dependency_overrides[get_settings] = lambda: mock_linkedin_settings
    try:
        member_urn = "urn:li:person:author_123"
        LinkedInService._in_memory_accounts[member_urn] = {
            "member_urn": member_urn,
            "member_id": "author_123",
            "name": "Jane Author",
            "access_token": "secret_valid_token",
            "expires_at": datetime.now(timezone.utc) + timedelta(days=20),
            "is_active": True,
            "connected_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        }

        mock_post_resp = MagicMock(spec=Response)
        mock_post_resp.status_code = 403
        mock_post_resp.json.return_value = {
            "message": "Not enough permissions to access: POST-rest /posts",
            "status": 403
        }

        mock_client = AsyncMock()
        mock_client.post.return_value = mock_post_resp

        with patch("app.services.linkedin_service.httpx.AsyncClient") as mock_async_client_cls:
            mock_async_client_cls.return_value.__aenter__.return_value = mock_client

            res = await async_client.post(
                "/api/v1/linkedin/publish",
                json={"text": "Test post"}
            )
            assert res.status_code == 403
            assert "w_member_social" in res.json()["detail"]
    finally:
        app.dependency_overrides.pop(get_settings, None)


@pytest.mark.asyncio
async def test_publish_db_persistence_failure_warning(async_client: AsyncClient, mock_linkedin_settings: Settings):
    """Test POST /api/v1/linkedin/publish returns warning when DB persistence fails after post succeeds."""
    # Mock database insertion failure
    mock_db = MagicMock()
    mock_db.db = {
        "published_posts": MagicMock()
    }
    mock_db.db["published_posts"].insert_one = AsyncMock(side_effect=Exception("MongoDB connection lost"))

    app.dependency_overrides[get_settings] = lambda: mock_linkedin_settings
    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        member_urn = "urn:li:person:author_123"
        LinkedInService._in_memory_accounts[member_urn] = {
            "member_urn": member_urn,
            "member_id": "author_123",
            "name": "Jane Author",
            "access_token": "secret_valid_token",
            "expires_at": datetime.now(timezone.utc) + timedelta(days=20),
            "is_active": True,
            "connected_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        }

        mock_post_resp = MagicMock(spec=Response)
        mock_post_resp.status_code = 201
        mock_post_resp.headers = {"x-restli-id": "urn:li:share:987654321"}
        mock_post_resp.json.return_value = {"id": "urn:li:share:987654321"}

        mock_client = AsyncMock()
        mock_client.post.return_value = mock_post_resp

        with patch("app.services.linkedin_service.httpx.AsyncClient") as mock_async_client_cls:
            mock_async_client_cls.return_value.__aenter__.return_value = mock_client

            res = await async_client.post(
                "/api/v1/linkedin/publish",
                json={"text": "Test post that succeeds in API but fails in DB"}
            )
            assert res.status_code == 201
            body = res.json()
            assert body["data"]["status"] == "published"
            assert "DO NOT blindly retry" in body["data"]["warning"]
    finally:
        app.dependency_overrides.pop(get_settings, None)
        app.dependency_overrides.pop(get_db, None)


