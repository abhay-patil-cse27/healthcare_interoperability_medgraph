"""
Chat Router
============
POST /chat/              — Send a message (consent-gated, session-aware, cache-backed)
GET  /chat/sessions      — List user's active chat sessions
POST /chat/sessions      — Explicitly create a new session
GET  /chat/sessions/{id} — Get full message history for a session
DELETE /chat/sessions/{id} — Close/archive a session
GET  /chat/cache/stats   — Cache health stats (admin/debug)
"""
import time
import uuid
import structlog
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from app.models.medical import ChatRequest, ChatResponse
from app.dependencies import get_db, get_current_user, require_permission, get_mongo_client
from app.models.rbac import Permission
from app.pipelines.retrieval_pipeline import RetrievalPipeline
from app.services.consent_service import ConsentService
from app.services.chat_history_service import ChatHistoryService
from app.services.cache_service import ResponseCacheService
from app.services.audit_service import log_phi_access
from app.config import get_settings

logger = structlog.get_logger()
router = APIRouter()

consent_svc = ConsentService()
history_svc = ChatHistoryService()
cache_svc   = ResponseCacheService()

_pipeline: RetrievalPipeline = None


def get_pipeline() -> RetrievalPipeline:
    global _pipeline
    if _pipeline is None:
        _pipeline = RetrievalPipeline()
    return _pipeline


async def _audit_chat(action, patient_id, accessor_id, accessor_role, resource_type, request_id, metadata):
    settings = get_settings()
    db = get_mongo_client()[settings.mongodb_db]
    await log_phi_access(
        action=action, patient_id=patient_id, accessor_id=accessor_id,
        accessor_role=accessor_role, resource_type=resource_type,
        request_id=request_id, db=db, metadata=metadata,
    )


# ── POST /chat/ ────────────────────────────────────────────────────────────────

@router.post("/", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    background_tasks: BackgroundTasks,
    current_user=Depends(get_current_user),
    db=Depends(get_db),
):
    start_ms = int(time.time() * 1000)
    request_id = str(uuid.uuid4())

    # 1. Consent gate
    access = await consent_svc.check_access(
        requester_id=current_user["user_id"],
        requester_role=current_user["role"],
        patient_id=request.patient_id,
        db=db,
    )
    if not access.allowed:
        raise HTTPException(
            status_code=403,
            detail={
                "error": "CONSENT_DENIED",
                "reason": access.reason,
                "patient_id": request.patient_id,
            },
        )

    # 2. Resolve or create session
    session = None
    if request.session_id:
        session = await history_svc.get_session(db, request.session_id)
        # Validate that this session belongs to the current user
        if session and session["user_id"] != current_user["user_id"]:
            raise HTTPException(status_code=403, detail="Session does not belong to current user")

    if not session:
        session = await history_svc.create_session(
            db=db,
            user_id=current_user["user_id"],
            user_role=current_user["role"],
            patient_id=request.patient_id,
            consent_id=access.consent_id,
            consent_scope=access.scope,
        )

    session_id = session["session_id"]

    # 3. Load conversation history for LLM context
    history_msgs = await history_svc.get_history(db, session_id)
    llm_history   = history_svc.build_history_for_llm(history_msgs)
    history_turns = len(llm_history) // 2  # each turn = 1 user + 1 assistant

    # 4. Cache lookup (skip cache if there's active conversation history,
    #    since the same question may need a different answer in context)
    cache_hit = False
    result = None
    if not llm_history:  # Only use cache for the first turn (no prior context)
        result = await cache_svc.get(db, request.patient_id, request.query)
        if result:
            cache_hit = True
            logger.info("cache_served", session_id=session_id, query_preview=request.query[:50])

    # 5. Run RAG pipeline if not cached
    if not result:
        pipeline = get_pipeline()
        result = await pipeline.run(
            patient_id=request.patient_id,
            query=request.query,
            consent_scope=access.scope or "full",
            consent_filters=access.filters or {},
            request_id=request_id,
            history=llm_history,
        )
        # Store in cache (only when no history, so it's a "pure" result)
        if not llm_history:
            background_tasks.add_task(
                _write_cache, db, request.patient_id, request.query, result
            )

    # 6. Persist conversation turn to history
    await history_svc.append_message(
        db, session_id, role="user", content=request.query,
        metadata={"request_id": request_id},
    )
    await history_svc.append_message(
        db, session_id, role="assistant", content=result["response"],
        metadata={
            "request_id": request_id,
            "citations": result["citations"],
            "cache_hit": cache_hit,
            "retrieval_time_ms": result.get("retrieval_time_ms", 0),
            "llm_time_ms": result.get("llm_time_ms", 0),
        },
    )

    total_time_ms = int(time.time() * 1000) - start_ms

    background_tasks.add_task(
        _audit_chat,
        action="CHAT_QUERY",
        patient_id=request.patient_id,
        accessor_id=current_user["user_id"],
        accessor_role=current_user["role"],
        resource_type="PatientQuery",
        request_id=request_id,
        metadata={
            "session_id": session_id,
            "consent_scope": access.scope,
            "consent_id": access.consent_id,
            "cache_hit": cache_hit,
            "history_turns": history_turns,
            "query_preview": request.query[:100],
        },
    )

    return ChatResponse(
        request_id=request_id,
        session_id=session_id,
        response=result["response"],
        citations=result["citations"],
        graph_nodes_used=result.get("graph_nodes_used", 0),
        vector_entries_used=result.get("vector_entries_used", 0),
        retrieval_time_ms=result.get("retrieval_time_ms", 0),
        llm_time_ms=result.get("llm_time_ms", 0),
        total_time_ms=total_time_ms,
        cache_hit=cache_hit,
        history_turns=history_turns,
    )


