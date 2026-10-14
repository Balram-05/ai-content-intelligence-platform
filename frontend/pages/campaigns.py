import streamlit as st
from api_client import APIClient
from components.header import render_page_header


def render_campaigns_page(client: APIClient) -> None:
    """Renders honest placeholder for future Content Campaigns feature."""
    render_page_header(
        title="Content Campaigns",
        subtitle="Multi-week narrative planning, thematic series, and cross-platform scheduling.",
        badge="Planned Feature",
    )

    st.markdown(
        """
        <div class="glass-card">
            <h3 style="margin-top: 0; color: #f8fafc;">🎯 Module Under Development</h3>
            <p style="color: #94a3b8; font-size: 0.95rem; line-height: 1.6;">
                The Campaigns module will allow creators and engineering leaders to organize thought-leadership 
                efforts into structured thematic series (e.g. "30 Days of Agentic AI Patterns").
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
        - **Campaign Lifecycle Management**: Group multiple topic generations under a shared `campaign_id`.
        - **Cadence & Content Calendar**: Scheduled automated generation with configurable release cadences.
        - **Narrative Progression**: Multi-stage prompts that build on concepts introduced in prior campaign posts.
        - **Multi-Persona Voice Guidelines**: Tailor distinct tone profiles for technical vs founder personas.
        """
    )
