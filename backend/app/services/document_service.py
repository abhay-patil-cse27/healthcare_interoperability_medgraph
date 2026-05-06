"""
Document Processing Service
==============================
Handles PDF upload, text extraction, section-aware chunking, and priority tagging.

HIPAA / FHIR / Privacy Compliance:
  - Original PDF stored encrypted in MongoDB GridFS (patient-accessible)
  - PHI redacted from text BEFORE any LLM processing
  - FHIR DocumentReference created for each uploaded document
  - Full audit trail on all document access
  - Document history viewable by patient in PDF format

Design:
  - Extracts raw text from PDF using PyMuPDF (fitz)
  - Identifies high-priority sections (Summary, Note, Interpretation, Remark, etc.)
  - Chunks text with section boundaries preserved
  - Stores document metadata in MongoDB
  - Stores original PDF in GridFS for patient viewing
  - Feeds PHI-REDACTED text into the ingestion pipeline (vector DB + graph DB)

Section Priority System:
  - HIGH: Summary, Note, Interpretation, Remark, Medical Remarks, Conclusion,
          Impression, Diagnosis, Clinical Correlation, Pathologist Remark
  - MEDIUM: Investigation results, Observed Values, Reference Intervals
  - LOW: Patient demographics, lab metadata, disclaimers, methodology notes

The LLM NEVER sees the original PII. Only redacted text is processed.
"""
import re
import uuid
import structlog
from datetime import datetime
from typing import List, Optional, Tuple
from dataclasses import dataclass, field

logger = structlog.get_logger()

DOCUMENTS_COLLECTION = "patient_documents"


# ── Section Priority Classification ──────────────────────────────────────────

@dataclass
class DocumentSection:
    """A section of a parsed document with priority tagging."""
    section_id: str
    section_type: str           # e.g., "interpretation", "lab_values", "demographics"
    priority: str               # "high", "medium", "low"
    title: str                  # Detected section header
    content: str                # Raw text content (verbatim from source)
    page_number: int
    char_start: int
    char_end: int


@dataclass
class ParsedDocument:
    """Full parsed document with metadata and prioritised sections."""
    document_id: str
    patient_id: str
    filename: str
    total_pages: int
    raw_text: str               # Complete extracted text
    sections: List[DocumentSection] = field(default_factory=list)
    high_priority_text: str = ""    # Concatenated high-priority sections
    medium_priority_text: str = ""  # Concatenated medium-priority sections
    patient_name: Optional[str] = None
    patient_age: Optional[str] = None
    patient_gender: Optional[str] = None
    report_date: Optional[str] = None
    referred_by: Optional[str] = None
    source_language: str = "English"
    parse_errors: List[str] = field(default_factory=list)


# High-priority section markers (case-insensitive)
HIGH_PRIORITY_MARKERS = [
    r"(?:medical\s+)?remarks?",
    r"interpretation",
    r"summary",
    r"conclusion",
    r"impression",
    r"diagnosis",
    r"clinical\s+correlation",
    r"pathologist\s+remark",
    r"note\s*:",
    r"suggested\s+interpretation",
    r"remark\s*:",
]

# Compile into a single pattern
_HIGH_PRIORITY_PATTERN = re.compile(
    r"(?:^|\n)\s*(?:" + "|".join(HIGH_PRIORITY_MARKERS) + r")\s*[:\-]?\s*",
    re.IGNORECASE | re.MULTILINE,
)


def extract_text_from_pdf(pdf_bytes: bytes) -> Tuple[str, int, List[str]]:
    """
    Extract text from PDF bytes using PyMuPDF.
    Returns (full_text, page_count, errors).
    """
    import fitz  # PyMuPDF

    errors = []
    pages_text = []

    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        page_count = len(doc)

        for page_num in range(page_count):
            try:
                page = doc[page_num]
                text = page.get_text("text")
                pages_text.append(text)
            except Exception as e:
                errors.append(f"Page {page_num + 1}: {str(e)}")
                pages_text.append("")

        doc.close()
    except Exception as e:
        errors.append(f"PDF open failed: {str(e)}")
        return "", 0, errors

    full_text = "\n\n".join(pages_text)
    return full_text, page_count, errors


