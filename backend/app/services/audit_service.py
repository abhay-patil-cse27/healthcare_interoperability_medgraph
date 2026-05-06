import uuid
import structlog
from datetime import datetime
from typing import Optional

logger = structlog.get_logger()

COLLECTION = "audit_logs"


async def log_phi_access(
    action: str,
    patient_id: str,
    accessor_id: str,
    accessor_role: str,
    resource_type: str,
    request_id: str,
    db,
    metadata: Optional[dict] = None,
) -> None:
    """
    Write a PHI access audit log entry to MongoDB.
    Patient ID is partially masked in logs (first 8 chars only).
    """
    event = {
        "event_id": str(uuid.uuid4()),
        "timestamp": datetime.utcnow().isoformat(),
        "action": action,
        "patient_id": patient_id,
        "accessor_id": accessor_id,
        "accessor_role": accessor_role,
        "resource_type": resource_type,
        "request_id": request_id,
        "metadata": metadata or {},
    }

    try:
        await db[COLLECTION].insert_one(event)
        logger.info(
            "phi_access_logged",
            action=action,
            patient_id_prefix=patient_id[:8] + "...",
            accessor_role=accessor_role,
            request_id=request_id,
        )
    except Exception as e:
        # Audit failures must not break the main flow
        logger.error("audit_log_failed", error=str(e), request_id=request_id)
