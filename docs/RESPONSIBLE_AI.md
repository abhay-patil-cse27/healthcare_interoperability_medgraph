# Responsible AI — Antigravity Agent

> Consent-gated · HITL-validated · Strictly word-bounded · HIPAA compliant

---

## Architecture

```
┌─────────┐     ┌──────────────┐     ┌──────────────┐     ┌───────────────┐     ┌────────┐
│ Patient │────▶│ PDF Upload   │────▶│ Consent      │────▶│ AI Screening  │────▶│  HITL  │
│         │     │ + PHI Redact │     │ Engine       │     │ (Word-Bounded)│     │Validator│
└─────────┘     └──────────────┘     └──────────────┘     └───────────────┘     └────┬───┘
                       │                                                              │
                       ▼                                                    ┌─────────┴─────────┐
                ┌──────────────┐                                            │                   │
                │ Vector DB    │◀── PHI-redacted chunks                EDIT & Forward    ACCEPT & Forward
                │ (Qdrant)     │    with priority tags                      │                   │
                └──────────────┘                                            ▼                   ▼
                       │                                            ┌───────────────────────────────┐
                       ▼                                            │  Time-Bound Consent Created   │
                ┌──────────────┐                                    │  for Target Doctor             │
                │ Graph DB     │                                    └───────────────┬───────────────┘
                │ (Neo4j)      │                                                    │
                └──────────────┘                                                    ▼
                                                                            ┌───────────────┐
                                                                            │    Doctor     │
                                                                            │ (Time-Bound)  │
                                                                            └───────────────┘
```

---

## Four-Eye Model

Every AI-generated clinical output passes through:
1. **AI Agent** (Antigravity) — generates grounded, word-bounded summary
2. **HITL Operator** — verifies patient identity and output accuracy
3. **Doctor** — reviews and acts on verified summary

**No AI output reaches a doctor without HITL verification.**

---

## Pipeline Stages

| Stage | Value | Description |
|-------|-------|-------------|
| 1 | `ai_generated` | AI has produced summary, sitting in HITL queue |
| 2 | `hitl_in_review` | HITL operator is actively reviewing |
| 3a | `hitl_edited` | HITL edited and forwarded (creates time-bound consent) |
| 3b | `hitl_accepted` | HITL accepted as-is and forwarded |
| 3c | `hitl_rejected` | HITL rejected — needs re-processing |
| 3d | `hitl_escalated` | Escalated to admin |
| 4 | `doctor_consent_active` | Doctor has active time-bound access |
| 5 | `doctor_reviewed` | Doctor has reviewed (pipeline complete) |
| 6 | `consent_expired` | Doctor's time-bound access expired |

---

## Strictly Word-Bounded LLM Output

The system prompt enforces:

1. **Output contains ONLY words from the source document**
2. **High-priority sections reproduced VERBATIM** (Interpretation, Note, Remark, Summary, Conclusion, Pathologist Remark)
3. **Numerical values reproduced EXACTLY** — no rounding, no paraphrasing
4. **No clinical knowledge injection** — LLM cannot add information not in source
5. **Non-diagnostic language only** — "may indicate", "consistent with", "warrants review"
6. **Missing data → "Data not available"** — never inferred

---

## Section Priority System

| Priority | Sections | Treatment |
|----------|----------|-----------|
| HIGH | Interpretation, Note, Remark, Summary, Conclusion, Impression, Pathologist Remark, Medical Remarks, Suggested Interpretation | Reproduced VERBATIM. Never split during chunking. |
| MEDIUM | Lab values, observed measurements, reference ranges | Values reproduced exactly. Abnormalities flagged. |
| LOW | Demographics, methodology, disclaimers | Included for context. Can be summarised. |

---

## PHI Redaction (HIPAA Safe Harbor)

Applied BEFORE any LLM processing:

| PII Type | Placeholder | Example |
|----------|-------------|---------|
| Patient name | `[PATIENT]` | AMOL G PATIL → [PATIENT] |
| Date of birth | `[DOB_REDACTED]` | 15/03/1978 → [DOB_REDACTED] |
| Phone | `[PHONE_REDACTED]` | +919922307401 → [PHONE_REDACTED] |
| Address | `[ADDRESS_REDACTED]` | GRUYOG APAT FLAT... → [ADDRESS_REDACTED] |
| Pin code | `[PINCODE_REDACTED]` | 416006 → [PINCODE_REDACTED] |
| Lab IDs | `[LAB_ID_REDACTED]` | VID/PID numbers → [LAB_ID_REDACTED] |
| Doctor name | `[DOCTOR_REDACTED]` | RAJENDRA PATIL → [DOCTOR_REDACTED] |
| Reg number | `[REG_REDACTED]` | 60811 → [REG_REDACTED] |
| Lab/Hospital | `[LAB_REDACTED]` | Metropolis Healthcare → [LAB_REDACTED] |
| Email | `[EMAIL_REDACTED]` | — |
| URLs | `[URL_REDACTED]` | — |
| IP addresses | `[IP_REDACTED]` | — |

**Preserved**: Age (years), gender, all clinical values, reference ranges, medical terminology.

---

## Deterministic Abnormality Detection

30+ lab parameters with regex-based extraction and classification:

```
NORMAL:   within reference range
HIGH:     above upper limit
LOW:      below lower limit
CRITICAL: >2x deviation from range boundary
```

Parameters covered: Glucose, HbA1c, Bilirubin (total/direct/indirect), Proteins, SGPT/ALT, SGOT/AST, Creatinine, BUN, Uric Acid, Cholesterol, Triglycerides, HDL, LDL, VLDL, Sodium, Potassium, Chloride, Haemoglobin, RBC, PCV, WBC, Platelets, Eosinophils, Basophils, ESR, TSH, FT3, FT4, Vitamin B12, Vitamin D, Phosphorus, Calcium.

---

## HITL Validator Role

| Permission | Description |
|-----------|-------------|
| `screening:validate` | View and validate AI screenings |
| `screening:edit` | Edit AI summary before forwarding |
| `screening:forward` | Forward to doctor with time-bound consent |
| `screening:escalate` | Escalate to admin |
| `screening:view_pending` | View the HITL queue |

---

## Escalation Triggers

Escalate to admin when:
- Patient identity cannot be confirmed
- Record history is inconsistent across sources
- HITL operator is unavailable for critical findings
- Critical abnormalities detected (>2x reference range deviation)

---

## Compliance

- **HIPAA**: Safe Harbor de-identification, minimum necessary rule, audit trail
- **FHIR R4**: DocumentReference for every uploaded document (LOINC 11502-2)
- **DPDP Act 2023**: Patient data sovereignty, consent-gated access
- **Non-maleficence**: Uncertain values flagged for human review, never inferred
- **Transparency**: All AI outputs labelled "(AI-generated — not a diagnosis)"
- **Accountability**: Every summary linked to verifiable source document
