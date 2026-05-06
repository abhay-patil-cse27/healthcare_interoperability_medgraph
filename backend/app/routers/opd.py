from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional
from app.models.rbac import Permission
from app.dependencies import get_db, require_permission
import uuid
from datetime import datetime

router = APIRouter()

@router.post("/appointments", status_code=201)
async def book_appointment(
    appt: dict,
    db = Depends(get_db),
    current_user = Depends(require_permission(Permission.APPOINTMENT_CREATE.value))
):
    """OPD Staff / Receptionist — book a new appointment."""
    if "appointment_id" not in appt:
        appt["appointment_id"] = str(uuid.uuid4())
    if current_user.get("hospital_id"):
        appt["hospital_id"] = current_user["hospital_id"]
    appt.setdefault("status", "scheduled")
    appt["created_at"] = datetime.utcnow()
    if "scheduled_time" in appt and isinstance(appt["scheduled_time"], str):
        appt["scheduled_time"] = datetime.fromisoformat(appt["scheduled_time"])
    await db.appointments.insert_one(appt)
    appt.pop("_id", None)
    return appt

@router.get("/appointments")
async def list_appointments(
    status: Optional[str] = Query(None),
    db = Depends(get_db),
    current_user = Depends(require_permission(Permission.APPOINTMENT_READ.value))
):
    """All appointments for the hospital, optionally filtered by status."""
    query: dict = {}
    hospital_id = current_user.get("hospital_id")
    if hospital_id:
        query["hospital_id"] = hospital_id
    if status:
        query["status"] = status
    cursor = db.appointments.find(query).sort("scheduled_time", -1).limit(200)
    results = []
    async for doc in cursor:
        doc.pop("_id", None)
        results.append(doc)
    return results

@router.get("/appointments/queue")
async def get_opd_queue(
    department_id: Optional[str] = Query(None),
    db = Depends(get_db),
    current_user = Depends(require_permission(Permission.APPOINTMENT_READ.value))
):
    """Today's OPD queue — optionally filtered by department."""
    query: dict = {}
    hospital_id = current_user.get("hospital_id")
    if hospital_id:
        query["hospital_id"] = hospital_id
    if department_id:
        query["department_id"] = department_id
    cursor = db.appointments.find(query).sort("scheduled_time", 1).limit(200)
    results = []
    async for doc in cursor:
        doc.pop("_id", None)
        results.append(doc)
    return results

@router.patch("/appointments/{appointment_id}/status")
async def update_appointment_status(
    appointment_id: str,
    status: str,
    db = Depends(get_db),
    current_user = Depends(require_permission(Permission.APPOINTMENT_CREATE.value))
):
    result = await db.appointments.update_one(
        {"appointment_id": appointment_id},
        {"$set": {"status": status, "updated_at": datetime.utcnow()}}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Appointment not found")
    return {"status": "success", "new_status": status}

@router.get("/stats")
async def opd_stats(
    db = Depends(get_db),
    current_user = Depends(require_permission(Permission.APPOINTMENT_READ.value))
):
    hospital_id = current_user.get("hospital_id")
    base = {"hospital_id": hospital_id} if hospital_id else {}
    scheduled  = await db.appointments.count_documents({**base, "status": "scheduled"})
    completed  = await db.appointments.count_documents({**base, "status": "completed"})
    cancelled  = await db.appointments.count_documents({**base, "status": "cancelled"})
    no_show    = await db.appointments.count_documents({**base, "status": "no_show"})
    return {"scheduled": scheduled, "completed": completed, "cancelled": cancelled, "no_show": no_show,
            "total": scheduled + completed + cancelled + no_show}
