"""
Chat History & Session Service — DynamoDB
==========================================
Provides persistent, role-aware conversation history stored in DynamoDB.

Tables:
  - medgraph-chat-sessions : one item per session (PK: session_id, GSI: user_id+updated_at)
  - medgraph-chat-messages : individual messages (PK: session_id, SK: timestamp#message_id)
"""
import uuid
import structlog
from datetime import datetime, timezone
from typing import List, Optional
from boto3.dynamodb.conditions import Key, Attr

logger = structlog.get_logger()

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
        now = datetime.now(timezone.utc).isoformat()
        session = {
            "session_id": str(uuid.uuid4()),
            "user_id": user_id,
            "user_role": user_role,
            "patient_id": patient_id,
            "consent_id": consent_id or "",
            "consent_scope": consent_scope or "",
            "created_at": now,
            "updated_at": now,
            "message_count": 0,
            "is_active": True,
        }
        await db.chat_sessions.insert_one(session)
        logger.info("chat_session_created", session_id=session["session_id"], user_id=user_id)
        return session

    async def get_session(self, db, session_id: str) -> Optional[dict]:
        doc = await db.chat_sessions.find_one({"session_id": session_id})
        if doc and doc.get("is_active"):
            return doc
        return None

    async def list_sessions(self, db, user_id: str, patient_id: Optional[str] = None) -> List[dict]:
        """List all active sessions for a user, optionally filtered by patient."""
        results = await db.chat_sessions.find(
            filter_dict={"is_active": True} if not patient_id else {"is_active": True, "patient_id": patient_id},
            index_name="user-index",
            key_condition=Key("user_id").eq(user_id),
            limit=50,
            scan_forward=False,  # Most recent first
        )
        return results

    async def close_session(self, db, session_id: str, user_id: str) -> bool:
        doc = await db.chat_sessions.find_one({"session_id": session_id})
        if not doc or doc.get("user_id") != user_id:
            return False
        await db.chat_sessions.update_one(
            {"session_id": session_id},
            {"$set": {
                "is_active": False,
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }},
        )
        return True

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
        now = datetime.now(timezone.utc).isoformat()
        message_id = str(uuid.uuid4())

        msg = {
            "session_id": session_id,
            "sort_key": f"{now}#{message_id}",
            "message_id": message_id,
            "role": role,
            "content": content,
            "metadata": metadata or {},
            "timestamp": now,
        }
        await db.chat_messages.insert_one(msg)

        # Update session
        await db.chat_sessions.update_one(
            {"session_id": session_id},
            {"$set": {"updated_at": now}, "$inc": {"message_count": 1}},
        )
        return msg

    async def get_history(self, db, session_id: str, limit: int = HISTORY_WINDOW * 2) -> List[dict]:
        """
        Return the last `limit` messages for a session in chronological order.
        """
        results = await db.chat_messages.find(
            key_condition=Key("session_id").eq(session_id),
            limit=limit,
            scan_forward=False,  # Get most recent first
        )
        # Reverse to chronological order
        results.reverse()
        return results

    def build_history_for_llm(self, messages: List[dict]) -> List[dict]:
        """
        Convert stored messages into the Bedrock messages format:
          [{"role": "user"|"assistant", "content": "..."}]
        """
        return [{"role": m["role"], "content": m["content"]} for m in messages]

    async def get_full_thread(self, db, session_id: str) -> List[dict]:
        """Return all messages for a session (for display in UI history view)."""
        return await db.chat_messages.find(
            key_condition=Key("session_id").eq(session_id),
            limit=500,
            scan_forward=True,
        )
