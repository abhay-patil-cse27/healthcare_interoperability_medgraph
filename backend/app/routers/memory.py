import time
import uuid
import structlog
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from app.models.medical import MemoryIngestRequest, MemoryIngestResponse
from app.dependencies import get_db, get_current_user, require_permission, get_db_background
from app.models.rbac import Permission
from app.pipelines.ingestion_pipeline import IngestionPipeline
from app.services.audit_service import log_phi_access
from app.config import get_settings

logger = structlog.get_logger()
router = APIRouter()

_pipeline: IngestionPipeline = None


def get_pipeline() -> IngestionPipeline:
    global _pipeline
    if _pipeline is None:
        _pipeline = IngestionPipeline()
    return _pipeline


async def _audit_ingest(action, patient_id, accessor_id, accessor_role, resource_type, request_id, metadata):
    """Background-safe audit writer — creates its own DB connection."""
    db = get_db_background()
    await log_phi_access(
        action=action,
        patient_id=patient_id,
        accessor_id=accessor_id,
        accessor_role=accessor_role,
        resource_type=resource_type,
        request_id=request_id,
        db=db,
        metadata=metadata,
    )


@router.post("/ingest", response_model=MemoryIngestResponse, status_code=201)
async def ingest_memory(
    request: MemoryIngestRequest,
    background_tasks: BackgroundTasks,
    current_user=Depends(require_permission(Permission.MEMORY_INGEST.value)),
    db=Depends(get_db),
):
    if current_user["role"] == "patient" and current_user["user_id"] != request.patient_id:
        raise HTTPException(
            status_code=403, detail="Patients can only ingest their own data"
        )

    request_id = str(uuid.uuid4())
    start_ms = int(time.time() * 1000)

    pipeline = get_pipeline()
    result = await pipeline.run(
        patient_id=request.patient_id,
        text=request.text,
        source=request.source,
        encounter_date=request.encounter_date,
        request_id=request_id,
    )

    processing_time_ms = int(time.time() * 1000) - start_ms

    background_tasks.add_task(
        _audit_ingest,
        action="INGEST",
        patient_id=request.patient_id,
        accessor_id=current_user["user_id"],
        accessor_role=current_user["role"],
        resource_type="HealthText",
        request_id=request_id,
        metadata={"source": request.source, "status": result["status"]},
    )

    return MemoryIngestResponse(
        request_id=request_id,
        status=result["status"],
        entities=result["entities"],
        graph_nodes_created=result["graph_nodes_created"],
        vector_entry_id=result["vector_entry_id"],
        processing_time_ms=processing_time_ms,
    )


@router.get("/history/{patient_id}")
async def get_history(
    patient_id: str,
    current_user=Depends(get_current_user),
    db=Depends(get_db),
):
    if current_user["role"] == "patient" and current_user["user_id"] != patient_id:
        raise HTTPException(status_code=403, detail="Access denied")

    cursor = (
        db.audit_logs.find({"patient_id": patient_id})
        .sort("timestamp", -1)
        .limit(20)
    )
    history = []
    async for doc in cursor:
        doc.pop("_id", None)
        history.append(doc)
    return {"patient_id": patient_id, "history": history}
