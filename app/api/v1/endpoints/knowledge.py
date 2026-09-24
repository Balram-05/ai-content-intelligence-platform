from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from app.models.common import StandardAPIResponse
from app.models.rag import KnowledgeIngestionResponse
from app.rag.ingestion import RAGIngestionService, RAGIngestionError
from app.api.dependencies import get_rag_ingestion_service
from app.core.logging import logger

router = APIRouter()


@router.post(
    "/knowledge/ingest",
    response_model=StandardAPIResponse[KnowledgeIngestionResponse],
    status_code=status.HTTP_200_OK,
    summary="Ingest PDF document into RAG Knowledge Base",
    description="Uploads a PDF document, extracts text page-by-page, chunks the content, generates Sentence Transformer embeddings, and persists vector data in ChromaDB."
)
async def ingest_knowledge_document(
    file: UploadFile = File(...),
    ingestion_service: RAGIngestionService = Depends(get_rag_ingestion_service)
) -> StandardAPIResponse[KnowledgeIngestionResponse]:
    """
    Endpoint for uploading and ingesting PDF documents into ChromaDB vector store.
    """
    filename = file.filename or "uploaded_document.pdf"
    logger.info(f"[API Knowledge] Received file upload: '{filename}'")

    # Validate file extension
    if not filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file format for '{filename}'. Only PDF documents (.pdf) are supported."
        )

    try:
        content_bytes = await file.read()
        if not content_bytes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Uploaded file '{filename}' is empty."
            )

        result = ingestion_service.ingest_pdf_bytes(content_bytes, source_name=filename)

        response_payload = KnowledgeIngestionResponse(
            document_id=result.document_id,
            source=result.source,
            total_pages=result.total_pages,
            total_chunks=result.total_chunks,
            collection_name=result.collection_name,
            status=result.status,
            message=result.message,
            metadata=result.metadata
        )

        return StandardAPIResponse(
            status="success",
            message=f"PDF document '{filename}' successfully ingested and indexed.",
            data=response_payload
        )

    except HTTPException:
        raise
    except RAGIngestionError as e:
        logger.error(f"[API Knowledge] Ingestion pipeline failed for '{filename}': {e}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"[API Knowledge] Unexpected error during ingestion of '{filename}': {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected internal server error during document ingestion: {e}"
        )
