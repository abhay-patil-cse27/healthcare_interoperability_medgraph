"""
Response Cache Service
========================
In-memory LRU cache with TTL for LLM responses. Avoids redundant LLM calls
for identical (patient_id, query) pairs within a time window.

Architecture:
  - L1: In-process TTLCache (cachetools) — zero-latency, per-worker
  - L2: MongoDB persistent cache — survives restarts, shared across workers

In production with multiple workers, replace L1 with a Redis client.
The interface is intentionally Redis-compatible so you can swap the backend
by changing only this file.

Cache key: SHA-256( patient_id + "::" + normalized_query )
TTL: configurable, default 10 minutes
"""
import hashlib
import time
import structlog
from typing import Optional
from datetime import datetime, timezone
try:
    from cachetools import TTLCache
    _HAS_CACHETOOLS = True
except ImportError:
    _HAS_CACHETOOLS = False

logger = structlog.get_logger()

# L1 — in-process cache: max 512 entries, 10-minute TTL
_L1_TTL_SECONDS = 600
_L1: "TTLCache | dict" = TTLCache(maxsize=512, ttl=_L1_TTL_SECONDS) if _HAS_CACHETOOLS else {}

CACHE_COL = "response_cache"


def _make_key(patient_id: str, query: str) -> str:
    """Produce a stable, short cache key from patient + query."""
    normalized = f"{patient_id}::{query.strip().lower()}"
    return hashlib.sha256(normalized.encode()).hexdigest()


class ResponseCacheService:

    # ── L1: In-Process TTL Cache ──────────────────────────────────────────

    def get_l1(self, patient_id: str, query: str) -> Optional[dict]:
        key = _make_key(patient_id, query)
        hit = _L1.get(key)
        if hit:
            logger.info("cache_l1_hit", key=key[:12])
        return hit

    def set_l1(self, patient_id: str, query: str, response: dict) -> None:
        key = _make_key(patient_id, query)
        _L1[key] = response

    def invalidate_patient(self, patient_id: str) -> None:
        """Evict all L1 entries for a patient (e.g., after a new memory ingest)."""
        keys_to_del = [k for k in list(_L1.keys()) if patient_id in k]
        for k in keys_to_del:
            _L1.pop(k, None)
        logger.info("cache_invalidated_patient", patient_id=patient_id, evicted=len(keys_to_del))

    # ── L2: MongoDB Persistent Cache ──────────────────────────────────────

    async def get_l2(self, db, patient_id: str, query: str) -> Optional[dict]:
        key = _make_key(patient_id, query)
        doc = await db[CACHE_COL].find_one({"_id": key})
        if not doc:
            return None
        # Honour TTL manually (MongoDB TTL indexes fire every 60s, so we double-check)
        age_s = time.time() - doc["cached_at_ts"]
        if age_s > _L1_TTL_SECONDS:
            await db[CACHE_COL].delete_one({"_id": key})
            return None
        logger.info("cache_l2_hit", key=key[:12], age_s=int(age_s))
        return doc["payload"]

    async def set_l2(self, db, patient_id: str, query: str, response: dict) -> None:
        key = _make_key(patient_id, query)
        now = time.time()
        await db[CACHE_COL].replace_one(
            {"_id": key},
            {
                "_id": key,
                "patient_id": patient_id,
                "cached_at_ts": now,
                "cached_at": datetime.now(timezone.utc),
                "payload": response,
            },
            upsert=True,
        )

    # ── Unified Get (L1 → L2) ─────────────────────────────────────────────

    async def get(self, db, patient_id: str, query: str) -> Optional[dict]:
        hit = self.get_l1(patient_id, query)
        if hit:
            return hit
        hit = await self.get_l2(db, patient_id, query)
        if hit:
            # Promote to L1
            self.set_l1(patient_id, query, hit)
        return hit

    async def set(self, db, patient_id: str, query: str, response: dict) -> None:
        self.set_l1(patient_id, query, response)
        await self.set_l2(db, patient_id, query, response)

    # ── Cache Stats ───────────────────────────────────────────────────────

    async def stats(self, db) -> dict:
        total = await db[CACHE_COL].count_documents({})
        return {
            "l1_entries": len(_L1),
            "l1_maxsize": getattr(_L1, "maxsize", "N/A"),
            "l2_entries": total,
            "ttl_seconds": _L1_TTL_SECONDS,
        }