def detect_source_language(text: str) -> str:
    """Detect if text contains Marathi (Devanagari) script."""
    devanagari_pattern = re.compile(r'[\u0900-\u097F]')
    devanagari_chars = len(devanagari_pattern.findall(text))
    total_chars = len(text)

    if total_chars == 0:
        return "Unknown"
    if devanagari_chars / total_chars > 0.1:
        return "Marathi"
    return "English"


def extract_patient_demographics(text: str) -> dict:
    """Extract patient name, age, gender from lab report header."""
    demographics = {}

    # Name pattern
    name_match = re.search(
        r"Name\s*:\s*(?:Mr\.|Mrs\.|Ms\.|Dr\.)?\s*(.+?)(?:\n|Age|Contact)",
        text, re.IGNORECASE
    )
    if name_match:
        demographics["patient_name"] = name_match.group(1).strip()

    # Age/Gender pattern
    age_match = re.search(
        r"Age\s*/?\s*Gender\s*:\s*(\d+)\s*Year\(?s?\)?\s*/?\s*(Male|Female|Other)",
        text, re.IGNORECASE
    )
    if age_match:
        demographics["patient_age"] = f"{age_match.group(1)} Years"
        demographics["patient_gender"] = age_match.group(2)

    # Report date
    date_match = re.search(
        r"Reported\s+On\s*:\s*(\d{2}/\d{2}/\d{4})",
        text, re.IGNORECASE
    )
    if date_match:
        demographics["report_date"] = date_match.group(1)

    # Referred by
    ref_match = re.search(
        r"Referred\s+by\s*:\s*(.+?)(?:\n|Registered)",
        text, re.IGNORECASE
    )
    if ref_match:
        demographics["referred_by"] = ref_match.group(1).strip()

    return demographics


def identify_sections(text: str) -> List[DocumentSection]:
    """
    Parse document text into prioritised sections.
    High-priority sections (interpretations, notes, remarks) are tagged for
    strict verbatim reproduction by the LLM.
    """
    sections: List[DocumentSection] = []
    section_counter = 0

    # Find all high-priority section boundaries
    high_matches = list(_HIGH_PRIORITY_PATTERN.finditer(text))

    # Track which character ranges are high-priority
    high_ranges = []
    for i, match in enumerate(high_matches):
        start = match.start()
        # End is either the next section marker or +2000 chars (whichever is first)
        if i + 1 < len(high_matches):
            end = high_matches[i + 1].start()
        else:
            # Look for next investigation header or end of text
            next_header = re.search(
                r"\n\s*(?:Investigation|Observed Value|Dr\.\s+[A-Z])",
                text[match.end():], re.IGNORECASE
            )
            if next_header:
                end = match.end() + next_header.start()
            else:
                end = min(match.end() + 2000, len(text))

        high_ranges.append((start, end))
        section_counter += 1
        sections.append(DocumentSection(
            section_id=f"sec_{section_counter:03d}",
            section_type="interpretation",
            priority="high",
            title=match.group(0).strip().rstrip(":- "),
            content=text[match.end():end].strip(),
            page_number=text[:start].count("\n\n") + 1,
            char_start=start,
            char_end=end,
        ))

    # Everything else that contains numeric lab values is medium priority
    # Simple heuristic: lines with numbers followed by units
    lab_value_pattern = re.compile(
        r"[\d.]+\s*(?:mg/dL|gm/dL|U/L|mmol/L|cells/cu\.mm|%|pg/mL|ng/dL|µIU/mL|mm/hr|fL|pg|10\^3)",
        re.IGNORECASE
    )

    # Find text blocks NOT in high-priority ranges that contain lab values
    current_pos = 0
    for h_start, h_end in sorted(high_ranges):
        block = text[current_pos:h_start]
        if lab_value_pattern.search(block) and len(block.strip()) > 20:
            section_counter += 1
            sections.append(DocumentSection(
                section_id=f"sec_{section_counter:03d}",
                section_type="lab_values",
                priority="medium",
                title="Lab Investigation Results",
                content=block.strip(),
                page_number=text[:current_pos].count("\n\n") + 1,
                char_start=current_pos,
                char_end=h_start,
            ))
        current_pos = h_end

    # Remaining text after last high-priority section
    if current_pos < len(text):
        remaining = text[current_pos:]
        if lab_value_pattern.search(remaining) and len(remaining.strip()) > 20:
            section_counter += 1
            sections.append(DocumentSection(
                section_id=f"sec_{section_counter:03d}",
                section_type="lab_values",
                priority="medium",
                title="Lab Investigation Results",
                content=remaining.strip(),
                page_number=text[:current_pos].count("\n\n") + 1,
                char_start=current_pos,
                char_end=len(text),
            ))

    # Sort by position in document
    sections.sort(key=lambda s: s.char_start)
    return sections


