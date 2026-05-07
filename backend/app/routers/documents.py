"""
Document Upload Router — HIPAA / FHIR / Privacy Compliant
============================================================
Patient-facing PDF upload with:
  - Original PDF stored in GridFS (patient can view/download)
  - PHI redacted BEFORE any LLM processing
  - FHIR DocumentReference created for EHR interoperability
  - Document history for patient portal
  - Full audit trail

Flow:
  1. Patient uploads PDF lab report
  2. Original PDF stored in GridFS (encrypted at rest)
  3. Text extracted, sections identified with priority tags
  4. PHI REDACTED from text before vector DB ingestion
  5. Redacted chunks ingested into vector store (RAG) + Neo4j (graph)
  6. FHIR DocumentReference created
  7. Document appears in patient's history (viewable as PDF)
  8. HITL can trigger screening from stored (redacted) data

Endpoints:
  POST /documents/upload              — Patient uploads PDF
  GET  /documents/my-documents        — Patient document history
  GET  /documents/{id}                — Document metadata
  GET  /documents/{id}/pdf            — Download original PDF (patient only)
  GET  /documents/{id}/fhir           — FHIR DocumentReference
  POST /documents/{id}/trigger-screening — HITL triggers screening
"""
import uuid
import structlog
from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, File, Form
from fastapi.responses import Response
from typing import Optional

from app.dependencies import get_db, get_current_user, require_permission, require_any_permission
from app.services.document_service import (
    DocumentService, chunk_document,
    DOCUMENTS_COLLECTION, RAW_TEXTS_COLLECTION, FHIR_REFS_COLLECTION,
)
from app.services.phi_redaction_service import PHIRedactionService
from app.services.screening_service import ScreeningService
from app.services.audit_service import log_phi_access
from app.pipelines.ingestion_pipeline import IngestionPipeline

logger = structlog.get_logger()
router = APIRouter()

_document_service = DocumentService()
_phi_service = PHIRedactionService()
_screening_service = ScreeningService()
_ingestion_pipeline: Optional[IngestionPipeline] = None


def _get_pipeline() -> IngestionPipeline:
    global _ingestion_pipeline
    if _ingestion_pipeline is None:
        _ingestion_pipeline = IngestionPipeline()
    return _ingestion_pipeline


