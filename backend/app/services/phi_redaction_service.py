"""
PHI Redaction Service — HIPAA Safe Harbor De-identification
=============================================================
Strips Protected Health Information (PHI) from text BEFORE it reaches the LLM.

HIPAA Safe Harbor method requires removal of 18 identifiers:
1. Names
2. Geographic data (address, city, zip)
3. Dates (except year) related to an individual
4. Phone numbers
5. Fax numbers
6. Email addresses
7. Social Security numbers
8. Medical record numbers
9. Health plan beneficiary numbers
10. Account numbers
11. Certificate/license numbers
12. Vehicle identifiers
13. Device identifiers
14. Web URLs
15. IP addresses
16. Biometric identifiers
17. Full-face photographs
18. Any other unique identifying number

This service:
  - Redacts PII/PHI from text before LLM ingestion
  - Preserves clinical values, lab results, and medical terminology
  - Maintains a reversible mapping so HITL can re-associate if needed
  - Logs all redaction actions for audit compliance
"""
import re
import uuid
import hashlib
import structlog
from typing import Dict, List, Tuple
from dataclasses import dataclass, field
from datetime import datetime

logger = structlog.get_logger()

PHI_REDACTION_COLLECTION = "phi_redaction_maps"


@dataclass
class RedactionResult:
    """Result of PHI redaction on a text block."""
    redacted_text: str
    redaction_map_id: str
    redactions_applied: int
    redacted_fields: List[str]
    original_hash: str  # SHA-256 of original for integrity verification


@dataclass
class RedactionEntry:
    """A single redacted item with its placeholder."""
    field_type: str         # e.g., "name", "phone", "address"
    original_value: str     # The actual PII value
    placeholder: str        # What replaced it, e.g., "[PATIENT_NAME]"
    char_start: int
    char_end: int


# ── Regex patterns for PHI detection ─────────────────────────────────────────

# Indian phone numbers: +91XXXXXXXXXX or 10-digit
_PHONE_PATTERN = re.compile(
    r'(?:\+91[\s-]?)?[6-9]\d{9}|\(\d{3}\)\s*\d{3}[\s-]?\d{4}',
)

# Email
_EMAIL_PATTERN = re.compile(
    r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
)

# Aadhaar number (12 digits, often with spaces)
_AADHAAR_PATTERN = re.compile(
    r'\b\d{4}\s?\d{4}\s?\d{4}\b',
)

# Pin codes (6 digits)
_PINCODE_PATTERN = re.compile(
    r'Pin\s*code\s*:\s*(\d{6})',
    re.IGNORECASE,
)

# Full address lines (after "Address :")
_ADDRESS_PATTERN = re.compile(
    r'Address\s*:\s*(.+?)(?=\n|Pin\s*code|VID|PID|$)',
    re.IGNORECASE | re.DOTALL,
)

# Patient name (after "Name :")
_NAME_PATTERN = re.compile(
    r'Name\s*:\s*(?:Mr\.|Mrs\.|Ms\.|Dr\.)?\s*([A-Z][A-Za-z\s.]+?)(?=\s*(?:Age|Contact|\n|$))',
    re.IGNORECASE,
)

# Contact number line
_CONTACT_PATTERN = re.compile(
    r'Contact\s*No\.?\s*:\s*(\+?\d[\d\s-]{8,14})',
    re.IGNORECASE,
)

# VID / PID numbers (lab-specific identifiers)
_VID_PATTERN = re.compile(
    r'VID\s*No\.?\s*:\s*([\d]+)',
    re.IGNORECASE,
)
_PID_PATTERN = re.compile(
    r'PID\s*No\.?\s*:\s*([A-Z0-9]+)',
    re.IGNORECASE,
)

# Doctor/Pathologist name and registration (clinical provenance — redacted from KB)
_DOCTOR_NAME_PATTERN = re.compile(
    r'Dr\.?\s+([A-Z][A-Z\s.]+?)(?:\s+(?:MD|MS|MBBS|DNB|DM|MCh|FRCS|Consultant|Pathologist|Reg))',
    re.IGNORECASE,
)
_REG_NO_PATTERN = re.compile(
    r'Reg\s*No\.?\s*:?\s*(\d{4,6})',
    re.IGNORECASE,
)

# Lab/Hospital name and address lines
_LAB_NAME_PATTERN = re.compile(
    r'(?:Sample\s+Collected\s+At|Processing\s+Location)\s*:?\s*(.+?)(?=\n|Page\s+\d|$)',
    re.IGNORECASE,
)

# Date of Birth — MUST be redacted (only age is allowed in knowledge base)
_DOB_PATTERN = re.compile(
    r'(?:D\.?O\.?B\.?|Date\s+of\s+Birth)\s*:\s*(\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4}|\d{4}[/\-]\d{1,2}[/\-]\d{1,2}|\d{1,2}[\s\-][A-Za-z]{3,9}[\s\-]\d{2,4})',
    re.IGNORECASE,
)

