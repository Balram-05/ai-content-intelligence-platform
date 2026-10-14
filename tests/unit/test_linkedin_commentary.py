import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone, timedelta
from httpx import Response

from app.services.linkedin_service import LinkedInService
from app.models.linkedin import LinkedInPublishRequest
from app.core.config import Settings


def test_format_linkedin_commentary_escapes_little_text_characters():
    """
    Verifies that LinkedIn Little Text Format reserved characters are properly escaped
    to prevent LinkedIn from silently truncating posts on the personal feed.
    """
    raw_text = (
        "📌 Prompt Engineering Hits the Wall 🚧 – Meet the Model Context Protocol (MCP)\n\n"
        "🔍 **Scaling LLMs with traditional prompt concatenation?**\n\n"
        "💡 **Enter MCP – a production‑ready contract for LLM context**\n\n"
        "⚙️ **Quick code glimpse (Python client)**\n"
        "```python\n"
        "payload={\"messages\": [...]}\n"
        "# send to downstream service\n"
        "```\n\n"
        "👉 [link placeholder]\n\n"
        "#ModelContextProtocol #AI_Production #TechTrends"
    )

    formatted, warning = LinkedInService._format_linkedin_commentary(raw_text)

    # 1. Headline parenthesis must be escaped
    assert r"\(MCP\)" in formatted, "Parentheses in headline (MCP) must be escaped as \\(MCP\\)"
    
    # 2. Markdown bold asterisks must be escaped
    assert r"\*\*Scaling LLMs" in formatted, "Bold asterisks must be escaped as \\*\\*"
    assert r"\(Python client\)" in formatted, "Parentheses in body must be escaped"

    # 3. Code block characters must be escaped
    assert r"\{" in formatted and r"\}" in formatted, "Braces in code block must be escaped"
    assert r"\[...\]" in formatted, "Brackets in code block must be escaped"
    assert r"\# send to downstream service" in formatted, "Stray hash in code comment must be escaped as \\#"

    # 4. Brackets in link placeholders must be escaped
    assert r"\[link placeholder\]" in formatted, "Brackets in [link placeholder] must be escaped"

    # 5. Valid hashtags must be preserved as clickable hashtags
    assert "#ModelContextProtocol" in formatted
    assert "#AI_Production" in formatted
    assert "#TechTrends" in formatted

    # 6. Warning must be None for normal length post
    assert warning is None


def test_format_linkedin_commentary_idempotency():
    """Formatting an already formatted commentary should not duplicate backslashes."""
    text = "Check out (MCP) with **bold**, {key: val}, [links], and #hashtag!"
    once, warn1 = LinkedInService._format_linkedin_commentary(text)
    twice, warn2 = LinkedInService._format_linkedin_commentary(once)

    assert once == twice, "Formatting must be idempotent and not re-escape existing escapes"
    assert warn1 == warn2


def test_format_linkedin_commentary_overlength_handling():
    """Overlength post (>3000 chars) must be cleanly truncated with a warning without breaking escapes."""
    long_text = "This is a sentence about AI agent architectures. " * 75
    assert len(long_text) > 3000

    formatted, warning = LinkedInService._format_linkedin_commentary(long_text, max_chars=3000)

    assert len(formatted) <= 3000
    assert formatted.endswith("...")
    assert warning is not None
    assert "exceeded LinkedIn's 3000-character limit" in warning


def test_extract_linkedin_post_text_handles_multiple_shapes():
    """Verifies that _extract_linkedin_post_text handles strings, dicts, lists, and alternative keys."""
    # Case A: Standard dictionary with title and content
    dict_payload = {
        "linkedin": {
            "title": "Agentic Workflows in 2026",
            "content": "Agents are reshaping modern software development from IDEs to CI/CD.",
            "call_to_action": "What is your take?",
            "hashtags": ["#AI", "SoftwareEngineering"],
        }
    }
    extracted_a = LinkedInService._extract_linkedin_post_text(dict_payload)
    assert "📌 Agentic Workflows in 2026" in extracted_a
    assert "Agents are reshaping modern software development" in extracted_a
    assert "What is your take?" in extracted_a
    assert "#AI #SoftwareEngineering" in extracted_a

    # Case B: Content as a list of paragraphs
    list_payload = {
        "linkedin": {
            "title": "Multi-agent systems",
            "body": ["Paragraph 1: Overview", "Paragraph 2: Deep dive", "Paragraph 3: Conclusion"],
            "cta": "Follow for more!",
            "hashtags": ["#Agents"],
        }
    }
    extracted_b = LinkedInService._extract_linkedin_post_text(list_payload)
    assert "📌 Multi-agent systems" in extracted_b
    assert "Paragraph 1: Overview" in extracted_b
    assert "Paragraph 2: Deep dive" in extracted_b
    assert "Follow for more!" in extracted_b

    # Case C: Title already inside body (should not duplicate title)
    dup_title_payload = {
        "linkedin": {
            "title": "Duplicate Check",
            "content": "Duplicate Check: here is the body of the post with more details.",
        }
    }
    extracted_c = LinkedInService._extract_linkedin_post_text(dup_title_payload)
    assert extracted_c.count("Duplicate Check") == 1