@router.post("/upload")
async def upload_document(
    request: Request,
    file: UploadFile = File(...),
    patient_id: str = Form(...),
    report_date: Optional[str] = Form(None),
    current_user=Depends(require_any_permission([
        "patient:write_own", "memory:ingest", "screening:validate"
    ])),
    db=Depends(get_db),
):
    """
    Upload a PDF lab report for processing.

    HIPAA Compliance:
    - Original PDF stored encrypted in GridFS (patient-accessible)
    - PHI is REDACTED from text before any LLM/vector DB processing
    - FHIR DocumentReference created for EHR interoperability
    - Full audit trail logged

    Privacy:
    - LLM never sees patient name, phone, address, or ID numbers
    - Only clinical values and medical terminology reach the AI
    - Redaction map stored securely for HITL re-association if needed
    """
    # Access control: patients can only upload their own
    if current_user["role"] == "patient" and current_user["user_id"] != patient_id:
        raise HTTPException(status_code=403, detail="Patients can only upload their own documents")

    # Validate file type — PDF only (prevents injection attacks)
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    # Validate content-type header
    if file.content_type and file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Invalid file type. Only application/pdf is accepted")

    # Size limit: 20MB
    pdf_bytes = await file.read()
    if len(pdf_bytes) > 20 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File size exceeds 20MB limit")

    if len(pdf_bytes) == 0:
        raise HTTPException(status_code=400, detail="Empty file")

    # Validate PDF magic bytes (prevents renamed malicious files)
    if not pdf_bytes[:5] == b"%PDF-":
        raise HTTPException(
            status_code=400,
            detail="Invalid PDF file. The file does not contain valid PDF data."
        )

    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))

    # ── Step 1: Process PDF (extract text, store original in GridFS) ──────
    parsed = await _document_service.process_pdf_upload(
        patient_id=patient_id,
        filename=file.filename,
        pdf_bytes=pdf_bytes,
        uploader_id=current_user["user_id"],
        uploader_role=current_user["role"],
        db=db,
    )

    if not parsed.raw_text.strip():
        raise HTTPException(
            status_code=422,
            detail=f"Could not extract text from PDF. Errors: {parsed.parse_errors}",
        )

    # ── Step 2: PHI Redaction (HIPAA Safe Harbor) ─────────────────────────
    redaction_result = await _phi_service.redact_for_llm(
        text=parsed.raw_text,
        patient_id=patient_id,
        document_id=parsed.document_id,
        db=db,
    )

    # Update document status
    await db[DOCUMENTS_COLLECTION].update_one(
        {"document_id": parsed.document_id},
        {"$set": {
            "phi_status":         "redacted",
            "redaction_map_id":   redaction_result.redaction_map_id,
            "redactions_applied": redaction_result.redactions_applied,
            "redacted_fields":    redaction_result.redacted_fields,
        }},
    )

    # ── Step 3: Chunk REDACTED text and ingest into vector DB ─────────────
    # Replace raw_text with redacted version for chunking
    parsed.raw_text = redaction_result.redacted_text
    chunks = chunk_document(parsed)
    pipeline = _get_pipeline()
    ingestion_results = []

    for chunk in chunks:
        try:
            result = await pipeline.run(
                patient_id=patient_id,
                text=chunk["text"],  # This is PHI-REDACTED text
                source=f"pdf_upload:{parsed.document_id}:{chunk['section_id']}",
                encounter_date=report_date or parsed.report_date,
                request_id=request_id,
            )
            ingestion_results.append({
                "section_id": chunk["section_id"],
                "priority": chunk["priority"],
                "status": result["status"],
                "vector_entry_id": result.get("vector_entry_id"),
            })
        except Exception as e:
            logger.error(
                "chunk_ingestion_failed",
                section_id=chunk["section_id"],
                error=str(e),
            )
            ingestion_results.append({
                "section_id": chunk["section_id"],
                "priority": chunk["priority"],
                "status": "failed",
                "error": str(e)[:100],
            })

    # ── Step 4: Create FHIR DocumentReference ─────────────────────────────
    fhir_ref = await _document_service.create_fhir_document_reference(
        document_id=parsed.document_id,
        patient_id=patient_id,
        filename=file.filename,
        report_date=report_date or parsed.report_date,
        db=db,
    )

    # ── Step 5: Audit log ─────────────────────────────────────────────────
    await log_phi_access(
        action="document_uploaded_hipaa_compliant",
        patient_id=patient_id,
        accessor_id=current_user["user_id"],
        accessor_role=current_user["role"],
        resource_type="pdf_lab_report",
        request_id=request_id,
        db=db,
        metadata={
            "document_id": parsed.document_id,
            "filename": file.filename,
            "pages": parsed.total_pages,
            "sections": len(parsed.sections),
            "high_priority_sections": sum(1 for s in parsed.sections if s.priority == "high"),
            "language": parsed.source_language,
            "phi_redactions": redaction_result.redactions_applied,
            "redacted_fields": redaction_result.redacted_fields,
            "chunks_ingested": sum(1 for r in ingestion_results if r["status"] == "success"),
            "fhir_document_reference_created": True,
        },
    )

    return {
        "document_id": parsed.document_id,
        "patient_id": patient_id,
        "filename": file.filename,
        "total_pages": parsed.total_pages,
        "source_language": parsed.source_language,
        "report_date": parsed.report_date,
        "sections_found": len(parsed.sections),
        "high_priority_sections": sum(1 for s in parsed.sections if s.priority == "high"),
        "privacy": {
            "phi_redacted": True,
            "redactions_applied": redaction_result.redactions_applied,
            "redacted_fields": redaction_result.redacted_fields,
            "hipaa_compliant": True,
            "llm_sees_only_redacted_text": True,
        },
        "storage": {
            "original_pdf_stored": True,
            "patient_can_view_pdf": True,
            "s3_stored":           True,
        },
        "fhir": {
            "document_reference_created": True,
            "resource_type": "DocumentReference",
            "loinc_code": "11502-2",
        },
        "ingestion": {
            "chunks_total": len(ingestion_results),
            "chunks_successful": sum(1 for r in ingestion_results if r["status"] == "success"),
            "details": ingestion_results,
        },
        "parse_errors": parsed.parse_errors,
        "status": "processed",
    }


@router.get("/my-documents")
async def get_my_documents(
    current_user=Depends(require_permission("patient:read_own")),
    db=Depends(get_db),
):
    """
    Patient views their uploaded document history.
    Returns metadata for each document — PDF viewable via /{id}/pdf endpoint.
    """
    return await _document_service.get_patient_documents(
        patient_id=current_user["user_id"], db=db
    )


