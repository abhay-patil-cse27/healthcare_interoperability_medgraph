from fastapi import APIRouter, Depends, Query
from typing import Optional
from app.models.rbac import Permission
from app.dependencies import get_db, require_any_permission, get_current_user
from datetime import datetime

router = APIRouter()

@router.get("/")
async def get_activity_logs(
    limit: int = Query(50),
    action: Optional[str] = Query(None),
    actor_role: Optional[str] = Query(None),
    db = Depends(get_db),
    current_user = Depends(require_any_permission([Permission.AUDIT_READ_HOSPITAL.value, Permission.AUDIT_READ_GLOBAL.value]))
):
    """Activity/audit logs scoped to hospital. Hospital Admins & Super Admins only."""
    query: dict = {}
    hospital_id = current_user.get("hospital_id")
    if hospital_id and current_user["role"] != "super_admin":
        query["hospital_id"] = hospital_id
    if action:
        query["action"] = action
    if actor_role:
        query["actor_role"] = actor_role

    cursor = db.activity_logs.find(query).sort("timestamp", -1).limit(limit)
    results = []
    async for doc in cursor:
        doc.pop("_id", None)
        results.append(doc)
    return results

@router.get("/my")
async def get_my_logs(
    limit: int = Query(30),
    db = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Personal activity log for any authenticated user."""
    cursor = db.activity_logs.find(
        {"actor_id": current_user["user_id"]}
    ).sort("timestamp", -1).limit(limit)
    results = []
    async for doc in cursor:
        doc.pop("_id", None)
        results.append(doc)
    return results
