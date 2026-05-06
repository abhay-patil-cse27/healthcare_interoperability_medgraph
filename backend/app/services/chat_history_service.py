"""
Chat History & Session Service
===============================
Provides persistent, role-aware conversation history stored in MongoDB.

Collections:
  - chat_sessions   : one doc per session (created when a user opens a chat window)
  - chat_messages   : individual messages, indexed by session_id

Design:
  - Each session is scoped to (user_id, patient_id)
  - History is windowed to the last N turns to keep LLM context lean
  - Sessions auto-expire via MongoDB TTL index (set in init_mongo.py)
"""
import uuid
import structlog
from datetime import datetime, timezone
from typing import List, Optional

logger = structlog.get_logger()

SESSIONS_COL = "chat_sessions"
MESSAGES_COL  = "chat_messages"

# How many past turns (user+assistant pairs) to include in LLM context
HISTORY_WINDOW = 6


class ChatHistoryService:

    # ── Session Management ────────────────────────────────────────────────

    async def create_session(
        self,
        db,
        user_id: str,
        user_role: str,
        patient_id: str,
        consent_id: Optional[str] = None,
        consent_scope: Optional[str] = None,
    ) -> dict:
        """Create a new chat session and return the session document."""
        session = {
            "session_id": str(uuid.uuid4()),
            "user_id": user_id,
            "user_role": user_role,
            "patient_id": patient_id,
            "consent_id": consent_id,
            "consent_scope": consent_scope,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
            "message_count": 0,
            "is_active": True,
        }
        await db[SESSIONS_COL].insert_one(session)
        session.pop("_id", None)
        logger.info("chat_session_created", session_id=session["session_id"], user_id=user_id)
        return session

    async def get_session(self, db, session_id: str) -> Optional[dict]:
        doc = await db[SESSIONS_COL].find_one({"session_id": session_id, "is_active": True})
        if doc:
            doc.pop("_id", None)
        return doc

    async def list_sessions(self, db, user_id: str, patient_id: Optional[str] = None) -> List[dict]:
        """List all active sessions for a user, optionally filtered by patient."""
        query: dict = {"user_id": user_id, "is_active": True}
        if patient_id:
            query["patient_id"] = patient_id
        cursor = db[SESSIONS_COL].find(query).sort("updated_at", -1).limit(50)
        sessions = []
        async for doc in cursor:
            doc.pop("_id", None)
            sessions.append(doc)
        return sessions

    async def close_session(self, db, session_id: str, user_id: str) -> bool:
        result = await db[SESSIONS_COL].update_one(
            {"session_id": session_id, "user_id": user_id},
            {"$set": {"is_active": False, "updated_at": datetime.now(timezone.utc)}},
        )
        return result.modified_count > 0

    # ── Message Management ────────────────────────────────────────────────

    async def append_message(
        self,
        db,
        session_id: str,
        role: str,          # "user" | "assistant"
        content: str,
        metadata: Optional[dict] = None,
    ) -> dict:
        """Append a single message to a session's history."""
        msg = {
            "message_id": str(uuid.uuid4()),
            "session_id": session_id,
            "role": role,
            "content": content,
            "metadata": metadata or {},
            "timestamp": datetime.now(timezone.utc),
        }
        await db[MESSAGES_COL].insert_one(msg)
        # Keep session updated_at fresh
        await db[SESSIONS_COL].update_one(
            {"session_id": session_id},
            {
                "$set": {"updated_at": datetime.now(timezone.utc)},
                "$inc": {"message_count": 1},
            },
        )
        msg.pop("_id", None)
        return msg

    async def get_history(self, db, session_id: str, limit: int = HISTORY_WINDOW * 2) -> List[dict]:
        """
        Return the last `limit` messages for a session (already in chronological order).
        Default limit = HISTORY_WINDOW * 2 because each turn = 1 user + 1 assistant message.
        """
        cursor = (
            db[MESSAGES_COL]
            .find({"session_id": session_id}, {"_id": 0})
            .sort("timestamp", -1)
            .limit(limit)
        )
        messages = []
        async for doc in cursor:
            messages.append(doc)
        # Reverse to get chronological order (oldest first)
        messages.reverse()
        return messages

    def build_history_for_llm(self, messages: List[dict]) -> List[dict]:
        """
        Convert stored messages into the OpenAI/Groq messages format:
          [{"role": "user"|"assistant", "content": "..."}]
        """
        return [{"role": m["role"], "content": m["content"]} for m in messages]

    async def get_full_thread(self, db, session_id: str) -> List[dict]:
        """Return all messages for a session (for display in UI history view)."""
        cursor = (
            db[MESSAGES_COL]
            .find({"session_id": session_id}, {"_id": 0})
            .sort("timestamp", 1)
        )
        return [doc async for doc in cursor]
