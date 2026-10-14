import streamlit as st
from api_client import APIClient
from components.header import render_page_header


def render_knowledge_base_page(client: APIClient) -> None:
    """
    Renders the RAG Knowledge Base interface:
    - PDF document upload & ingestion into ChromaDB
    - Semantic vector similarity search against ChromaDB
    - Display of retrieved chunks with metadata, sources, and distance scores
    - Overview of the PDF Ingestion API pipeline
    """
    render_page_header(
        title="Knowledge Base (RAG)",
        subtitle="Semantic vector retrieval and internal document intelligence powered by ChromaDB & SentenceTransformers.",
        badge="Phase 1B Operational",
    )

    # =========================================================================
    # Section 1: Upload Knowledge Document
    # =========================================================================
    st.subheader("📤 Upload Knowledge Document")
    st.caption(
        "Upload reference PDF documents to expand the platform's vector knowledge base. "
        "Once ingested, documents become immediately available to the RAG retrieval "
        "pipeline and downstream content-generation workflows."
    )

    with st.container(border=True):
        uploaded_file = st.file_uploader(
            "Select a PDF document to ingest",
            type=["pdf"],
            help="Choose a PDF file (.pdf) to extract, chunk, and embed into ChromaDB.",
            key="knowledge_pdf_uploader",
        )

        col_act1, col_act2 = st.columns([1, 4])
        with col_act1:
            ingest_btn = st.button(
                "⚡ Ingest Document",
                type="primary",
                key="btn_ingest_pdf",
                disabled=(uploaded_file is None),
            )
        with col_act2:
            if st.session_state.get("latest_rag_ingest_result"):
                if st.button("🗑️ Clear Status", key="btn_clear_ingest_status"):
                    st.session_state.pop("latest_rag_ingest_result", None)
                    st.rerun()

        if ingest_btn:
            if uploaded_file is None:
                st.warning("Please select a PDF file before attempting ingestion.")
            elif uploaded_file.size == 0:
                st.error("❌ The selected file is empty (0 bytes). Please upload a valid PDF document.")
            else:
                file_bytes = uploaded_file.getvalue()
                if not file_bytes or len(file_bytes) == 0:
                    st.error("❌ The selected file contains no readable data.")
                else:
                    with st.spinner(f"Extracting pages, chunking, and generating embeddings for '{uploaded_file.name}'..."):
                        ingest_result = client.ingest_document(
                            filename=uploaded_file.name,
                            file_bytes=file_bytes,
                        )
                    st.session_state["latest_rag_ingest_result"] = ingest_result

        # Display ingestion result from session state
        saved_ingest = st.session_state.get("latest_rag_ingest_result")
        if saved_ingest:
            if saved_ingest.get("success"):
                data_envelope = saved_ingest.get("data", {})
                ingest_data = data_envelope.get("data", {}) if isinstance(data_envelope, dict) else {}

                source = ingest_data.get("source") or (uploaded_file.name if uploaded_file else "Document")
                doc_id = ingest_data.get("document_id", "N/A")
                pages = ingest_data.get("total_pages", "N/A")
                chunks = ingest_data.get("total_chunks", 0)
                coll = ingest_data.get("collection_name", "knowledge_base")
                meta = ingest_data.get("metadata", {}) or {}

                st.success(f"✅ Document **{source}** successfully ingested and indexed into ChromaDB!")

                mc1, mc2, mc3, mc4 = st.columns(4)
                with mc1:
                    st.metric("Total Pages", pages)
                with mc2:
                    st.metric("Chunks Indexed", chunks)
                with mc3:
                    st.metric("Vector Collection", coll)
                with mc4:
                    st.metric("Status", ingest_data.get("status", "success").capitalize())

                with st.expander("📋 View Ingestion Metadata", expanded=False):
                    st.markdown(f"**Document ID:** `{doc_id}`")
                    st.markdown(f"**Embedding Model:** `{meta.get('embedding_model', 'sentence-transformers/all-MiniLM-L6-v2')}`")
                    st.markdown(f"**Non-Empty Pages:** {meta.get('non_empty_pages', pages)}")
                    st.markdown(f"**Status Message:** {ingest_data.get('message', 'Ready for semantic retrieval')}")
            else:
                err_code = saved_ingest.get("http_status", 500)
                err_text = (
                    saved_ingest.get("error")
                    or saved_ingest.get("data", {}).get("detail")
                    or saved_ingest.get("data", {}).get("message")
                    or "Unknown error occurred during ingestion."
                )
                st.error(f"❌ Ingestion Failed (HTTP {err_code}): {err_text}")

    st.markdown("---")

    # =========================================================================
    # Section 2: Semantic Vector Retrieval
    # =========================================================================
    st.subheader("🔍 Semantic Vector Retrieval")
    st.caption("Search across ingested engineering whitepapers, architecture docs, and technical knowledge chunks.")

    with st.form("knowledge_search_form"):
        query = st.text_input(
            "Natural Language Query",
            value="How does LangGraph use a supervisor node to route agents?",
            placeholder="e.g. Model Context Protocol tool calling architecture",
            help="Enter a semantic search query to compare against vector embeddings.",
        )

        col1, col2 = st.columns([1, 3])
        with col1:
            top_k = st.slider("Top K Chunks", min_value=1, max_value=10, value=4)

        search_submitted = st.form_submit_button("🔍 Search Knowledge Base", type="primary")

    if search_submitted:
        cleaned_query = query.strip()
        if not cleaned_query:
            st.warning("Please enter a search query.")
        else:
            with st.spinner("Embedding query with SentenceTransformers & searching ChromaDB..."):
                search_res = client.search_knowledge_base(query=cleaned_query, top_k=top_k)

            st.session_state["latest_rag_search_result"] = search_res

    # Display results from session state
    saved_search = st.session_state.get("latest_rag_search_result")
    if saved_search:
        if saved_search.get("success"):
            data_payload = saved_search.get("data", {}).get("data", {})
            total = data_payload.get("total_results", 0)
            results = data_payload.get("results", [])

            st.markdown(f"**Found {total} relevant chunk(s)** for query: *'{data_payload.get('query', '')}'*")

            if not results:
                st.info("No matching chunks found in ChromaDB. Ensure documents have been ingested via the upload tool above or `/api/v1/knowledge/ingest`.")
            else:
                for idx, chunk in enumerate(results, start=1):
                    meta = chunk.get("metadata", {})
                    distance = chunk.get("distance", 0.0)
                    doc_id = meta.get("document_id", "N/A")
                    source = meta.get("source", "Unknown Document")
                    page = meta.get("page_number", "N/A")
                    chunk_idx = meta.get("chunk_index", "N/A")

                    with st.expander(f"📄 Result #{idx}: {source} (Page {page}, Distance: {distance:.4f})", expanded=(idx == 1)):
                        st.markdown(f"**Source Document:** `{source}` | **Page:** `{page}` | **Chunk:** `{chunk_idx}` | **Doc ID:** `{doc_id}`")
                        st.markdown(f"**Vector Distance:** `{distance:.4f}` *(Lower distance indicates higher semantic proximity)*")
                        st.markdown("**Chunk Content:**")
                        st.info(chunk.get("text", ""))
        else:
            err_msg = (
                saved_search.get("error")
                or saved_search.get("data", {}).get("detail")
                or saved_search.get("data", {}).get("message")
                or "Unknown error."
            )
            st.error(f"❌ Knowledge Base Search Failed: {err_msg}")

    st.markdown("---")

    # =========================================================================
    # Section 3: Ingestion Pipeline Reference
    # =========================================================================
    st.subheader("📥 Document Ingestion Subsystem")
    st.markdown(
        """
        The RAG subsystem indexes documents via the FastAPI backend:
        
        - **Upload Section**: Native frontend uploader submitting multipart PDF payloads directly to the backend.
        - **Endpoint**: `POST /api/v1/knowledge/ingest` (Accepts multipart PDF files)
        - **Processing**: `pypdf` page extraction → overlapping chunker (1000 char size, 200 char overlap)
        - **Embedding Model**: `sentence-transformers/all-MiniLM-L6-v2` (384-dimensional dense vectors)
        - **Storage**: Persistent local ChromaDB collection (`./.chroma`, collection `knowledge_base`)
        - **RAG Integration**: Chunks are retrieved dynamically during content generation by the LangGraph supervisor workflow.
        """
    )

