from fastapi import APIRouter, Depends, Query
from app.dependencies import get_db, get_current_user
import uuid
from datetime import datetime

router = APIRouter()

@router.get("/")
async def get_notifications(
    unread_only: bool = Query(False),
    limit: int = Query(30),
    db = Depends(get_db),
    current_user = Depends(get_current_user)          # any authenticated user
):
    uid        = current_user["user_id"]
    role       = current_user["role"]
    hospital_id = current_user.get("hospital_id")

    query: dict = {
        "$or": [
            {"for_user_id": uid},
            {"for_roles":   role},
        ]
    }
    if hospital_id:
        # also include hospital-wide notifs
        query["$or"].append({"hospital_id": hospital_id})
    if unread_only:
        query["read_by"] = {"$not": {"$elemMatch": {"$eq": uid}}}

    cursor = db.notifications.find(query).sort("created_at", -1).limit(limit)
    results = []
    async for doc in cursor:
        doc.pop("_id", None)
        doc["is_read"] = uid in (doc.get("read_by") or [])
        results.append(doc)
    return results

@router.post("/{notification_id}/read")
async def mark_read(
    notification_id: str,
    db = Depends(get_db),
    current_user = Depends(get_current_user)
):
    await db.notifications.update_one(
        {"notification_id": notification_id},
        {"$addToSet": {"read_by": current_user["user_id"]}}
    )
    return {"status": "ok"}

@router.post("/mark-all-read")
async def mark_all_read(
    db = Depends(get_db),
    current_user = Depends(get_current_user)
):
    uid  = current_user["user_id"]
    role = current_user["role"]
    await db.notifications.update_many(
        {"$or": [{"for_user_id": uid}, {"for_roles": role}]},
        {"$addToSet": {"read_by": uid}}
    )
    return {"status": "ok"}

@router.get("/count")
async def unread_count(
    db = Depends(get_db),
    current_user = Depends(get_current_user)
):
    uid  = current_user["user_id"]
    role = current_user["role"]
    query = {
        "$or": [{"for_user_id": uid}, {"for_roles": role}],
        "read_by": {"$not": {"$elemMatch": {"$eq": uid}}}
    }
    count = await db.notifications.count_documents(query)
    return {"unread": count}
