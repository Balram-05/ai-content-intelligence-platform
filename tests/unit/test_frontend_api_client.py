import pytest
from unittest.mock import patch, MagicMock
import httpx
from frontend.api_client import APIClient


@pytest.fixture
def client():
    return APIClient(base_url="http://127.0.0.1:8000", timeout=5.0)


def test_client_init_strips_trailing_slash():
    c = APIClient(base_url="http://127.0.0.1:8000/")
    assert c.base_url == "http://127.0.0.1:8000"


def test_check_health_success(client):
    mock_resp = MagicMock(spec=httpx.Response)
    mock_resp.status_code = 200
    mock_resp.is_success = True
    mock_resp.json.return_value = {"status": "success", "data": {"status": "healthy"}}

    with patch("httpx.Client.get", return_value=mock_resp):
        res = client.check_health()
        assert res["http_status"] == 200
        assert res["success"] is True
        assert res["data"]["data"]["status"] == "healthy"


def test_check_health_connect_error(client):
    with patch("httpx.Client.get", side_effect=httpx.ConnectError("Connection refused")):
        res = client.check_health()
        assert res["http_status"] == 503
        assert res["success"] is False
        assert "Unable to connect" in res["error"]


def test_get_linkedin_status_success(client):
    mock_resp = MagicMock(spec=httpx.Response)
    mock_resp.status_code = 200
    mock_resp.is_success = True
    mock_resp.json.return_value = {"status": "success", "data": {"connected": True}}

    with patch("httpx.Client.get", return_value=mock_resp):
        res = client.get_linkedin_status()
        assert res["http_status"] == 200
        assert res["success"] is True
        assert res["data"]["data"]["connected"] is True


def test_publish_from_topic_payload_and_success(client):
    mock_resp = MagicMock(spec=httpx.Response)
    mock_resp.status_code = 201
    mock_resp.is_success = True
    mock_resp.json.return_value = {
        "status": "success",
        "data": {
            "status": "published",
            "topic": "AI Agents",
            "generated_text": "Great post about agents!",
            "post_urn": "urn:li:share:12345",
            "author_urn": "urn:li:person:auth1",
            "run_id": "run_999",
            "published_at": "2026-10-14T11:00:00Z",
            "warning": None,
        },
    }

    with patch("httpx.Client.post") as mock_post:
        mock_post.return_value = mock_resp
        res = client.publish_from_topic(
            topic="AI Agents",
            tone="technical",
            audience="AI engineers",
            run_id="run_999",
            timeout=60.0,
        )

        assert res["http_status"] == 201
        assert res["success"] is True
        data = res["data"]["data"]
        assert data["post_urn"] == "urn:li:share:12345"
        assert data["status"] == "published"

        # Verify call arguments
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        assert args[0] == "http://127.0.0.1:8000/api/v1/linkedin/publish-from-topic"
        assert kwargs["json"] == {
            "topic": "AI Agents",
            "tone": "technical",
            "audience": "AI engineers",
            "run_id": "run_999",
        }


def test_publish_from_topic_timeout_handling(client):
    with patch("httpx.Client.post", side_effect=httpx.TimeoutException("Timed out")):
        res = client.publish_from_topic(topic="AI Agents", timeout=10.0)
        assert res["http_status"] == 504
        assert res["success"] is False
        assert "DO NOT immediately re-submit" in res["error"]


def test_search_knowledge_base_success(client):
    mock_resp = MagicMock(spec=httpx.Response)
    mock_resp.status_code = 200
    mock_resp.is_success = True
    mock_resp.json.return_value = {
        "status": "success",
        "data": {
            "query": "LangGraph",
            "total_results": 1,
            "results": [{"chunk_id": "c1", "text": "LangGraph is great", "distance": 0.1}],
        },
    }

    with patch("httpx.Client.post", return_value=mock_resp):
        res = client.search_knowledge_base(query="LangGraph", top_k=3)
        assert res["http_status"] == 200
        assert res["success"] is True
        assert res["data"]["data"]["total_results"] == 1
