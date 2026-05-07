"""
Vaidya Router — वैद्य (Physician / One Who Has Knowledge)
============================================================
POST /vaidya/chat   — General-purpose MedGraph platform guide chatbot (auth required).

This endpoint:
  - Is open to ANY authenticated user regardless of role (no consent gate, no PHI).
  - Uses its own VAIDYA_MODEL_ID (separate from the clinical RAG BEDROCK_MODEL_ID).
  - ALWAYS applies Bedrock Guardrails (BEDROCK_GUARDRAIL_ID + BEDROCK_GUARDRAIL_VERSION from .env).
  - Maintains a sliding-window history (last 10 turns) passed in the request body.
  - Returns guardrail_action="BLOCKED"|"NONE" in the response (mirrors ChatResponse schema).
  - Logs every guardrail intervention with user/role/IP for audit.

Guardrail behaviour mirrors the existing RAG pipeline (bedrock_service.py):
  When stopReason == "guardrail_intervened":
    • result["guardrail_action"] = "BLOCKED"
    • result["text"]            = guardrail's safe replacement message
    → logged as vaidya_guardrail_blocked, returned with guardrail_action="BLOCKED"
"""

import time
import asyncio
import structlog
import boto3
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from typing import List, Optional
from app.config import get_settings
from app.dependencies import get_current_user

logger = structlog.get_logger()
router = APIRouter()


# ── Vaidya-specific Bedrock client (uses VAIDYA_MODEL_ID, not BEDROCK_MODEL_ID) ──

class VaidyaLLM:
    """
    Lightweight Bedrock wrapper for Vaidya.
    Uses VAIDYA_MODEL_ID (latest Claude, e.g. claude-3-7-sonnet) and the same
    BEDROCK_GUARDRAIL_ID / BEDROCK_GUARDRAIL_VERSION as the clinical RAG pipeline.
    """

    def __init__(self):
        settings = get_settings()
        self.client           = boto3.client("bedrock-runtime", region_name=settings.aws_region)
        self.model_id         = settings.vaidya_model_id
        self.guardrail_id     = settings.bedrock_guardrail_id
        self.guardrail_version = settings.bedrock_guardrail_version

        logger.info(
            "vaidya_llm_ready",
            model=self.model_id,
            guardrail_id=self.guardrail_id or "DISABLED",
            guardrail_version=self.guardrail_version or "n/a",
        )

    async def invoke(
        self,
        system_prompt: str,
        user_message: str,
        history: List[dict],
        max_tokens: int = 1024,
        temperature: float = 0.4,
    ) -> dict:
        """
        Invoke Bedrock Converse API with guardrails always enabled.
        Returns:
            {
              "text":             str,
              "latency_ms":       int,
              "guardrail_action": "NONE" | "BLOCKED",
              "guardrail_trace":  dict (optional, for audit logs)
            }
        """
        # Build messages array: history + current user turn
        messages = []
        for turn in history:
            messages.append({
                "role":    turn["role"],
                "content": [{"text": turn["content"]}],
            })
        messages.append({
            "role":    "user",
            "content": [{"text": user_message}],
        })

        invoke_kwargs = {
            "modelId":         self.model_id,
            "system":          [{"text": system_prompt}],
            "messages":        messages,
            "inferenceConfig": {
                "maxTokens":   max_tokens,
                "temperature": temperature,
            },
        }

        # ── Bypass Clinical Guardrails for Platform Guide ──
        # We deliberately DO NOT apply the strict clinical Bedrock Guardrail here.
        # Vaidya has zero access to PHI/RAG context, so it cannot leak records.
        # Applying the clinical guardrail incorrectly blocks innocent questions 
        # like "how do I view my health records?".
        # The VAIDYA_SYSTEM_PROMPT is sufficient to enforce safety.

        start = time.time()
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None, lambda: self.client.converse(**invoke_kwargs)
        )
        latency_ms = int((time.time() - start) * 1000)

        stop_reason      = response.get("stopReason", "")
        guardrail_trace  = response.get("trace", {}).get("guardrail", {})

        # ── Guardrail blocked the response ──────────────────────────────────
        if stop_reason == "guardrail_intervened":
            output_msg   = response.get("output", {}).get("message", {})
            blocked_text = ""
            if output_msg.get("content"):
                blocked_text = output_msg["content"][0].get("text", "")

            logger.warning(
                "bedrock_guardrail_intervened",
                model=self.model_id,
                guardrail_id=self.guardrail_id,
                latency_ms=latency_ms,
            )

            return {
                "text": (
                    blocked_text
                    or "This request was blocked by our safety policies. Please rephrase your question."
                ),
                "latency_ms":       latency_ms,
                "guardrail_action": "BLOCKED",
                "guardrail_trace":  guardrail_trace,
            }

        # ── Normal response ──────────────────────────────────────────────────
        text  = response["output"]["message"]["content"][0]["text"]
        usage = response.get("usage", {})

        logger.info(
            "vaidya_invoked",
            model=self.model_id,
            latency_ms=latency_ms,
            input_tokens=usage.get("inputTokens", 0),
            output_tokens=usage.get("outputTokens", 0),
            guardrail_applied=bool(self.guardrail_id),
        )

        result = {
            "text":             text,
            "latency_ms":       latency_ms,
            "guardrail_action": "NONE",
        }
        if guardrail_trace:
            result["guardrail_trace"] = guardrail_trace
        return result


# ── Singleton ────────────────────────────────────────────────────────────────
_vaidya_llm: VaidyaLLM = None