@pytest.mark.asyncio
async def test_publish_text_post_sends_full_escaped_payload():
    """
    Verifies that when publishing a full post with headline, body, code, poll, and hashtags,
    the exact JSON payload sent to LinkedIn Posts API retains the entire text (with proper escapes)
    rather than only the headline.
    """
    member_urn = "urn:li:person:mock_author_456"
    mock_settings = Settings(
        LINKEDIN_CLIENT_ID="mock_client_id",
        LINKEDIN_CLIENT_SECRET="mock_client_secret",
        LINKEDIN_REDIRECT_URI="http://127.0.0.1:8000/api/v1/linkedin/callback",
        LINKEDIN_API_VERSION="202502",
    )

    full_generated_text = (
        "📌 Prompt Engineering Hits the Wall 🚧 – Meet the Model Context Protocol (MCP)\n\n"
        "🔍 **Scaling LLMs with traditional prompt concatenation?**\n\n"
        "When you keep appending raw prompts, you quickly run into the 8k‑16k token ceiling.\n\n"
        "💡 **Enter MCP – a production‑ready contract for LLM context**\n\n"
        "1️⃣ Structured token management\n"
        "2️⃣ Stateless‑friendly serialization\n\n"
        "⚙️ **Quick code glimpse (Python client)**\n"
        "```python\n"
        "payload={\"messages\": [...]}\n"
        "```\n\n"
        "🗳️ **Poll:** What is your biggest latency pain point?\n\n"
        "👉 [link placeholder]\n\n"
        "#ModelContextProtocol #AIProduction #LLM"
    )

    service = LinkedInService(db=None, settings=mock_settings)
    service._in_memory_accounts[member_urn] = {
        "member_urn": member_urn,
        "member_id": "mock_author_456",
        "name": "Jane Developer",
        "access_token": "mock_access_token_xyz",
        "expires_at": datetime.now(timezone.utc) + timedelta(days=30),
        "is_active": True,
        "connected_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    }

    mock_resp = MagicMock(spec=Response)
    mock_resp.status_code = 201
    mock_resp.headers = {"x-restli-id": "urn:li:share:9988776655"}
    mock_resp.json.return_value = {"id": "urn:li:share:9988776655"}

    mock_client = AsyncMock()
    mock_client.post.return_value = mock_resp

    with patch("app.services.linkedin_service.httpx.AsyncClient") as mock_http_cls:
        mock_http_cls.return_value.__aenter__.return_value = mock_client

        req = LinkedInPublishRequest(
            text=full_generated_text,
            run_id="test_run_complete_post",
            topic="Model Context Protocol (MCP) in Production AI Agents",
        )
        response = await service.publish_text_post(req)

        assert response.status == "published"
        assert response.post_urn == "urn:li:share:9988776655"
        # User-facing readable text returned and stored retains original readability
        assert response.text == full_generated_text

        # Inspect the exact JSON payload dispatched to LinkedIn Posts API
        mock_client.post.assert_called_once()
        call_args = mock_client.post.call_args
        endpoint_url = call_args[0][0] if call_args[0] else call_args.kwargs.get("url")
        assert endpoint_url == "https://api.linkedin.com/rest/posts"

        sent_payload = call_args.kwargs.get("json", {})
        assert sent_payload.get("author") == member_urn
        commentary = sent_payload.get("commentary", "")

        # Verify that commentary is NOT just the headline:
        assert len(commentary) > 500, f"Commentary was unexpectedly truncated to {len(commentary)} chars!"
        assert r"\(MCP\)" in commentary, "Headline parentheses must be escaped in commentary"
        assert "Scaling LLMs with traditional prompt concatenation?" in commentary, "Paragraph 1 must be present"
        assert "Structured token management" in commentary, "Numbered points must be present"
        assert "payload=" in commentary, "Code example must be present"
        assert "Poll:" in commentary, "Poll section must be present"
        assert "#ModelContextProtocol" in commentary, "Hashtags must be present"
