import os
from typing import Dict, Any, Optional, List
import httpx


class APIClient:
    """Streamlit HTTP Client communicating with FastAPI backend via httpx."""

    def __init__(self, base_url: Optional[str] = None, timeout: float = 30.0):
        self.base_url = (base_url or os.getenv("FASTAPI_BASE_URL", "http://127.0.0.1:8000")).rstrip("/")
        self.timeout = timeout

    # -------------------------------------------------------------------------
    # Core Health & System Telemetry
    # -------------------------------------------------------------------------

    def check_health(self) -> Dict[str, Any]:
        """Fetch backend health status from /api/v1/health."""
        url = f"{self.base_url}/api/v1/health"
        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.get(url)
                try:
                    data = response.json()
                except Exception:
                    data = {"raw_text": response.text}

                return {
                    "http_status": response.status_code,
                    "success": response.is_success,
                    "data": data,
                }
        except httpx.ConnectError:
            return {
                "http_status": 503,
                "success": False,
                "error": f"Unable to connect to FastAPI backend at {self.base_url}. Is FastAPI running?",
            }
        except httpx.TimeoutException:
            return {
                "http_status": 504,
                "success": False,
                "error": f"Request to FastAPI backend at {url} timed out after {self.timeout}s.",
            }
        except Exception as e:
            return {
                "http_status": 500,
                "success": False,
                "error": str(e),
            }

    # -------------------------------------------------------------------------
    # LinkedIn Integration & Publishing
    # -------------------------------------------------------------------------

    def get_linkedin_status(self) -> Dict[str, Any]:
        """Fetch LinkedIn connection status from GET /api/v1/linkedin/status."""
        url = f"{self.base_url}/api/v1/linkedin/status"
        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.get(url)
                try:
                    data = response.json()
                except Exception:
                    data = {"raw_text": response.text}

                return {
                    "http_status": response.status_code,
                    "success": response.is_success,
                    "data": data,
                }
        except httpx.ConnectError:
            return {
                "http_status": 503,
                "success": False,
                "error": f"Unable to connect to FastAPI backend at {self.base_url}.",
            }
        except httpx.TimeoutException:
            return {
                "http_status": 504,
                "success": False,
                "error": f"Request to {url} timed out after {self.timeout}s.",
            }
        except Exception as e:
            return {
                "http_status": 500,
                "success": False,
                "error": str(e),
            }

    def get_linkedin_auth_url(self) -> Dict[str, Any]:
        """Fetch LinkedIn OAuth authorization URL from GET /api/v1/linkedin/auth-url."""
        url = f"{self.base_url}/api/v1/linkedin/auth-url"
        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.get(url)
                try:
                    data = response.json()
                except Exception:
                    data = {"raw_text": response.text}

                return {
                    "http_status": response.status_code,
                    "success": response.is_success,
                    "data": data,
                }
        except httpx.ConnectError:
            return {
                "http_status": 503,
                "success": False,
                "error": f"Unable to connect to FastAPI backend at {self.base_url}.",
            }
        except httpx.TimeoutException:
            return {
                "http_status": 504,
                "success": False,
                "error": f"Request to {url} timed out after {self.timeout}s.",
            }
        except Exception as e:
            return {
                "http_status": 500,
                "success": False,
                "error": str(e),
            }

    def publish_from_topic(
        self,
        topic: str,
        tone: Optional[str] = "professional",
        audience: Optional[str] = "software developers",
        run_id: Optional[str] = None,
        timeout: float = 120.0,
    ) -> Dict[str, Any]:
        """
        Trigger end-to-end AI research, generation, and LinkedIn publishing
        via POST /api/v1/linkedin/publish-from-topic.

        Uses a dedicated long-running timeout because LangGraph multi-agent
        research, RAG retrieval, strategy, generation, and LinkedIn Posts REST API
        call can take 20-60 seconds.
        """
        url = f"{self.base_url}/api/v1/linkedin/publish-from-topic"
        payload = {
            "topic": topic,
            "tone": tone or "professional",
            "audience": audience or "software developers",
        }
        if run_id and run_id.strip():
            payload["run_id"] = run_id.strip()

        try:
            # Explicitly do NOT retry to avoid duplicate posts on LinkedIn
            with httpx.Client(timeout=timeout) as client:
                response = client.post(url, json=payload)
                try:
                    data = response.json()
                except Exception:
                    data = {"raw_text": response.text}

                return {
                    "http_status": response.status_code,
                    "success": response.is_success,
                    "data": data,
                }
        except httpx.ConnectError:
            return {
                "http_status": 503,
                "success": False,
                "error": f"Unable to connect to FastAPI backend at {self.base_url}. Is FastAPI running?",
            }
        except httpx.TimeoutException:
            return {
                "http_status": 504,
                "success": False,
                "error": (
                    f"Publishing request timed out after {timeout} seconds. The backend multi-agent workflow "
                    "or LinkedIn API may still be processing in the background. DO NOT immediately re-submit "
                    "to prevent duplicate posts on LinkedIn. Check your LinkedIn profile or refresh telemetry."
                ),
            }
        except Exception as e:
            return {
                "http_status": 500,
                "success": False,
                "error": f"Unexpected error during publishing: {str(e)}",
            }

    # -------------------------------------------------------------------------
    # Content Generation (Multi-Platform / Phase 1A)
    # -------------------------------------------------------------------------

    def generate_content(
        self,
        topic: str,
        platforms: List[str],
        audience: str = "AI engineers",
        tone: str = "technical",
        campaign_id: Optional[str] = None,
        source_url: Optional[str] = None,
        run_id: Optional[str] = None,
        timeout: float = 90.0,
    ) -> Dict[str, Any]:
        """Trigger POST /api/v1/content/generate agentic content workflow."""
        url = f"{self.base_url}/api/v1/content/generate"
        payload = {
            "topic": topic,
            "platforms": platforms,
            "audience": audience,
            "tone": tone,
        }
        if campaign_id:
            payload["campaign_id"] = campaign_id
        if source_url:
            payload["source_url"] = source_url
        if run_id:
            payload["run_id"] = run_id

        try:
            with httpx.Client(timeout=timeout) as client:
                response = client.post(url, json=payload)
                try:
                    data = response.json()
                except Exception:
                    data = {"raw_text": response.text}

                return {
                    "http_status": response.status_code,
                    "success": response.is_success,
                    "data": data,
                }
        except httpx.ConnectError:
            return {
                "http_status": 503,
                "success": False,
                "error": f"Unable to connect to FastAPI backend at {self.base_url}.",
            }
        except httpx.TimeoutException:
            return {
                "http_status": 504,
                "success": False,
                "error": f"Content generation timed out after {timeout}s.",
            }
        except Exception as e:
            return {
                "http_status": 500,
                "success": False,
                "error": str(e),
            }

    def trigger_content_generation_stub(
        self,
        topic: str,
        platforms: List[str],
        audience: str = "AI engineers",
        tone: str = "technical",
        campaign_id: Optional[str] = None,
        source_url: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Preserved for backwards compatibility with earlier frontend versions."""
        return self.generate_content(
            topic=topic,
            platforms=platforms,
            audience=audience,
            tone=tone,
            campaign_id=campaign_id,
            source_url=source_url,
        )

    # -------------------------------------------------------------------------
    # RAG Knowledge Subsystem
    # -------------------------------------------------------------------------

    def search_knowledge_base(
        self,
        query: str,
        top_k: int = 4,
    ) -> Dict[str, Any]:
        """Trigger POST /api/v1/knowledge/search endpoint."""
        url = f"{self.base_url}/api/v1/knowledge/search"
        payload = {
            "query": query,
            "top_k": top_k,
        }
        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(url, json=payload)
                try:
                    data = response.json()
                except Exception:
                    data = {"raw_text": response.text}

                return {
                    "http_status": response.status_code,
                    "success": response.is_success,
                    "data": data,
                }
        except httpx.ConnectError:
            return {
                "http_status": 503,
                "success": False,
                "error": f"Unable to connect to FastAPI backend at {self.base_url}.",
            }
        except httpx.TimeoutException:
            return {
                "http_status": 504,
                "success": False,
                "error": f"Request to {url} timed out after {self.timeout}s.",
            }
        except Exception as e:
            return {
                "http_status": 500,
                "success": False,
                "error": str(e),
            }


