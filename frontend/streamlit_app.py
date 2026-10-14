import os
import sys
from pathlib import Path
import streamlit as st

# Ensure frontend directory is in python path for robust module imports
frontend_dir = Path(__file__).resolve().parent
if str(frontend_dir) not in sys.path:
    sys.path.insert(0, str(frontend_dir))

from api_client import APIClient
from styles import apply_global_styles
from components.header import render_app_branding
from pages.dashboard import render_dashboard_page
from pages.content_studio import render_content_studio_page
from pages.knowledge_base import render_knowledge_base_page
from pages.publishing_history import render_publishing_history_page
from pages.campaigns import render_campaigns_page
from pages.analytics import render_analytics_page
from pages.settings import render_settings_page


# -----------------------------------------------------------------------------
# Streamlit Application Page Configuration
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="AI Personal Branding & Content Intelligence Platform",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Apply unified styling (indigo/violet accents, dark mode cards, badges)
apply_global_styles()

# -----------------------------------------------------------------------------
# Shared State & API Client Initialization
# -----------------------------------------------------------------------------
if "fastapi_base_url" not in st.session_state:
    st.session_state["fastapi_base_url"] = os.getenv("FASTAPI_BASE_URL", "http://127.0.0.1:8000")

client = APIClient(base_url=st.session_state["fastapi_base_url"])

# -----------------------------------------------------------------------------
# Sidebar Configuration & Telemetry Status
# -----------------------------------------------------------------------------
with st.sidebar:
    st.markdown(
        """
        <div style="padding-bottom: 0.5rem;">
            <div style="font-weight: 800; font-size: 1.15rem; background: linear-gradient(135deg, #6366f1, #a855f7); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
                ⚡ Content Intelligence
            </div>
            <div style="font-size: 0.75rem; color: #94a3b8; font-weight: 500; text-transform: uppercase; letter-spacing: 0.05em;">
                Personal Branding Engine
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.expander("⚙️ Gateway Connection", expanded=False):
        current_url = st.text_input(
            "Base URL",
            value=st.session_state["fastapi_base_url"],
            help="FastAPI server endpoint",
            key="sidebar_gateway_input",
        )
        if current_url.strip() != st.session_state["fastapi_base_url"]:
            st.session_state["fastapi_base_url"] = current_url.strip()
            client.base_url = current_url.strip()
            st.rerun()

    st.divider()

# -----------------------------------------------------------------------------
# Multipage Navigation Setup (Native st.navigation & st.Page)
# -----------------------------------------------------------------------------
pages = {
    "WORKSPACE": [
        st.Page(
            lambda: render_dashboard_page(client),
            title="Dashboard",
            icon=":material/dashboard:",
            default=True,
            url_path="dashboard",
        ),
        st.Page(
            lambda: render_content_studio_page(client),
            title="Content Studio",
            icon=":material/edit_document:",
            url_path="content-studio",
        ),
        st.Page(
            lambda: render_knowledge_base_page(client),
            title="Knowledge Base",
            icon=":material/menu_book:",
            url_path="knowledge-base",
        ),
    ],
    "MANAGEMENT": [
        st.Page(
            lambda: render_publishing_history_page(client),
            title="Publishing History",
            icon=":material/history:",
            url_path="publishing-history",
        ),
        st.Page(
            lambda: render_campaigns_page(client),
            title="Campaigns",
            icon=":material/campaign:",
            url_path="campaigns",
        ),
        st.Page(
            lambda: render_analytics_page(client),
            title="Analytics",
            icon=":material/analytics:",
            url_path="analytics",
        ),
    ],
    "CONFIGURATION": [
        st.Page(
            lambda: render_settings_page(client),
            title="Settings",
            icon=":material/settings:",
            url_path="settings",
        ),
    ],
}

nav = st.navigation(pages)

# -----------------------------------------------------------------------------
# Main Application Shell
# -----------------------------------------------------------------------------
# Render top branding banner
render_app_branding()
st.markdown("<hr style='margin: 0.5rem 0 1.5rem 0; border: none; border-top: 1px solid rgba(148, 163, 184, 0.15);'>", unsafe_allow_html=True)

# Execute current page
nav.run()

# Sidebar footer
with st.sidebar:
    st.divider()
    st.caption("🚀 **Phase 1B-3 Active**")
    st.caption("LangGraph · ChromaDB · Search MCP · LinkedIn")
