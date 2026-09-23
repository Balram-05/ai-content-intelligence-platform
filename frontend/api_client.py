import os
from typing import Dict, Any, Optional
import httpx


class APIClient:
    """Streamlit HTTP Client communicating with FastAPI backend via httpx."""

    def __init__(self, base_url: Optional[str] = None, timeout: float = 5.0):
        self.base_url = base_url or os.getenv("FASTAPI_BASE_URL", "http://127.0.0.1:8000")
        self.timeout = timeout

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
                    "data": data
                }
        except httpx.ConnectError:
            return {
                "http_status": 503,
                "success": False,
                "error": f"Unable to connect to FastAPI backend at {self.base_url}. Is FastAPI running?"
            }
        except httpx.TimeoutException:
            return {
                "http_status": 504,
                "success": False,
                "error": f"Request to FastAPI backend at {url} timed out after {self.timeout}s."
            }
        except Exception as e:
            return {
                "http_status": 500,
                "success": False,
                "error": str(e)
            }

    def trigger_content_generation_stub(
        self,
        topic: str,
        platforms: list[str],
        audience: str = "AI engineers",
        tone: str = "technical",
        campaign_id: Optional[str] = None,
        source_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """Trigger POST /api/v1/content/generate stub endpoint."""
        url = f"{self.base_url}/api/v1/content/generate"
        payload = {
            "topic": topic,
            "platforms": platforms,
            "audience": audience,
            "tone": tone,
            "campaign_id": campaign_id,
            "source_url": source_url
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
                    "data": data
                }
        except httpx.ConnectError:
            return {
                "http_status": 503,
                "success": False,
                "error": f"Unable to connect to FastAPI backend at {self.base_url}."
            }
        except Exception as e:
            return {
                "http_status": 500,
                "success": False,
                "error": str(e)
            }
