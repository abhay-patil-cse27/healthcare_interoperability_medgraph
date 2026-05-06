from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional, Any
from app.models.rbac import Permission
from app.dependencies import get_db, require_permission
from datetime import datetime

router = APIRouter()

@router.post("/", status_code=201)
async def create_prescription(
    prescription: dict,
    db = Depends(get_db),
    current_user = Depends(require_permission(Permission.PRESCRIPTION_WRITE.value))
):
    """Doctor/Surgeon writes a prescription."""
    prescription["doctor_id"]  = current_user["user_id"]
    prescription["hospital_id"] = current_user.get("hospital_id")
    prescription["status"]      = prescription.get("status", "pending")
    prescription["created_at"]  = datetime.utcnow()
    if "prescription_id" not in prescription:
        import uuid
        prescription["prescription_id"] = str(uuid.uuid4())
    await db.prescriptions.insert_one(prescription)
    prescription.pop("_id", None)
    return prescription

@router.get("/patient/{patient_id}")
async def get_patient_prescriptions(
    patient_id: str,
    db = Depends(get_db),
    current_user = Depends(require_permission(Permission.PRESCRIPTION_READ.value))
):
    """Read active prescriptions for a patient."""
    cursor = db.prescriptions.find({"patient_id": patient_id}).sort("created_at", -1)
    results = []
    async for doc in cursor:
        doc.pop("_id", None)
        results.append(doc)
    return results

@router.get("/queue")
async def get_pharmacy_queue(
    status: str = "pending",
    db = Depends(get_db),
    current_user = Depends(require_permission(Permission.PRESCRIPTION_READ.value))
):
    """Pharmacist — fetch all prescriptions by status, scoped to hospital."""
    query: dict = {"status": status}
    hospital_id = current_user.get("hospital_id")
    if hospital_id:
        query["hospital_id"] = hospital_id
    cursor = db.prescriptions.find(query).sort("created_at", -1).limit(100)
    results = []
    async for doc in cursor:
        doc.pop("_id", None)
        results.append(doc)
    return results

@router.get("/stats")
async def pharmacy_stats(
    db = Depends(get_db),
    current_user = Depends(require_permission(Permission.PRESCRIPTION_READ.value))
):
    """Stats for pharmacist dashboard."""
    hospital_id = current_user.get("hospital_id")
    base_query  = {"hospital_id": hospital_id} if hospital_id else {}
    pending   = await db.prescriptions.count_documents({**base_query, "status": "pending"})
    dispensed = await db.prescriptions.count_documents({**base_query, "status": "dispensed"})
    return {"pending": pending, "dispensed": dispensed, "total": pending + dispensed}

@router.post("/{prescription_id}/dispense")
async def dispense_prescription(
    prescription_id: str,
    db = Depends(get_db),
    current_user = Depends(require_permission(Permission.PRESCRIPTION_DISPENSE.value))
):
    """Pharmacist marks a prescription as dispensed."""
    result = await db.prescriptions.update_one(
        {"prescription_id": prescription_id},
        {"$set": {"status": "dispensed", "dispensed_at": datetime.utcnow(),
                  "dispensed_by": current_user["user_id"]}}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Prescription not found or already dispensed")
    return {"status": "success", "message": "Prescription dispensed"}
