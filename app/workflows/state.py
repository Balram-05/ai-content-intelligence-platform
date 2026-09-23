from typing import TypedDict, Optional, List, Dict, Any


class ContentState(TypedDict, total=False):
    """
    LangGraph state schema for Phase 1A content generation workflow.
    """
    topic: str
    platforms: List[str]
    audience: Optional[str]
    tone: Optional[str]
    source_url: Optional[str]
    campaign_id: Optional[str]
    research: Optional[Dict[str, Any]]
    strategy: Optional[Dict[str, Any]]
    generated_content: Optional[Dict[str, Any]]
    next_step: Optional[str]
    error: Optional[str]
