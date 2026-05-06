from fastapi import APIRouter, Depends, HTTPException
from typing import Optional
from app.models.rbac import Permission
from app.dependencies import get_db, require_permission
from datetime import datetime, timedelta

router = APIRouter()

@router.post("/records", status_code=201)
async def create_mlc_record(
    mlc: dict,
    db = Depends(get_db),
    current_user = Depends(require_permission(Permission.MLC_CREATE.value))
):
    """Doctor flags a Medico-Legal Case."""
    import uuid
    if "mlc_id" not in mlc:
        mlc["mlc_id"] = str(uuid.uuid4())
    mlc["doctor_id"]  = current_user["user_id"]
    mlc["hospital_id"] = current_user.get("hospital_id") or mlc.get("hospital_id")
    mlc["is_locked"]  = False
    mlc["created_at"] = datetime.utcnow()
    await db.mlc_records.insert_one(mlc)
    if mlc.get("admission_id"):
        await db.admissions.update_one(
            {"admission_id": mlc["admission_id"]},
            {"$set": {"is_mlc": True, "mlc_fir_number": mlc.get("fir_number")}}
        )
    mlc.pop("_id", None)
    return mlc

@router.get("/records")
async def list_mlc_records(
    db = Depends(get_db),
    current_user = Depends(require_permission(Permission.MLC_READ.value))
):
    """
    List all MLC records.
    - Police: all records (read-only, limited fields)
    - Doctor/Ward Incharge: hospital-scoped
    """
    query: dict = {}
    hospital_id = current_user.get("hospital_id")
    if hospital_id:
        query["hospital_id"] = hospital_id
    cursor = db.mlc_records.find(query).sort("created_at", -1).limit(100)
    results = []
    async for doc in cursor:
        doc.pop("_id", None)
        # Police sees limited fields
        if current_user["role"] == "police_interface":
            doc = {k: doc[k] for k in ["mlc_id","case_type","fir_number","police_station",
                                        "injury_description","is_locked","created_at"] if k in doc}
        results.append(doc)
    return results

@router.get("/records/{mlc_id}")
async def get_mlc_record(
    mlc_id: str,
    db = Depends(get_db),
    current_user = Depends(require_permission(Permission.MLC_READ.value))
):
    record = await db.mlc_records.find_one({"mlc_id": mlc_id})
    if not record:
        raise HTTPException(status_code=404, detail="MLC Record not found")
    time_since = datetime.utcnow() - record["created_at"]
    if not record.get("is_locked") and time_since > timedelta(hours=24):
        await db.mlc_records.update_one({"mlc_id": mlc_id}, {"$set": {"is_locked": True}})
        record["is_locked"] = True
    record.pop("_id", None)
    return record

@router.get("/stats")
async def mlc_stats(
    db = Depends(get_db),
    current_user = Depends(require_permission(Permission.MLC_READ.value))
):
    hospital_id = current_user.get("hospital_id")
    base = {"hospital_id": hospital_id} if hospital_id else {}
    total    = await db.mlc_records.count_documents(base)
    locked   = await db.mlc_records.count_documents({**base, "is_locked": True})
    with_fir = await db.mlc_records.count_documents({**base, "fir_number": {"$ne": None}})
    return {"total": total, "locked": locked, "with_fir": with_fir, "open": total - locked}
