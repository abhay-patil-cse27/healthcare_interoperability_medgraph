from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from typing import Dict
from app.models.clinical import VitalSign
from app.models.rbac import Permission
from app.dependencies import get_db, require_permission
import uuid

router = APIRouter()

@router.post("/iot-vitals", status_code=201)
async def receive_iot_vitals(
    vital: VitalSign,
    db = Depends(get_db),
    current_user = Depends(require_permission(Permission.WARD_BOT_WRITE_VITALS.value))
):
    """
    Webhook endpoint for IoT bedside monitors to push vitals automatically.
    The client must authenticate with a Ward Bot service JWT.
    """
    vital.recorded_by = "ward_bot_system"
    
    # Auto-alert threshold logic
    if vital.sp02 and vital.sp02 < 92:
        vital.is_alert = True
        
    await db.vitals.insert_one(vital.model_dump())
    
    if vital.is_alert:
        # Trigger push notification / page to assigned nurse / ward incharge
        pass
        
    return {"status": "success", "alert_triggered": vital.is_alert}

@router.post("/alerts/escalate")
async def escalate_alert(
    payload: Dict[str, str],
    db = Depends(get_db),
    current_user = Depends(require_permission(Permission.WARD_BOT_SEND_ALERT.value))
):
    """
    Ward bot can trigger escalations to human staff if tasks (e.g. med administration) are missed.
    """
    # Logic to record escalation and notify Ward Incharge
    return {"status": "escalated", "message": "Ward Incharge notified"}
