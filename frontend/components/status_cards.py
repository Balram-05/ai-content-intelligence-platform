from typing import Dict, Any, Optional
import streamlit as st
from api_client import APIClient


def render_status_cards(client: APIClient, refresh_trigger: bool = False) -> Dict[str, Any]:
    """
    Renders telemetry status cards for:
    1. FastAPI Backend Gateway
    2. MongoDB Persistence Layer
    3. LinkedIn Account Integration
    4. AI Agentic Workflow Engine

    Uses actual responses from /api/v1/health and /api/v1/linkedin/status.
    Returns a dictionary of raw health and linkedin data for optional downstream use.
    """
    # Use cached check or call directly
    health_resp = client.check_health()
    linkedin_resp = client.get_linkedin_status()

    col1, col2, col3, col4 = st.columns(4)

    # -------------------------------------------------------------------------
    # Card 1: FastAPI Gateway
    # -------------------------------------------------------------------------
    with col1:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.caption("GATEWAY SERVICE")
        if health_resp["success"]:
            health_data = health_resp["data"].get("data", {})
            env = health_data.get("environment", "dev").upper()
            ver = health_data.get("version", "v1")
            st.metric(
                label="FastAPI Backend",
                value=f"HTTP {health_resp['http_status']}",
                delta=f"Online ({env})",
                delta_color="normal",
            )
            st.markdown(
                '<span class="status-badge status-badge-healthy">● Fully Operational</span>',
                unsafe_allow_html=True,
            )
        else:
            st.metric(
                label="FastAPI Backend",
                value=f"HTTP {health_resp.get('http_status', 'N/A')}",
                delta="Offline / Unreachable",
                delta_color="inverse",
            )
            st.markdown(
                '<span class="status-badge status-badge-disconnected">● Disconnected</span>',
                unsafe_allow_html=True,
            )
        st.markdown("</div>", unsafe_allow_html=True)

    # -------------------------------------------------------------------------
    # Card 2: MongoDB Persistence
    # -------------------------------------------------------------------------
    with col2:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.caption("PERSISTENCE LAYER")
        if health_resp["success"]:
            health_data = health_resp["data"].get("data", {})
            db_info = health_data.get("database", {})
            is_connected = db_info.get("connected", False)
            db_name = db_info.get("database_name", "N/A")

            if is_connected:
                st.metric(
                    label="MongoDB Database",
                    value="Connected",
                    delta=f"DB: {db_name}",
                    delta_color="normal",
                )
                st.markdown(
                    '<span class="status-badge status-badge-healthy">● Connected</span>',
                    unsafe_allow_html=True,
                )
            else:
                st.metric(
                    label="MongoDB Database",
                    value="Degraded",
                    delta="Unreachable",
                    delta_color="inverse",
                )
                st.markdown(
                    '<span class="status-badge status-badge-degraded">● Degraded</span>',
                    unsafe_allow_html=True,
                )
        else:
            st.metric(
                label="MongoDB Database",
                value="Unknown",
                delta="Backend Offline",
                delta_color="off",
            )
            st.markdown(
                '<span class="status-badge status-badge-disconnected">● Unknown</span>',
                unsafe_allow_html=True,
            )
        st.markdown("</div>", unsafe_allow_html=True)

    # -------------------------------------------------------------------------
    # Card 3: LinkedIn Profile Integration
    # -------------------------------------------------------------------------
    with col3:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.caption("SOCIAL CHANNEL")
        if linkedin_resp["success"]:
            li_data = linkedin_resp["data"].get("data", {})
            is_li_connected = li_data.get("connected", False)
            account = li_data.get("account") or {}

            if is_li_connected:
                member_name = account.get("name") or account.get("member_id", "Authorized")
                st.metric(
                    label="LinkedIn Profile",
                    value="Connected",
                    delta=f"{member_name}",
                    delta_color="normal",
                )
                st.markdown(
                    '<span class="status-badge status-badge-healthy">● OAuth 2.0 Active</span>',
                    unsafe_allow_html=True,
                )
            else:
                st.metric(
                    label="LinkedIn Profile",
                    value="Not Linked",
                    delta="Auth Required",
                    delta_color="inverse",
                )
                st.markdown(
                    '<span class="status-badge status-badge-disconnected">● Disconnected</span>',
                    unsafe_allow_html=True,
                )
        else:
            st.metric(
                label="LinkedIn Profile",
                value="Unknown",
                delta="Backend Offline",
                delta_color="off",
            )
            st.markdown(
                '<span class="status-badge status-badge-disconnected">● Unreachable</span>',
                unsafe_allow_html=True,
            )
        st.markdown("</div>", unsafe_allow_html=True)

    # -------------------------------------------------------------------------
    # Card 4: AI Workflow Engine
    # -------------------------------------------------------------------------
    with col4:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.caption("ORCHESTRATION")
        if health_resp["success"]:
            st.metric(
                label="LangGraph Pipeline",
                value="Ready",
                delta="Supervisor & Agents",
                delta_color="normal",
            )
            st.markdown(
                '<span class="status-badge status-badge-published">● Phase 1B Verified</span>',
                unsafe_allow_html=True,
            )
        else:
            st.metric(
                label="LangGraph Pipeline",
                value="Unavailable",
                delta="Awaiting Gateway",
                delta_color="off",
            )
            st.markdown(
                '<span class="status-badge status-badge-disconnected">● Offline</span>',
                unsafe_allow_html=True,
            )
        st.markdown("</div>", unsafe_allow_html=True)

    # Contextual guidance if components are disconnected or degraded
    if health_resp["success"]:
        health_data = health_resp["data"].get("data", {})
        db_info = health_data.get("database", {})
        if not db_info.get("connected"):
            db_err = db_info.get("error", "Database connection lost.")
            st.warning(f"⚠️ **Database Warning**: MongoDB is degraded ({db_err}). In-memory fallback will be used by the backend.")

    if linkedin_resp["success"]:
        li_data = linkedin_resp["data"].get("data", {})
        if not li_data.get("connected"):
            auth_url_resp = client.get_linkedin_auth_url()
            auth_link = None
            if auth_url_resp.get("success"):
                auth_link = auth_url_resp.get("data", {}).get("data", {}).get("authorization_url")

            with st.container():
                st.markdown(
                    """
                    <div class="alert-callout alert-callout-warning">
                        <div>
                            <strong>LinkedIn Account Not Connected:</strong> To publish posts from the Content Studio,
                            authorize your personal profile via LinkedIn OAuth 2.0 with <code>w_member_social</code> scope.
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                if auth_link:
                    st.link_button("🔗 Authorize LinkedIn Profile (OAuth 2.0)", auth_link, type="secondary")
                else:
                    st.caption("Configure `LINKEDIN_CLIENT_ID` and `LINKEDIN_CLIENT_SECRET` in `.env` to activate OAuth linking.")
    elif not health_resp["success"]:
        st.error(f"❌ **FastAPI Backend Offline**: {health_resp.get('error', 'Unable to reach backend gateway.')}")
        st.info("Start the FastAPI server via: `uvicorn app.main:app --reload --host 127.0.0.1 --port 8000`")

    return {
        "health": health_resp,
        "linkedin": linkedin_resp,
    }
