import uuid
import structlog
from datetime import datetime
from typing import Optional

logger = structlog.get_logger()


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
    Write a PHI access audit log entry to DynamoDB.
    Table: medgraph-audit-logs
    PK: patient_id, SK: timestamp#event_id
    """
    timestamp = datetime.utcnow().isoformat()
    event_id = str(uuid.uuid4())

    event = {
        "patient_id": patient_id,
        "sort_key": f"{timestamp}#{event_id}",
        "event_id": event_id,
        "timestamp": timestamp,
        "action": action,
        "accessor_id": accessor_id,
        "accessor_role": accessor_role,
        "resource_type": resource_type,
        "request_id": request_id,
        "metadata": metadata or {},
    }

    try:
        await db.audit_logs.insert_one(event)
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