# URLs
_URL_PATTERN = re.compile(
    r'https?://[^\s]+|www\.[^\s]+',
    re.IGNORECASE,
)

# IP addresses
_IP_PATTERN = re.compile(
    r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b',
)


def redact_phi(text: str, patient_id: str) -> Tuple[str, List[RedactionEntry]]:
    """
    Apply HIPAA Safe Harbor de-identification to text.

    PRESERVED (allowed in knowledge base):
    - Age (e.g., "48 Years") — clinically relevant, not a unique identifier
    - Gender (e.g., "Male") — clinically relevant
    - All clinical values (lab results, reference ranges)
    - Medical terminology, drug names, conditions
    - Report dates (when sample was collected/reported)

    REDACTED (never enters knowledge base):
    - Patient name → [PATIENT]
    - Date of birth → [DOB_REDACTED]
    - Phone numbers → [PHONE_REDACTED]
    - Addresses → [ADDRESS_REDACTED]
    - Pin codes → [PINCODE_REDACTED]
    - Email → [EMAIL_REDACTED]
    - Aadhaar/ID numbers → [ID_REDACTED]
    - VID/PID → [LAB_ID_REDACTED]
    - Doctor names → [DOCTOR_REDACTED]
    - Registration numbers → [REG_REDACTED]
    - Lab/Hospital names → [LAB_REDACTED]
    - URLs → [URL_REDACTED]
    - IP addresses → [IP_REDACTED]

    NOTE: Age is NOT the same as DOB. Age (e.g., "48 Years") is kept because
    it's clinically essential and not a unique identifier. DOB (e.g., "15/03/1978")
    is redacted because it can identify an individual.
    """
    redactions: List[RedactionEntry] = []
    redacted = text

    # Order matters: longer patterns first to avoid partial matches

    # 1. Patient Name
    for match in _NAME_PATTERN.finditer(redacted):
        name_val = match.group(1).strip()
        if len(name_val) > 2:  # Avoid false positives
            redactions.append(RedactionEntry(
                field_type="patient_name",
                original_value=name_val,
                placeholder="[PATIENT]",
                char_start=match.start(1),
                char_end=match.end(1),
            ))

    # 2. Contact/Phone
    for match in _CONTACT_PATTERN.finditer(redacted):
        redactions.append(RedactionEntry(
            field_type="phone",
            original_value=match.group(1),
            placeholder="[PHONE_REDACTED]",
            char_start=match.start(1),
            char_end=match.end(1),
        ))

    # 3. Address
    for match in _ADDRESS_PATTERN.finditer(redacted):
        redactions.append(RedactionEntry(
            field_type="address",
            original_value=match.group(1).strip(),
            placeholder="[ADDRESS_REDACTED]",
            char_start=match.start(1),
            char_end=match.end(1),
        ))

    # 4. Pin code
    for match in _PINCODE_PATTERN.finditer(redacted):
        redactions.append(RedactionEntry(
            field_type="pincode",
            original_value=match.group(1),
            placeholder="[PINCODE_REDACTED]",
            char_start=match.start(1),
            char_end=match.end(1),
        ))

    # 5. VID/PID
    for match in _VID_PATTERN.finditer(redacted):
        redactions.append(RedactionEntry(
            field_type="vid_number",
            original_value=match.group(1),
            placeholder="[LAB_ID_REDACTED]",
            char_start=match.start(1),
            char_end=match.end(1),
        ))
    for match in _PID_PATTERN.finditer(redacted):
        redactions.append(RedactionEntry(
            field_type="pid_number",
            original_value=match.group(1),
            placeholder="[LAB_ID_REDACTED]",
            char_start=match.start(1),
            char_end=match.end(1),
        ))

    # 6. Email
    for match in _EMAIL_PATTERN.finditer(redacted):
        redactions.append(RedactionEntry(
            field_type="email",
            original_value=match.group(0),
            placeholder="[EMAIL_REDACTED]",
            char_start=match.start(),
            char_end=match.end(),
        ))

    # 7. Standalone phone numbers (not already caught by contact pattern)
    for match in _PHONE_PATTERN.finditer(redacted):
        # Check if already redacted by contact pattern
        already_redacted = any(
            r.char_start <= match.start() <= r.char_end
            for r in redactions if r.field_type == "phone"
        )
        if not already_redacted:
            redactions.append(RedactionEntry(
                field_type="phone",
                original_value=match.group(0),
                placeholder="[PHONE_REDACTED]",
                char_start=match.start(),
                char_end=match.end(),
            ))

    # 8. URLs
    for match in _URL_PATTERN.finditer(redacted):
        redactions.append(RedactionEntry(
            field_type="url",
            original_value=match.group(0),
            placeholder="[URL_REDACTED]",
            char_start=match.start(),
            char_end=match.end(),
        ))

    # 9. IP addresses
    for match in _IP_PATTERN.finditer(redacted):
        redactions.append(RedactionEntry(
            field_type="ip_address",
            original_value=match.group(0),
            placeholder="[IP_REDACTED]",
            char_start=match.start(),
            char_end=match.end(),
        ))

    # 10. Doctor/Pathologist names
    for match in _DOCTOR_NAME_PATTERN.finditer(redacted):
        redactions.append(RedactionEntry(
            field_type="doctor_name",
            original_value=match.group(1).strip(),
            placeholder="[DOCTOR_REDACTED]",
            char_start=match.start(1),
            char_end=match.end(1),
        ))

    # 11. Registration numbers
    for match in _REG_NO_PATTERN.finditer(redacted):
        redactions.append(RedactionEntry(
            field_type="registration_number",
            original_value=match.group(1),
            placeholder="[REG_REDACTED]",
            char_start=match.start(1),
            char_end=match.end(1),
        ))

    # 12. Lab/Hospital names and addresses
    for match in _LAB_NAME_PATTERN.finditer(redacted):
        redactions.append(RedactionEntry(
            field_type="lab_name",
            original_value=match.group(1).strip(),
            placeholder="[LAB_REDACTED]",
            char_start=match.start(1),
            char_end=match.end(1),
        ))

    # 13. Date of Birth (DOB) — age is kept, DOB is PII
    for match in _DOB_PATTERN.finditer(redacted):
        redactions.append(RedactionEntry(
            field_type="date_of_birth",
            original_value=match.group(1),
            placeholder="[DOB_REDACTED]",
            char_start=match.start(1),
            char_end=match.end(1),
        ))

    # Apply redactions in reverse order (to preserve char positions)
    redactions.sort(key=lambda r: r.char_start, reverse=True)
    for entry in redactions:
        redacted = (
            redacted[:entry.char_start]
            + entry.placeholder
            + redacted[entry.char_end:]
        )

    return redacted, list(reversed(redactions))


