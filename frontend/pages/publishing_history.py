import streamlit as st
from api_client import APIClient
from components.header import render_page_header


def render_publishing_history_page(client: APIClient) -> None:
    """Renders honest placeholder for future Publishing History feature."""
    render_page_header(
        title="Publishing History",
        subtitle="Chronological audit log and historical distribution records across connected social channels.",
        badge="Planned Feature",
    )

    st.markdown(
        """
        <div class="glass-card">
            <h3 style="margin-top: 0; color: #f8fafc;">📋 Module Under Development</h3>
            <p style="color: #94a3b8; font-size: 0.95rem; line-height: 1.6;">
                This module will provide a full chronological view of all posts published through the platform,
                querying the <code>published_posts</code> collection in MongoDB.
            </p>
            <div style="margin-top: 1rem;">
                <span class="status-badge status-badge-degraded">● Phase 2 Roadmap</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("#### Planned Architectural Capabilities:")
    st.markdown(
        """
        - **MongoDB Audit Trail**: Query past publications with `post_urn`, `author_urn`, and `published_at` timestamps.
        - **Workflow Run Traceability**: Deep link each post back to its specific LangGraph `run_id`, including research and strategy snapshots.
        - **Status Tracking**: Filter posts by status (`published`, `partial_save`, `failed`).
        - **CSV / JSON Export**: Export historical records for compliance and record-keeping.
        """
    )
