from typing import Dict, Any, Optional
from datetime import datetime
import streamlit as st


def render_post_preview(
    publish_result: Dict[str, Any],
    title: str = "Published LinkedIn Post",
) -> None:
    """
    Renders an elegant, comprehensive preview of a published LinkedIn post
    with full telemetry metadata, direct text copying, and warnings.
    """
    if not publish_result:
        st.info("No publication data to display.")
        return

    # Extract fields cleanly, handling both direct dict and StandardAPIResponse wrapped formats
    data = publish_result.get("data", publish_result)
    if isinstance(data, dict) and "data" in data and isinstance(data["data"], dict):
        data = data["data"]

    status = data.get("status", "published").upper()
    topic = data.get("topic", "N/A")
    generated_text = data.get("generated_text") or data.get("text", "")
    post_urn = data.get("post_urn", "N/A")
    author_urn = data.get("author_urn", "N/A")
    run_id = data.get("run_id", "N/A")
    published_at_raw = data.get("published_at")
    warning = data.get("warning")

    # Format timestamp
    published_at_str = "N/A"
    if published_at_raw:
        try:
            if isinstance(published_at_raw, str):
                dt = datetime.fromisoformat(published_at_raw.replace("Z", "+00:00"))
            elif isinstance(published_at_raw, datetime):
                dt = published_at_raw
            else:
                dt = None
            if dt:
                published_at_str = dt.strftime("%Y-%m-%d %H:%M:%S UTC")
        except Exception:
            published_at_str = str(published_at_raw)

    st.markdown('<div class="post-preview-container">', unsafe_allow_html=True)

    # Header with status badge
    st.markdown(
        f"""
        <div class="post-preview-header">
            <div>
                <span style="font-size: 1.15rem; font-weight: 700; color: #f8fafc;">
                    💼 {title}
                </span>
                <span style="margin-left: 8px; color: #94a3b8; font-size: 0.85rem;">
                    (Topic: <em>{topic}</em>)
                </span>
            </div>
            <div>
                <span class="status-badge status-badge-published">● {status}</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Persistence warning alert if present
    if warning:
        st.markdown(
            f"""
            <div class="alert-callout alert-callout-warning">
                <div>
                    <strong>Publication Persistence Warning:</strong> {warning}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Post content container
    st.markdown("**Post Content:**")
    st.markdown(
        f'<div class="post-preview-body">{generated_text}</div>',
        unsafe_allow_html=True,
    )

    # Copy utility
    with st.expander("📋 Copy Post Text (Raw Markdown)"):
        st.code(generated_text, language="markdown")

    # Metadata badges
    st.markdown(
        f"""
        <div style="margin-top: 1rem; border-top: 1px solid #1f2937; padding-top: 0.75rem;">
            <div style="font-size: 0.8rem; font-weight: 600; color: #94a3b8; margin-bottom: 0.5rem;">
                VERIFIED PUBLICATION TELEMETRY
            </div>
            <div>
                <span class="meta-pill">Post URN: {post_urn}</span>
                <span class="meta-pill">Run ID: {run_id}</span>
                <span class="meta-pill">Author URN: {author_urn}</span>
                <span class="meta-pill">Published: {published_at_str}</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("</div>", unsafe_allow_html=True)
