from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from typing import List, Dict
from app.models.clinical import Admission
from app.models.hospital import Bed
from app.models.rbac import Permission
from app.dependencies import get_db, require_permission
import uuid
from datetime import datetime

router = APIRouter()

@router.post("/admissions", response_model=Admission, status_code=201)
async def create_admission(
    admission: Admission,
    db = Depends(get_db),
    current_user = Depends(require_permission(Permission.ADMISSION_CREATE.value))
):
    """
    IPD Staff endpoint to admit a patient to a ward/bed.
    """
    if current_user.get("hospital_id"):
        admission.hospital_id = current_user["hospital_id"]

    # Verify bed availability
    bed = await db.beds.find_one({"bed_id": admission.bed_id})
    if not bed:
        raise HTTPException(status_code=404, detail="Bed not found")
    if bed.get("is_occupied", False):
        raise HTTPException(status_code=400, detail="Bed is currently occupied")

    # Mark bed as occupied
    await db.beds.update_one(
        {"bed_id": admission.bed_id},
        {"$set": {"is_occupied": True, "current_admission_id": admission.admission_id}}
    )

    await db.admissions.insert_one(admission.model_dump())
    
    # If MLC, trigger police notification stub
    if admission.is_mlc:
        # We would log this or trigger the MLC workflow
        pass
        
    return admission

@router.post("/admissions/{admission_id}/discharge")
async def discharge_patient(
    admission_id: str,
    db = Depends(get_db),
    current_user = Depends(require_permission(Permission.ADMISSION_DISCHARGE.value))
):
    """
    Process IPD discharge. Frees the bed and initiates insurance claims.
    """
    admission = await db.admissions.find_one({"admission_id": admission_id})
    if not admission:
        raise HTTPException(status_code=404, detail="Admission not found")
    if admission["status"] != "admitted":
        raise HTTPException(status_code=400, detail="Patient already discharged or transferred")

    # Free the bed
    await db.beds.update_one(
        {"bed_id": admission["bed_id"]},
        {"$set": {"is_occupied": False, "current_admission_id": None}}
    )

    # Update admission record
    await db.admissions.update_one(
        {"admission_id": admission_id},
        {"$set": {"status": "discharged", "discharge_time": datetime.utcnow()}}
    )
    
    # Here we would trigger the Insurance Claims Workflow asynchronously...
    
    return {"status": "success", "message": "Patient discharged successfully"}

@router.get("/wards/{ward_id}/beds", response_model=List[Bed])
async def list_ward_beds(
    ward_id: str,
    db = Depends(get_db),
    current_user = Depends(require_permission(Permission.BED_MANAGE.value))
):
    cursor = db.beds.find({"ward_id": ward_id})
    return [Bed(**doc) async for doc in cursor]
