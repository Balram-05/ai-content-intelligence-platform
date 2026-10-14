import streamlit as st
from api_client import APIClient
from components.header import render_page_header


def render_settings_page(client: APIClient) -> None:
    """
    Renders the Configuration & Settings page:
    - FastAPI Gateway Base URL management
    - Real-time connection diagnostic test
    - LinkedIn OAuth integration parameters (sanitized, non-sensitive)
    - Future configuration roadmap
    """
    render_page_header(
        title="Settings & Configuration",
        subtitle="Manage platform gateway endpoints, inspect integration configurations, and view operational parameters.",
        badge="System Config",
    )

    st.subheader("🌐 Gateway Connection")
    st.caption("Configure the HTTP endpoint used by this Streamlit application to communicate with FastAPI.")

    current_base_url = st.session_state.get("fastapi_base_url", client.base_url)

    with st.form("settings_gateway_form"):
        new_base_url = st.text_input(
            "FastAPI Gateway URL",
            value=current_base_url,
            help="Base URL of the running FastAPI server (e.g. http://127.0.0.1:8000).",
        )
        saved = st.form_submit_button("💾 Save Gateway Configuration", type="primary")

    if saved:
        cleaned_url = new_base_url.strip().rstrip("/")
        st.session_state["fastapi_base_url"] = cleaned_url
        client.base_url = cleaned_url
        st.success(f"Updated Gateway URL to: `{cleaned_url}`")
        st.rerun()

    st.markdown("#### Gateway Connectivity Diagnostic:")
    if st.button("🧪 Test Gateway Connection"):
        with st.spinner("Testing health endpoint..."):
            diag_resp = client.check_health()
        if diag_resp.get("success"):
            st.success(f"✅ Gateway reachable at `{client.base_url}`! HTTP {diag_resp.get('http_status')}")
            st.json(diag_resp.get("data", {}))
        else:
            st.error(f"❌ Connection failed: {diag_resp.get('error', 'Unreachable')}")

    st.markdown("---")

    st.subheader("💼 LinkedIn OAuth Configuration Parameters")
    st.caption("Parameters registered for personal profile authorization (secrets are safely managed in backend .env).")

    st.markdown(
        """
        - **OAuth Callback Endpoint**: `http://127.0.0.1:8000/api/v1/linkedin/callback`
        - **Requested Scopes**: `openid profile w_member_social`
        - **REST API Protocol**: LinkedIn Posts API (`/rest/posts`, version `202502`)
        - **CSRF Defense**: Cryptographic state tokens stored server-side with 600s TTL
        """
    )

    st.markdown("---")

    st.subheader("🔮 Planned Configuration Capabilities")
    st.markdown(
        """
        - **LLM Provider Switching**: Seamlessly toggle between Groq (Llama 3.3 70B) and OpenAI (GPT-4o) from the UI.
        - **Custom MCP Tool Servers**: Dynamically register external Search or Social MCP endpoints.
        - **Tone & Persona Presets**: Store custom organizational brand guidelines and prompt templates.
        """
    )
