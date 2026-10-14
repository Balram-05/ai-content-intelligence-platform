import streamlit as st
from api_client import APIClient
from components.header import render_page_header
from components.status_cards import render_status_cards


def render_dashboard_page(client: APIClient) -> None:
    """
    Renders the Executive Dashboard:
    - Real-time service telemetry & integration health
    - LinkedIn account status
    - Architecture & Multi-Agent LangGraph workflow overview
    - Quick action links
    """
    render_page_header(
        title="Platform Dashboard",
        subtitle="Real-time architecture telemetry, database persistence status, and multi-agent pipeline monitoring.",
        badge="Phase 1B Production Ready",
    )

    # Top action bar with refresh control
    col_act1, col_act2 = st.columns([4, 1])
    with col_act2:
        if st.button("🔄 Refresh Telemetry", use_container_width=True, type="secondary"):
            st.rerun()

    # Telemetry Status Cards (Backend, DB, LinkedIn, LangGraph)
    telemetry = render_status_cards(client)

    st.markdown("---")

    # Call-to-action Banner
    st.markdown(
        """
        <div class="glass-card glass-card-accent" style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 16px;">
            <div>
                <h3 style="margin: 0; font-size: 1.2rem; color: #f8fafc;">🚀 Ready to Generate & Publish Content?</h3>
                <p style="margin: 0.25rem 0 0 0; color: #94a3b8; font-size: 0.9rem;">
                    Launch the <strong>Content Studio</strong> to run automated topic research, RAG context retrieval, strategy synthesis, and live LinkedIn publishing.
                </p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Workflow Overview & Architectural Map
    st.subheader("📐 Verified End-to-End Execution Sequence")
    st.caption("Current verified data flow for topic-to-LinkedIn publishing in Phase 1B.")

    st.markdown(
        """
        ```
        [Streamlit Frontend] (Content Studio Form)
                 │  HTTP POST /api/v1/linkedin/publish-from-topic
                 ▼
        [FastAPI Gateway] (Route: app/api/v1/endpoints/linkedin.py)
                 │
                 ├─► [Pre-flight Check] Validates active LinkedIn OAuth token
                 │
                 ├─► [ContentService] (app/services/content_service.py)
                 │         │
                 │         ▼
                 │   [LangGraph Multi-Agent Workflow] (app/workflows/content_graph.py)
                 │         │
                 │         ├─► [Supervisor Agent] (app/agents/supervisor.py)
                 │         ├─► [Research Agent] (Search MCP: Web, News, ArXiv, Trends)
                 │         ├─► [RAG Retrieval Agent] (ChromaDB + SentenceTransformers)
                 │         ├─► [Strategy Agent] (Audience framing & hook formulation)
                 │         └─► [Content Generator] (Groq / OpenAI LLM post authoring)
                 │
                 ├─► [LinkedInService] (app/services/linkedin_service.py)
                 │         │
                 │         ├─► [LinkedIn REST API] (https://api.linkedin.com/rest/posts)
                 │         │         └── Creates live commentary post on personal feed
                 │         │
                 │         └─► [MongoDB] (Collection: 'published_posts')
                 │                   └── Persists post_urn, run_id, text, and timestamp
                 │
                 ▼
        [Streamlit Frontend] ── Displays verified post_urn, publication status & metadata
        ```
        """
    )

    # Interactive Architecture Component Breakdown
    arch_tab1, arch_tab2, arch_tab3 = st.tabs(
        ["🤖 Multi-Agent Engine", "📚 RAG Subsystem", "💼 LinkedIn OAuth & Publishing"]
    )

    with arch_tab1:
        st.markdown(
            """
            - **Supervisor Node**: Centrally directs graph progression and state machine transitions.
            - **Research Agent**: Collects external insights via real-time Search MCP (ArXiv papers, Google News, GitHub Trends).
            - **Strategy Agent**: Synthesizes key takeaways, audience pain points, and viral formatting hooks.
            - **Content Generator Node**: Writes engaging, professional posts aligned with tone and audience parameters.
            """
        )

    with arch_tab2:
        st.markdown(
            """
            - **Vector Store**: Local ChromaDB embedded collection (`./.chroma`).
            - **Embedding Model**: `all-MiniLM-L6-v2` via SentenceTransformers.
            - **Ingestion Pipeline**: PDF extraction with overlap chunking (`POST /api/v1/knowledge/ingest`).
            - **Retrieval Engine**: Semantic vector similarity search (`POST /api/v1/knowledge/search`).
            """
        )

    with arch_tab3:
        st.markdown(
            """
            - **OAuth 2.0 with PKCE/State**: Anti-CSRF server-side state token verification.
            - **Scope**: `openid profile w_member_social` for personal profile publishing.
            - **Posts API**: Direct integration with LinkedIn's official `/rest/posts` protocol.
            - **Audit Trail**: Every publication records `post_urn`, `author_urn`, and `run_id` into MongoDB.
            """
        )

    # Raw health diagnostics expander (preserving existing feature)
    if telemetry.get("health", {}).get("success"):
        with st.expander("🔍 Gateway Health Payload (Raw Diagnostics)"):
            st.json(telemetry["health"].get("data", {}))