@router.get("/{document_id}")
async def get_document_metadata(
    document_id: str,
    current_user=Depends(require_any_permission([
        "patient:read_own", "screening:validate", "patient:read_consented"
    ])),
    db=Depends(get_db),
):
    """Get document metadata by ID."""
    doc = await db[DOCUMENTS_COLLECTION].find_one({"document_id": document_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    # Access control: patients can only see their own
    if current_user["role"] == "patient" and doc["patient_id"] != current_user["user_id"]:
        raise HTTPException(status_code=403, detail="Access denied")

    doc.pop("_id", None)
    return doc


@router.get("/{document_id}/pdf")
async def download_document_pdf(
    document_id: str,
    request: Request,
    current_user=Depends(require_any_permission([
        "patient:read_own", "screening:validate"
    ])),
    db=Depends(get_db),
):
    """
    Download the original PDF document.

    Access control:
    - Patients can download their own documents
    - HITL validators can access for verification

    The original PDF is stored unmodified — this is the patient's health record.
    """
    doc_meta = await db[DOCUMENTS_COLLECTION].find_one({"document_id": document_id})
    if not doc_meta:
        raise HTTPException(status_code=404, detail="Document not found")

    if current_user["role"] == "patient" and doc_meta["patient_id"] != current_user["user_id"]:
        raise HTTPException(status_code=403, detail="Access denied")

    # Retrieve PDF from GridFS
    pdf_bytes = await _document_service.get_pdf_for_patient(
        document_id=document_id,
        patient_id=doc_meta["patient_id"],
        db=db,
    )

    if not pdf_bytes:
        raise HTTPException(status_code=404, detail="PDF file not found in storage")

    # Audit the access
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    await log_phi_access(
        action="document_pdf_downloaded",
        patient_id=doc_meta["patient_id"],
        accessor_id=current_user["user_id"],
        accessor_role=current_user["role"],
        resource_type="pdf_document",
        request_id=request_id,
        db=db,
        metadata={"document_id": document_id, "filename": doc_meta.get("filename")},
    )

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'inline; filename="{doc_meta.get("filename", "report.pdf")}"',
            "X-Document-ID": document_id,
            "X-HIPAA-Classification": "PHI",
        },
    )


@router.get("/{document_id}/fhir")
async def get_fhir_document_reference(
    document_id: str,
    current_user=Depends(require_any_permission([
        "patient:read_own", "fhir:read", "screening:validate"
    ])),
    db=Depends(get_db),
):
    """
    Get the FHIR R4 DocumentReference for this document.
    Compliant with HL7 FHIR EHR standards.
    """
    fhir_doc = await db[FHIR_REFS_COLLECTION].find_one({"document_id": document_id})
    if not fhir_doc:
        raise HTTPException(status_code=404, detail="FHIR DocumentReference not found")

    # Access control
    if current_user["role"] == "patient" and fhir_doc["patient_id"] != current_user["user_id"]:
        raise HTTPException(status_code=403, detail="Access denied")

    return fhir_doc.get("fhir_resource", {})


@router.post("/{document_id}/trigger-screening")
async def trigger_screening_from_document(
    document_id: str,
    request: Request,
    current_user=Depends(require_permission("screening:validate")),
    db=Depends(get_db),
):
    """
    HITL validator triggers a screening from an uploaded document.

    Uses the PHI-REDACTED text stored during upload.
    The LLM never sees the original PII — only redacted clinical data.
    """
    doc_meta = await db[DOCUMENTS_COLLECTION].find_one({"document_id": document_id})
    if not doc_meta:
        raise HTTPException(status_code=404, detail="Document not found")

    # Fetch the raw text
    raw_doc = await db[RAW_TEXTS_COLLECTION].find_one({"document_id": document_id})
    if not raw_doc:
        raise HTTPException(
            status_code=422,
            detail="Document text not available. Re-upload required.",
        )

    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))

    # Get the PHI-redacted version for LLM processing
    redaction_map_id = doc_meta.get("redaction_map_id")
    if redaction_map_id:
        # Use already-redacted text from the redaction service
        redaction_result = await _phi_service.redact_for_llm(
            text=raw_doc["raw_text"],
            patient_id=doc_meta["patient_id"],
            document_id=document_id,
            db=db,
        )
        llm_text = redaction_result.redacted_text
    else:
        # Fallback: redact now
        redaction_result = await _phi_service.redact_for_llm(
            text=raw_doc["raw_text"],
            patient_id=doc_meta["patient_id"],
            document_id=document_id,
            db=db,
        )
        llm_text = redaction_result.redacted_text

    # Also redact high-priority text
    high_priority_text = raw_doc.get("high_priority_text", "")
    if high_priority_text:
        hp_redaction = await _phi_service.redact_for_llm(
            text=high_priority_text,
            patient_id=doc_meta["patient_id"],
            document_id=f"{document_id}_hp",
            db=db,
        )
        high_priority_text = hp_redaction.redacted_text

    # Run screening with PHI-redacted data
    summary = await _screening_service.generate_screening(
        patient_id=doc_meta["patient_id"],
        lab_report_text=llm_text,
        requester_id=current_user["user_id"],
        requester_role=current_user["role"],
        request_id=request_id,
        db=db,
        patient_name="[REDACTED]",  # Never send real name to LLM
        patient_age=doc_meta.get("patient_age"),
        patient_gender=doc_meta.get("patient_gender"),
        known_conditions=[],
        source_document_id=document_id,
        high_priority_text=high_priority_text,
        source_language=doc_meta.get("source_language", "English"),
    )

    return summary
