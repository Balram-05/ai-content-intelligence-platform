import streamlit as st
from typing import Optional


def render_app_branding() -> None:
    """Renders the main platform brand header with title and subtitle."""
    st.markdown(
        """
        <div>
            <div class="brand-header-title">AI Personal Branding & Content Intelligence Platform</div>
            <div class="brand-header-subtitle">Research. Create. Publish.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_page_header(title: str, subtitle: str, badge: Optional[str] = None) -> None:
    """
    Renders a unified page-level header with title, subtitle, and optional status badge.
    """
    badge_html = f'<span class="status-badge status-badge-published">{badge}</span>' if badge else ""
    st.markdown(
        f"""
        <div style="margin-bottom: 1.25rem;">
            <div style="display: flex; align-items: center; gap: 12px;">
                <h1 class="page-title" style="margin: 0;">{title}</h1>
                {badge_html}
            </div>
            <p class="page-description" style="margin-top: 0.25rem;">{subtitle}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
