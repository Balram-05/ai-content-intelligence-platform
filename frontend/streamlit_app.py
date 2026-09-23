import streamlit as st
from api_client import APIClient

st.set_page_config(
    page_title="AI Personal Branding Platform",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for rich aesthetics
st.markdown("""
    <style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        background: linear-gradient(135deg, #6366f1 0%, #a855f7 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        color: #6b7280;
        font-size: 1.05rem;
        margin-bottom: 2rem;
    }
    .card {
        border-radius: 12px;
        padding: 1.25rem;
        background-color: #1f2937;
        color: #f3f4f6;
        border: 1px solid #374151;
        margin-bottom: 1rem;
    }
    .status-badge-healthy {
        background-color: #065f46;
        color: #34d399;
        padding: 4px 12px;
        border-radius: 20px;
        font-weight: 600;
        font-size: 0.85rem;
    }
    .status-badge-degraded {
        background-color: #92400e;
        color: #fbbf24;
        padding: 4px 12px;
        border-radius: 20px;
        font-weight: 600;
        font-size: 0.85rem;
    }
    </style>
""", unsafe_allow_html=True)

# Sidebar settings
st.sidebar.title("⚙️ Configuration")
backend_url = st.sidebar.text_input("FastAPI Base URL", value="http://127.0.0.1:8000")
client = APIClient(base_url=backend_url)

st.sidebar.divider()
st.sidebar.markdown("**Phase 0 Foundation**")
st.sidebar.caption("Streamlit Frontend → FastAPI Backend → MongoDB")

# Main Header
st.markdown('<div class="main-header">AI Personal Branding & Content Intelligence Platform</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Phase 0 Architectural Foundation & Verification Control Panel</div>', unsafe_allow_html=True)

# Tabs
tab1, tab2, tab3 = st.tabs(["📊 System Health & Status", "⚡ Content Generation (Stub)", "📐 Target Architecture"])

with tab1:
    st.subheader("System & Database Health Monitor")
    st.caption("Verifies end-to-end communication from Streamlit → FastAPI → MongoDB.")
    
    if st.button("🔄 Refresh System Status", type="primary"):
        st.rerun()
        
    with st.spinner("Checking backend and MongoDB health..."):
        health_resp = client.check_health()
        
    col1, col2, col3 = st.columns(3)
    
    if health_resp["success"]:
        data = health_resp["data"].get("data", {})
        sys_status = data.get("status", "unknown")
        db_info = data.get("database", {})
        
        with col1:
            st.metric("FastAPI Gateway", f"HTTP {health_resp['http_status']} OK", "Connected")
        with col2:
            st.metric("Overall System Status", sys_status.upper(), f"Env: {data.get('environment', 'dev')}")
        with col3:
            db_status_str = "CONNECTED" if db_info.get("connected") else "DISCONNECTED"
            st.metric("MongoDB Database", db_status_str, db_info.get("database_name", "N/A"))
            
        if not db_info.get("connected"):
            st.warning(f"⚠️ **MongoDB Connection Degraded**: {db_info.get('error')}")
            st.info("Ensure MongoDB is running locally at `mongodb://localhost:27017` or configured via `.env`.")
        else:
            st.success("✅ **System fully operational**: FastAPI and MongoDB connected.")
            
        with st.expander("🔍 View Raw JSON Response"):
            st.json(health_resp["data"])
    else:
        with col1:
            st.metric("FastAPI Gateway", f"HTTP {health_resp['http_status']}", "Offline / Unreachable")
        with col2:
            st.metric("System Status", "UNHEALTHY", "Offline")
        with col3:
            st.metric("MongoDB", "UNKNOWN", "N/A")
            
        st.error(f"❌ **Connection Error**: {health_resp.get('error')}")
        st.info("Make sure the FastAPI backend is running via `uvicorn app.main:app --reload`.")

with tab2:
    st.subheader("Content Generation Workflow (Phase 0 Stub)")
    st.caption("Submits a test request to `POST /api/v1/content/generate` to verify schema validation and routing.")
    
    with st.form("content_stub_form"):
        topic = st.text_input("Content Topic", value="Model Context Protocol (MCP) Architecture", help="Enter topic or prompt")
        
        col_a, col_b = st.columns(2)
        with col_a:
            audience = st.selectbox("Target Audience", ["AI engineers", "Tech Founders", "Software Engineers", "General Tech"])
            tone = st.selectbox("Tone", ["technical", "educational", "conversational", "thought-provoking"])
        with col_b:
            campaign_id = st.text_input("Campaign ID (Optional)", value="cmp_12345")
            source_url = st.text_input("Source URL (Optional)", value="https://example.com/mcp-spec")
            
        platforms = st.multiselect(
            "Target Platforms",
            options=["linkedin", "twitter", "instagram", "blog", "newsletter"],
            default=["linkedin", "twitter"]
        )
        
        submitted = st.form_submit_button("🚀 Submit Stub Request", type="primary")
        
    if submitted:
        if not topic:
            st.warning("Please specify a topic.")
        elif not platforms:
            st.warning("Please select at least one target platform.")
        else:
            with st.spinner("Submitting stub request to FastAPI..."):
                gen_resp = client.trigger_content_generation_stub(
                    topic=topic,
                    platforms=platforms,
                    audience=audience,
                    tone=tone,
                    campaign_id=campaign_id if campaign_id else None,
                    source_url=source_url if source_url else None
                )
                
            if gen_resp["success"]:
                resp_data = gen_resp["data"].get("data", {})
                st.success(f"✅ **Request Acknowledged!** `run_id`: `{resp_data.get('run_id')}`")
                
                col_r1, col_r2 = st.columns(2)
                with col_r1:
                    st.json({
                        "run_id": resp_data.get("run_id"),
                        "status": resp_data.get("status"),
                        "message": resp_data.get("message")
                    })
                with col_r2:
                    st.json({
                        "requested_topic": resp_data.get("requested_topic"),
                        "platforms": resp_data.get("platforms")
                    })
            else:
                st.error(f"❌ Submission Failed: {gen_resp.get('error')}")

with tab3:
    st.subheader("Phase 0 Architecture & Modular Growth Path")
    st.markdown("""
    ### Target Architecture Layout
    ```
    Streamlit Frontend (port 8501)
            │  HTTP / JSON (httpx)
            ▼
    FastAPI Gateway (port 8000) [/api/v1]
            │
            ├─► Route → HealthService → MongoDB Database
            │
            └─► Future Modular Plugs:
                 ├── app/agents/      (LangGraph Supervisor, Research, Strategy, Content, Critic, Publisher)
                 ├── app/workflows/   (LangGraph State Graph Workflows)
                 ├── app/rag/         (ChromaDB + Hybrid BM25/Dense Retriever)
                 ├── app/mcp/         (Model Context Protocol Clients & Tools)
                 └── app/workers/     (Redis + Celery Background Task Workers)
    ```
    """)