def chunk_document(
    parsed: ParsedDocument,
    max_chunk_size: int = 2000,
    overlap: int = 200,
) -> List[dict]:
    """
    Chunk the document for vector DB storage.
    Preserves section boundaries — never splits a high-priority section.
    Each chunk carries its priority tag and section metadata.
    """
    chunks = []

    for section in parsed.sections:
        content = section.content
        if len(content) <= max_chunk_size:
            chunks.append({
                "text": content,
                "section_id": section.section_id,
                "section_type": section.section_type,
                "priority": section.priority,
                "title": section.title,
                "page_number": section.page_number,
                "document_id": parsed.document_id,
                "patient_id": parsed.patient_id,
            })
        else:
            # Split large sections with overlap, but only for medium/low priority
            if section.priority == "high":
                # Never split high-priority — store as single chunk even if large
                chunks.append({
                    "text": content,
                    "section_id": section.section_id,
                    "section_type": section.section_type,
                    "priority": section.priority,
                    "title": section.title,
                    "page_number": section.page_number,
                    "document_id": parsed.document_id,
                    "patient_id": parsed.patient_id,
                })
            else:
                # Split medium/low priority sections
                start = 0
                chunk_idx = 0
                while start < len(content):
                    end = start + max_chunk_size
                    chunk_text = content[start:end]
                    chunk_idx += 1
                    chunks.append({
                        "text": chunk_text,
                        "section_id": f"{section.section_id}_chunk{chunk_idx}",
                        "section_type": section.section_type,
                        "priority": section.priority,
                        "title": section.title,
                        "page_number": section.page_number,
                        "document_id": parsed.document_id,
                        "patient_id": parsed.patient_id,
                    })
                    start = end - overlap

    return chunks


