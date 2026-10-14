import streamlit as st
from api_client import APIClient
from components.header import render_page_header


def render_knowledge_base_page(client: APIClient) -> None:
    """
    Renders the RAG Knowledge Base interface:
    - Semantic vector similarity search against ChromaDB
    - Display of retrieved chunks with metadata, sources, and distance scores
    - Overview of the PDF Ingestion API pipeline
    """
    render_page_header(
        title="Knowledge Base (RAG)",
        subtitle="Semantic vector retrieval and internal document intelligence powered by ChromaDB & SentenceTransformers.",
        badge="Phase 1B-2 Operational",
    )

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
                st.info("No matching chunks found in ChromaDB. Ensure documents have been ingested via `/api/v1/knowledge/ingest`.")
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
            st.error(f"❌ Knowledge Base Search Failed: {saved_search.get('error', 'Unknown error.')}")

    st.markdown("---")

    # Ingestion Pipeline Reference
    st.subheader("📥 Document Ingestion Subsystem")
    st.markdown(
        """
        The RAG subsystem indexes documents via the FastAPI backend:
        
        - **Endpoint**: `POST /api/v1/knowledge/ingest` (Accepts multipart PDF files)
        - **Processing**: `pypdf` page extraction → overlapping chunker (1000 char size, 200 char overlap)
        - **Embedding Model**: `sentence-transformers/all-MiniLM-L6-v2` (384-dimensional dense vectors)
        - **Storage**: Persistent local ChromaDB collection (`./.chroma`)
        
        *To ingest new PDF documents into the platform knowledge base, use the ingestion API or Swagger UI.*
        """
    )