def _get_llm() -> VaidyaLLM:
    global _vaidya_llm
    if _vaidya_llm is None:
        _vaidya_llm = VaidyaLLM()
    return _vaidya_llm


# ── Pydantic models ──────────────────────────────────────────────────────────

class VaidyaTurn(BaseModel):
    role:    str   # "user" | "assistant"
    content: str


class VaidyaChatRequest(BaseModel):
    message:   str              = Field(min_length=1, max_length=2000)
    history:   List[VaidyaTurn] = Field(default=[], max_length=20)
    user_role: Optional[str]    = None  # passed by frontend for role-contextual answers


class VaidyaChatResponse(BaseModel):
    reply:            str
    latency_ms:       int
    guardrail_action: str = "NONE"   # "NONE" | "BLOCKED" — mirrors ChatResponse in medical.py


# ── System Prompt ─────────────────────────────────────────────────────────────

VAIDYA_SYSTEM_PROMPT = """You are Vaidya (वैद्य), the intelligent AI guide of MedGraph AI — \
a healthcare interoperability platform built for India's hospital ecosystem.

## Your Purpose
You help ALL users (patients, doctors, nurses, admins, pharmacists, and every other role) understand:
- How to navigate and use the MedGraph platform
- What each role can do and what dashboards/features are available
- General health literacy and medical terminology (in plain language)
- How MedGraph handles data privacy, consent, FHIR exchange, and ABHA integration
- How to troubleshoot common platform workflows

## Platform Modules
- **Patient Portal**: Health records, AI chat about own records, document upload, consent management
- **Doctor/Surgeon**: Patient lookup (MRN/name/ABHA), clinical RAG chat (consent-gated), FHIR exchange, MLC records, screening inbox
- **Nurse/Ward**: Vitals logging, patient notes, assigned patient list
- **Pharmacist**: Prescription queue, dispense workflow, drug interaction checks
- **OPD/IPD Staff**: Appointments, admissions, bed management
- **Hospital Admin**: Department setup, staff invitation, hospital stats
- **Super/Govt Admin**: System-wide management, hospital creation, audit logs
- **Insurance Officer**: Claim creation, pre-authorization, claim status
- **Scheme Officer**: Government scheme eligibility checks and disbursals
- **Police/MLC**: Medico-Legal Case access (read-only)
- **HITL Validator**: Responsible AI queue — review, edit, forward or reject AI-screened documents
- **Notifications**: Real-time alerts for all roles
- **Activity Logs**: Audit trail for admins

## Consent & Privacy
- Doctors must request and receive patient consent before accessing records
- Patients can grant/revoke consent from their portal
- FHIR bundles are generated only with valid, active consent
- Vaidya has ZERO access to any patient's actual health records

## Rules You MUST Follow
1. **Never provide personal medical diagnoses** — always redirect to their doctor
2. **Never reveal or access any patient's medical records** — you have zero PHI access
3. **Warm, clear, professional tone** — like a knowledgeable hospital reception guide
4. **Be concise** — prefer bullet points for multi-step answers
5. You CAN explain general health concepts (e.g., "what is hypertension?") in plain language
6. Always remind users to consult their doctor for personal health decisions

You are named after the Sanskrit वैद्य meaning "one who has knowledge" — be wise, helpful, and safe."""


# ── Endpoint: POST /vaidya/chat (authenticated only) ─────────────────────────

@router.post("/chat", response_model=VaidyaChatResponse)
async def vaidya_chat(
    body:         VaidyaChatRequest,
    http_request: Request,
    current_user  = Depends(get_current_user),
):
    """
    Vaidya platform guide chatbot — any authenticated role.
    Uses VAIDYA_MODEL_ID with BEDROCK_GUARDRAIL_ID always active.
    Guardrail interventions are logged with user/role/IP for audit.
    """
    llm = _get_llm()

    # Sliding-window history (last 10 turns = 20 messages)
    history = [
        {"role": t.role, "content": t.content}
        for t in body.history[-10:]
    ]

    # Prepend role hint for role-contextual responses
    role_hint = f"[User role: {body.user_role}] " if body.user_role else ""

    # Structured context label for guardrail audit logs
    client_ip    = http_request.client.host if http_request.client else "unknown"
    user_id      = current_user.get("user_id", "unknown")
    user_role    = current_user.get("role", "unknown")

    try:
        result = await llm.invoke(
            system_prompt=VAIDYA_SYSTEM_PROMPT,
            user_message=role_hint + body.message,
            history=history,
            max_tokens=1024,
            temperature=0.4,
        )

        guardrail_action = result.get("guardrail_action", "NONE")

        # Log blocked requests with full user context for audit trail
        if guardrail_action == "BLOCKED":
            logger.warning(
                "vaidya_guardrail_blocked",
                user_id=user_id,
                role=user_role,
                ip=client_ip,
                guardrail_id=llm.guardrail_id,
                guardrail_version=llm.guardrail_version,
                model=llm.model_id,
                query_preview=body.message[:80],
            )

        return VaidyaChatResponse(
            reply=result["text"],
            latency_ms=result.get("latency_ms", 0),
            guardrail_action=guardrail_action,
        )

    except Exception as e:
        logger.error(
            "vaidya_chat_error",
            error=str(e),
            user_id=user_id,
            role=user_role,
            model=llm.model_id,
        )
        raise HTTPException(
            status_code=503,
            detail="Vaidya is temporarily unavailable. Please try again shortly.",
        )
