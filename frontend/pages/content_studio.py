import uuid
from typing import Optional, Dict, Any
import streamlit as st
from api_client import APIClient
from components.header import render_page_header
from components.post_preview import render_post_preview


def render_content_studio_page(client: APIClient) -> None:
    """
    Renders the Content Studio page:
    - Primary Tab: Topic-to-LinkedIn Automated Generation & Publishing (Live Demonstration)
    - Secondary Tab: Multi-Platform AI Content Generation (Draft Only / No Publish)
    """
    render_page_header(
        title="Content Studio",
        subtitle="End-to-end multi-agent research, RAG retrieval, strategy formulation, and automated social distribution.",
        badge="Live Demo Center",
    )

    tab_linkedin, tab_general = st.tabs(
        [
            "💼 Topic-to-LinkedIn Publisher (Live)",
            "⚡ Multi-Platform Draft Generator (No Publish)",
        ]
    )

    # =========================================================================
    # TAB 1: Topic-to-LinkedIn Direct Publishing (Main Presentation Feature)
    # =========================================================================
    with tab_linkedin:
        st.subheader("Automated Topic-to-LinkedIn Pipeline")
        st.caption(
            "Researches topic via Search MCP, retrieves internal knowledge from ChromaDB RAG, "
            "synthesizes strategy, writes optimized commentary, and posts directly to LinkedIn."
        )

        # Quick pre-flight check of LinkedIn connection
        with st.container():
            li_status = client.get_linkedin_status()
            if li_status.get("success"):
                li_data = li_status.get("data", {}).get("data", {})
                if not li_data.get("connected"):
                    st.warning(
                        "⚠️ **LinkedIn Not Connected**: Your account is currently not authorized. "
                        "Publishing will fail until authorized via OAuth 2.0."
                    )
                    auth_url_resp = client.get_linkedin_auth_url()
                    if auth_url_resp.get("success"):
                        auth_url = auth_url_resp.get("data", {}).get("data", {}).get("authorization_url")
                        if auth_url:
                            st.link_button("🔗 Connect LinkedIn Account Now", auth_url, type="primary")
                else:
                    acc = li_data.get("account") or {}
                    name = acc.get("name") or acc.get("member_id", "Authorized Member")
                    st.success(f"✅ Connected to LinkedIn Profile: **{name}** (`{acc.get('member_urn', 'urn:li:person')}`)")
            else:
                st.info("ℹ️ Unable to reach LinkedIn status endpoint. Ensure the FastAPI backend is running.")

        # Input Form
        with st.form("linkedin_publish_form"):
            topic = st.text_input(
                "Content Topic *",
                value="Model Context Protocol (MCP) in Production AI Agents",
                placeholder="e.g. Graph RAG Architecture vs Traditional Vector Search",
                help="The core subject to be researched, contextualized via RAG, and authored.",
            )

            col1, col2 = st.columns(2)
            with col1:
                tone = st.selectbox(
                    "Desired Tone",
                    options=["professional", "technical", "conversational", "thought-provoking", "educational"],
                    index=0,
                    help="Determines stylistic voice and vocabulary used by the Content Generator.",
                )
            with col2:
                audience = st.selectbox(
                    "Target Audience Demographic",
                    options=[
                        "software developers",
                        "AI engineers",
                        "Tech Founders",
                        "Engineering Leaders",
                        "General Tech Enthusiasts",
                    ],
                    index=0,
                    help="Directs Strategy Agent to tailor hooks, value propositions, and complexity.",
                )

            custom_run_id = st.text_input(
                "Custom Workflow Run ID (Optional)",
                value="",
                placeholder="e.g. run_demo_presentation",
                help="Optional custom identifier for tracing this run in logs and MongoDB.",
            )

            st.markdown(
                """
                <div class="alert-callout alert-callout-warning" style="margin-top: 1rem;">
                    <div>
                        <strong>⚠️ Live Publishing Notice:</strong> Submitting this request executes the 
                        multi-agent workflow and <strong>immediately publishes a public post</strong> 
                        to your personal LinkedIn profile feed via the official LinkedIn Posts API.
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            submitted = st.form_submit_button(
                "🚀 Generate & Publish to LinkedIn",
                type="primary",
                use_container_width=True,
            )

        # Handle form submission explicitly
        if submitted:
            cleaned_topic = topic.strip() if topic else ""
            if not cleaned_topic:
                st.error("❌ Validation Error: Please provide a valid topic before publishing.")
            else:
                run_id_val = custom_run_id.strip() if custom_run_id.strip() else None

                progress_placeholder = st.empty()
                with progress_placeholder.container():
                    st.info(
                        "🔄 **Executing Multi-Agent Workflow**:\n\n"
                        "1. **Pre-flight**: Verifying LinkedIn OAuth 2.0 authorization...\n"
                        "2. **Research Agent**: Querying Search MCP (ArXiv, Google News, GitHub Trends)...\n"
                        "3. **RAG Agent**: Retrieving vector embeddings from ChromaDB...\n"
                        "4. **Strategy Agent**: Synthesizing angle, audience hooks, and structural outline...\n"
                        "5. **Content Generator**: Generating LinkedIn commentary with Groq / OpenAI LLM...\n"
                        "6. **Publisher**: Dispatching to LinkedIn REST Posts API & saving to MongoDB...\n\n"
                        "_This end-to-end cycle typically takes 20-50 seconds. Please wait..._"
                    )

                with st.spinner("Autonomous agents working..."):
                    result = client.publish_from_topic(
                        topic=cleaned_topic,
                        tone=tone,
                        audience=audience,
                        run_id=run_id_val,
                        timeout=120.0,
                    )

                progress_placeholder.empty()

                # Store response in session state so reruns preserve the display safely
                st.session_state["latest_linkedin_publish_result"] = result
                st.session_state["latest_linkedin_request"] = {
                    "topic": cleaned_topic,
                    "tone": tone,
                    "audience": audience,
                    "run_id": run_id_val,
                }

        # Display latest publication result if present in session state
        saved_result = st.session_state.get("latest_linkedin_publish_result")
        if saved_result:
            st.markdown("---")
            if saved_result.get("success"):
                st.balloons()
                st.success("🎉 **Success! Your post has been published live to LinkedIn.**")

                render_post_preview(saved_result, title="Verified Live LinkedIn Post")

                col_cl1, col_cl2 = st.columns([4, 1])
                with col_cl2:
                    if st.button("🗑️ Clear Result Display", use_container_width=True):
                        st.session_state.pop("latest_linkedin_publish_result", None)
                        st.session_state.pop("latest_linkedin_request", None)
                        st.rerun()
            else:
                status_code = saved_result.get("http_status", 500)
                raw_err = saved_result.get("error")
                data_payload = saved_result.get("data", {})
                detail_msg = ""
                if isinstance(data_payload, dict):
                    detail_msg = data_payload.get("detail") or data_payload.get("message") or ""

                error_display = detail_msg or raw_err or "Unknown error occurred."

                st.error(f"❌ **Publication Failed (HTTP {status_code})**: {error_display}")

                # Granular troubleshooting guidance based on actual HTTP status
                if status_code == 400 and "authorize" in str(error_display).lower():
                    st.info("💡 **Resolution**: Your LinkedIn account is not connected. Use the authorization button above to link your account.")
                elif status_code == 401:
                    st.info("💡 **Resolution**: Your LinkedIn access token has expired. Please re-authenticate via `/api/v1/linkedin/auth-url`.")
                elif status_code == 403:
                    st.info("💡 **Resolution**: LinkedIn rejected publication due to missing permissions. Ensure `w_member_social` scope was granted during OAuth login.")
                elif status_code == 503:
                    st.info("💡 **Resolution**: Unable to communicate with FastAPI backend. Ensure `uvicorn app.main:app` is running.")
                elif status_code == 504:
                    st.warning("⚠️ **Resolution**: Request timed out. The backend or LinkedIn API may still be processing. Check your LinkedIn profile before attempting another submission.")

                with st.expander("🔍 View Raw Error Payload"):
                    st.json(saved_result)

    # =========================================================================
    # TAB 2: Multi-Platform AI Content Generation (Draft Only)
    # =========================================================================
    with tab_general:
        st.subheader("Multi-Platform Agentic Draft Generator")
        st.caption(
            "Invokes `POST /api/v1/content/generate` to produce research, strategy, "
            "and draft content across multiple platforms without publishing."
        )

        with st.form("draft_content_form"):
            draft_topic = st.text_input(
                "Topic",
                value="Building Reliable LLM Pipelines with Evaluation Frameworks",
                placeholder="Enter topic...",
            )

            c1, c2 = st.columns(2)
            with c1:
                draft_audience = st.selectbox(
                    "Target Audience",
                    ["AI engineers", "Tech Founders", "Software Engineers", "General Tech"],
                    key="draft_aud",
                )
                draft_tone = st.selectbox(
                    "Tone",
                    ["technical", "educational", "conversational", "thought-provoking"],
                    key="draft_tone",
                )
            with c2:
                draft_campaign_id = st.text_input("Campaign ID (Optional)", value="")
                draft_source_url = st.text_input("Source URL (Optional)", value="")

            draft_platforms = st.multiselect(
                "Platforms to Author",
                options=["linkedin", "twitter", "instagram", "blog", "newsletter"],
                default=["linkedin", "twitter"],
            )

            draft_submitted = st.form_submit_button(
                "⚡ Generate Multi-Platform Drafts",
                type="primary",
            )

        if draft_submitted:
            if not draft_topic.strip():
                st.warning("Please specify a topic.")
            elif not draft_platforms:
                st.warning("Please select at least one platform.")
            else:
                with st.spinner("Generating multi-platform content via LangGraph..."):
                    gen_resp = client.generate_content(
                        topic=draft_topic.strip(),
                        platforms=draft_platforms,
                        audience=draft_audience,
                        tone=draft_tone,
                        campaign_id=draft_campaign_id.strip() if draft_campaign_id.strip() else None,
                        source_url=draft_source_url.strip() if draft_source_url.strip() else None,
                        timeout=90.0,
                    )

                st.session_state["latest_draft_gen_result"] = gen_resp

        saved_draft = st.session_state.get("latest_draft_gen_result")
        if saved_draft:
            st.markdown("---")
            if saved_draft.get("success"):
                d_data = saved_draft.get("data", {}).get("data", {})
                st.success(f"✅ **Generated Successfully!** Run ID: `{d_data.get('run_id')}`")

                res_tab1, res_tab2, res_tab3 = st.tabs(
                    ["📝 Generated Content", "🔍 Research Output", "🎯 Strategy Framing"]
                )

                with res_tab1:
                    gen_content = d_data.get("generated_content", {})
                    if isinstance(gen_content, dict):
                        for plat, content_val in gen_content.items():
                            st.markdown(f"#### Platform: `{plat.upper()}`")
                            if isinstance(content_val, dict):
                                st.markdown(f"**Title**: {content_val.get('title', '')}")
                                st.write(content_val.get("content", ""))
                                if content_val.get("call_to_action"):
                                    st.caption(f"CTA: {content_val.get('call_to_action')}")
                                if content_val.get("hashtags"):
                                    st.caption(f"Tags: {' '.join(content_val.get('hashtags', []))}")
                            else:
                                st.write(str(content_val))
                    else:
                        st.write(str(gen_content))

                with res_tab2:
                    st.json(d_data.get("research", {}))
                    if d_data.get("research_sources"):
                        st.markdown("**External Sources:**")
                        st.json(d_data.get("research_sources"))

                with res_tab3:
                    st.json(d_data.get("strategy", {}))
            else:
                st.error(f"❌ Draft Generation Failed: {saved_draft.get('error')}")
                with st.expander("View Error Details"):
                    st.json(saved_draft)