async def _write_cache(db, patient_id: str, query: str, result: dict):
    """Background task to write result to cache without blocking the response."""
    await cache_svc.set(db, patient_id, query, result)


# ── Debug / Diagnostic ─────────────────────────────────────────────────────────

@router.get("/debug/consent/{patient_id}")
async def debug_consent(
    patient_id: str,
    current_user=Depends(get_current_user),
    db=Depends(get_db),
):
    """
    Debug endpoint: shows exactly what the consent service finds in MongoDB
    for the current user + patient pair. Helps diagnose 403 on /chat/.
    Remove or gate behind admin role before going to production.
    """
    from datetime import datetime, timezone

    doctor_id = current_user["user_id"]

    # Raw records (any status, any expiry)
    raw_records = []
    async for doc in db["consents"].find({"doctor_id": doctor_id, "patient_id": patient_id}):
        doc.pop("_id", None)
        # Stringify datetimes for JSON serialisation
        for k, v in doc.items():
            if isinstance(v, datetime):
                doc[k] = v.isoformat()
        raw_records.append(doc)

    # What check_access actually returns
    access = await consent_svc.check_access(
        requester_id=doctor_id,
        requester_role=current_user["role"],
        patient_id=patient_id,
        db=db,
    )

    return {
        "doctor_id": doctor_id,
        "patient_id": patient_id,
        "server_utc_now": datetime.now(timezone.utc).isoformat(),
        "raw_consent_records": raw_records,
        "check_access_result": {
            "allowed": access.allowed,
            "reason": access.reason,
            "scope": access.scope,
            "consent_id": access.consent_id,
        },
    }


# ── Session Management Endpoints ───────────────────────────────────────────────

@router.get("/sessions")
async def list_sessions(
    patient_id: str = None,
    current_user=Depends(get_current_user),
    db=Depends(get_db),
):
    """List active chat sessions for the current user."""
    sessions = await history_svc.list_sessions(db, current_user["user_id"], patient_id)
    return {"sessions": sessions, "count": len(sessions)}


@router.post("/sessions")
async def create_session(
    patient_id: str,
    current_user=Depends(require_permission(Permission.CHAT_QUERY.value)),
    db=Depends(get_db),
):
    """Explicitly create a new session for a patient (optional — /chat/ auto-creates)."""
    # Verify consent exists
    access = await consent_svc.check_access(
        requester_id=current_user["user_id"],
        requester_role=current_user["role"],
        patient_id=patient_id,
        db=db,
    )
    if not access.allowed:
        raise HTTPException(status_code=403, detail={"error": "CONSENT_DENIED", "reason": access.reason})

    session = await history_svc.create_session(
        db=db,
        user_id=current_user["user_id"],
        user_role=current_user["role"],
        patient_id=patient_id,
        consent_id=access.consent_id,
        consent_scope=access.scope,
    )
    return session


@router.get("/sessions/{session_id}")
async def get_session_history(
    session_id: str,
    current_user=Depends(get_current_user),
    db=Depends(get_db),
):
    """Get the full message history for a session."""
    session = await history_svc.get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session["user_id"] != current_user["user_id"]:
        raise HTTPException(status_code=403, detail="Access denied")

    messages = await history_svc.get_full_thread(db, session_id)
    return {"session": session, "messages": messages, "count": len(messages)}


@router.delete("/sessions/{session_id}")
async def close_session(
    session_id: str,
    current_user=Depends(get_current_user),
    db=Depends(get_db),
):
    """Archive/close a session (delete from user's view)."""
    closed = await history_svc.close_session(db, session_id, current_user["user_id"])
    if not closed:
        raise HTTPException(status_code=404, detail="Session not found or already closed")
    return {"status": "closed", "session_id": session_id}


# ── Cache Stats ────────────────────────────────────────────────────────────────

@router.get("/cache/stats")
async def cache_stats(
    current_user=Depends(require_permission(Permission.SYSTEM_MANAGE.value)),
    db=Depends(get_db),
):
    """Return cache health statistics."""
    stats = await cache_svc.stats(db)
    return stats