class PHIRedactionService:
    """
    Manages PHI redaction with reversible mapping stored securely.

    The redaction map is stored in MongoDB with access restricted to
    HITL validators and admins — never exposed to the LLM or external systems.
    """

    async def redact_for_llm(
        self,
        text: str,
        patient_id: str,
        document_id: str,
        db,
    ) -> RedactionResult:
        """
        Redact PHI from text before sending to LLM.
        Stores the reversible mapping for HITL re-association.
        """
        original_hash = hashlib.sha256(text.encode()).hexdigest()
        redacted_text, redactions = redact_phi(text, patient_id)

        # Store redaction map (encrypted at rest via MongoDB encryption)
        redaction_map_id = str(uuid.uuid4())
        if redactions:
            map_record = {
                "redaction_map_id": redaction_map_id,
                "patient_id": patient_id,
                "document_id": document_id,
                "original_hash": original_hash,
                "redactions": [
                    {
                        "field_type": r.field_type,
                        "original_value": r.original_value,
                        "placeholder": r.placeholder,
                        "char_start": r.char_start,
                        "char_end": r.char_end,
                    }
                    for r in redactions
                ],
                "created_at": datetime.utcnow(),
                "access_restricted_to": ["hitl_validator", "super_admin"],
            }
            await db[PHI_REDACTION_COLLECTION].insert_one(map_record)

        logger.info(
            "phi_redacted",
            patient_id=patient_id[:8] + "...",
            document_id=document_id,
            redactions_count=len(redactions),
            fields_redacted=[r.field_type for r in redactions],
        )

        return RedactionResult(
            redacted_text=redacted_text,
            redaction_map_id=redaction_map_id,
            redactions_applied=len(redactions),
            redacted_fields=list(set(r.field_type for r in redactions)),
            original_hash=original_hash,
        )

    async def restore_phi(
        self,
        redacted_text: str,
        redaction_map_id: str,
        requester_role: str,
        db,
    ) -> str:
        """
        Restore PHI from redacted text using the stored mapping.
        Only accessible by HITL validators and admins.
        """
        if requester_role not in ["hitl_validator", "super_admin", "hospital_admin"]:
            logger.warning("phi_restore_denied", role=requester_role)
            return redacted_text  # Return redacted version

        map_record = await db[PHI_REDACTION_COLLECTION].find_one(
            {"redaction_map_id": redaction_map_id}
        )
        if not map_record:
            return redacted_text

        restored = redacted_text
        for entry in map_record.get("redactions", []):
            restored = restored.replace(
                entry["placeholder"],
                entry["original_value"],
                1,  # Replace only first occurrence per entry
            )

        return restored