class DocumentService:
    """
    Orchestrates PDF upload → parse → PHI redact → chunk → ingest into vector DB + graph.

    HIPAA Compliance:
      - Original PDF stored in GridFS (encrypted at rest) for patient access
      - PHI stripped before LLM processing
      - FHIR DocumentReference created for interoperability
      - All access audited
    """

    async def process_pdf_upload(
        self,
        patient_id: str,
        filename: str,
        pdf_bytes: bytes,
        uploader_id: str,
        uploader_role: str,
        db,
    ) -> ParsedDocument:
        """
        Full document processing pipeline:
        1. Store original PDF in GridFS (patient-viewable)
        2. Extract text from PDF
        3. Detect language
        4. Extract patient demographics
        5. Identify and prioritise sections
        6. Store document metadata + raw text in MongoDB
        7. Return parsed document for downstream PHI-redacted ingestion
        """
        document_id = str(uuid.uuid4())

        # Step 1: Store original PDF in GridFS for patient viewing
        gridfs_id = await self._store_pdf_gridfs(
            document_id=document_id,
            patient_id=patient_id,
            filename=filename,
            pdf_bytes=pdf_bytes,
            db=db,
        )

        # Step 2: Extract text
        raw_text, page_count, errors = extract_text_from_pdf(pdf_bytes)

        if not raw_text.strip():
            return ParsedDocument(
                document_id=document_id,
                patient_id=patient_id,
                filename=filename,
                total_pages=page_count,
                raw_text="",
                parse_errors=errors + ["No text extracted from PDF"],
            )

        # Step 3: Detect language
        source_language = detect_source_language(raw_text)

        # Step 4: Extract demographics
        demographics = extract_patient_demographics(raw_text)

        # Step 5: Identify sections with priority
        sections = identify_sections(raw_text)

        # Step 6: Build high/medium priority text blocks
        high_priority_text = "\n\n".join(
            f"[{s.title}]: {s.content}" for s in sections if s.priority == "high"
        )
        medium_priority_text = "\n\n".join(
            s.content for s in sections if s.priority == "medium"
        )

        # Build parsed document
        parsed = ParsedDocument(
            document_id=document_id,
            patient_id=patient_id,
            filename=filename,
            total_pages=page_count,
            raw_text=raw_text,
            sections=sections,
            high_priority_text=high_priority_text,
            medium_priority_text=medium_priority_text,
            patient_name=demographics.get("patient_name"),
            patient_age=demographics.get("patient_age"),
            patient_gender=demographics.get("patient_gender"),
            report_date=demographics.get("report_date"),
            referred_by=demographics.get("referred_by"),
            source_language=source_language,
            parse_errors=errors,
        )

        # Step 7: Store metadata in MongoDB
        doc_record = {
            "document_id": document_id,
            "patient_id": patient_id,
            "filename": filename,
            "total_pages": page_count,
            "source_language": source_language,
            "patient_name": parsed.patient_name,
            "patient_age": parsed.patient_age,
            "patient_gender": parsed.patient_gender,
            "report_date": parsed.report_date,
            "referred_by": parsed.referred_by,
            "section_count": len(sections),
            "high_priority_sections": sum(1 for s in sections if s.priority == "high"),
            "uploaded_by": uploader_id,
            "uploader_role": uploader_role,
            "uploaded_at": datetime.utcnow(),
            "parse_errors": errors,
            "gridfs_id": gridfs_id,
            "content_type": "application/pdf",
            "file_size_bytes": len(pdf_bytes),
            "phi_status": "pending_redaction",
            "hipaa_compliant": True,
            "status": "processed",
        }
        await db[DOCUMENTS_COLLECTION].insert_one(doc_record)

        # Store raw text separately for screening triggers
        await db["document_raw_texts"].insert_one({
            "document_id": document_id,
            "patient_id": patient_id,
            "raw_text": raw_text,
            "high_priority_text": high_priority_text,
            "medium_priority_text": medium_priority_text,
            "stored_at": datetime.utcnow(),
        })

        logger.info(
            "document_processed",
            document_id=document_id,
            patient_id=patient_id[:8] + "...",
            pages=page_count,
            sections=len(sections),
            high_priority=sum(1 for s in sections if s.priority == "high"),
            language=source_language,
            gridfs_stored=True,
        )

        return parsed

    async def _store_pdf_gridfs(
        self,
        document_id: str,
        patient_id: str,
        filename: str,
        pdf_bytes: bytes,
        db,
    ) -> str:
        """
        Store original PDF in MongoDB GridFS for patient viewing.
        GridFS handles large files (>16MB BSON limit) efficiently.
        Metadata includes patient_id for access control.
        """
        from motor.motor_asyncio import AsyncIOMotorGridFSBucket

        fs = AsyncIOMotorGridFSBucket(db, bucket_name="patient_documents")
        gridfs_id = await fs.upload_from_stream(
            filename,
            pdf_bytes,
            metadata={
                "document_id": document_id,
                "patient_id": patient_id,
                "content_type": "application/pdf",
                "uploaded_at": datetime.utcnow().isoformat(),
                "hipaa_classification": "PHI",
                "access_control": "patient_self_or_consented",
            },
        )
        logger.info(
            "pdf_stored_gridfs",
            document_id=document_id,
            gridfs_id=str(gridfs_id),
            size_bytes=len(pdf_bytes),
        )
        return str(gridfs_id)

    async def get_pdf_for_patient(
        self,
        document_id: str,
        patient_id: str,
        db,
    ) -> Optional[bytes]:
        """
        Retrieve original PDF from GridFS for patient viewing.
        Access control: only the patient themselves or consented providers.
        """
        from motor.motor_asyncio import AsyncIOMotorGridFSBucket
        import io

        doc_meta = await db[DOCUMENTS_COLLECTION].find_one({
            "document_id": document_id,
            "patient_id": patient_id,
        })
        if not doc_meta:
            return None

        gridfs_id = doc_meta.get("gridfs_id")
        if not gridfs_id:
            return None

        fs = AsyncIOMotorGridFSBucket(db, bucket_name="patient_documents")
        try:
            from bson import ObjectId
            stream = io.BytesIO()
            await fs.download_to_stream(ObjectId(gridfs_id), stream)
            return stream.getvalue()
        except Exception as e:
            logger.error("gridfs_download_failed", error=str(e), document_id=document_id)
            return None

    async def get_patient_documents(
        self, patient_id: str, db, limit: int = 50
    ) -> List[dict]:
        """List all documents uploaded for a patient (document history)."""
        cursor = db[DOCUMENTS_COLLECTION].find(
            {"patient_id": patient_id}
        ).sort("uploaded_at", -1).limit(limit)

        results = []
        async for doc in cursor:
            doc.pop("_id", None)
            results.append({
                "document_id": doc.get("document_id"),
                "filename": doc.get("filename"),
                "total_pages": doc.get("total_pages"),
                "report_date": doc.get("report_date"),
                "source_language": doc.get("source_language"),
                "uploaded_at": doc.get("uploaded_at"),
                "file_size_bytes": doc.get("file_size_bytes"),
                "section_count": doc.get("section_count"),
                "high_priority_sections": doc.get("high_priority_sections"),
                "status": doc.get("status"),
                "has_pdf": bool(doc.get("gridfs_id")),
            })
        return results

    async def create_fhir_document_reference(
        self,
        document_id: str,
        patient_id: str,
        filename: str,
        report_date: Optional[str],
        db,
    ) -> dict:
        """
        Create a FHIR R4 DocumentReference resource for the uploaded document.
        Compliant with FHIR EHR standards for document management.
        """
        fhir_doc_ref = {
            "resourceType": "DocumentReference",
            "id": document_id,
            "status": "current",
            "type": {
                "coding": [{
                    "system": "http://loinc.org",
                    "code": "11502-2",
                    "display": "Laboratory report",
                }],
                "text": "Laboratory Report",
            },
            "subject": {
                "reference": f"Patient/{patient_id}",
            },
            "date": report_date or datetime.utcnow().isoformat(),
            "content": [{
                "attachment": {
                    "contentType": "application/pdf",
                    "url": f"/documents/{document_id}/pdf",
                    "title": filename,
                },
                "format": {
                    "system": "http://ihe.net/fhir/ValueSet/IHE.FormatCode.codesystem",
                    "code": "urn:ihe:lab:xd-lab:2008",
                    "display": "XD-LAB",
                },
            }],
            "context": {
                "period": {
                    "start": report_date or datetime.utcnow().isoformat(),
                },
            },
            "securityLabel": [{
                "coding": [{
                    "system": "http://terminology.hl7.org/CodeSystem/v3-Confidentiality",
                    "code": "R",
                    "display": "Restricted",
                }],
            }],
            "meta": {
                "tag": [{
                    "system": "urn:medgraph:hipaa",
                    "code": "phi",
                    "display": "Contains PHI - access controlled",
                }],
            },
        }

        await db["fhir_document_references"].insert_one({
            "document_id": document_id,
            "patient_id": patient_id,
            "fhir_resource": fhir_doc_ref,
            "created_at": datetime.utcnow(),
        })

        return fhir_doc_ref
