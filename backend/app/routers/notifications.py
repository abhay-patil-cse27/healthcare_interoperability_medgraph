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
    current_user = Depends(get_current_user)
):
    uid        = current_user["user_id"]
    role       = current_user["role"]

    # DynamoDB doesn't support $or — scan all and filter in-memory
    try:
        all_notifs = await db.notifications.find({}).to_list(200)
    except Exception:
        all_notifs = []

    # Filter: notifications for this user's role or directly for them
    results = []
    for doc in all_notifs:
        if doc.get("for_user_id") == uid or role in (doc.get("for_roles") or []):
            doc["is_read"] = uid in (doc.get("read_by") or [])
            if unread_only and doc["is_read"]:
                continue
            results.append(doc)

    # Sort by created_at descending
    results.sort(key=lambda x: x.get("created_at") or "", reverse=True)
    return results[:limit]

@router.post("/{notification_id}/read")
async def mark_read(
    notification_id: str,
    db = Depends(get_db),
    current_user = Depends(get_current_user)
):
    uid = current_user["user_id"]
    doc = await db.notifications.find_one({"notification_id": notification_id})
    if doc:
        read_by = doc.get("read_by") or []
        if uid not in read_by:
            read_by.append(uid)
            await db.notifications.update_one(
                {"notification_id": notification_id},
                {"$set": {"read_by": read_by}},
            )
    return {"status": "ok"}

@router.post("/mark-all-read")
async def mark_all_read(
    db = Depends(get_db),
    current_user = Depends(get_current_user)
):
    uid  = current_user["user_id"]
    role = current_user["role"]
    # DynamoDB doesn't have update_many — fetch and update individually
    try:
        results = await db.notifications.find({"for_roles": role}).to_list(200)
        for doc in results:
            read_by = doc.get("read_by") or []
            if uid not in read_by:
                read_by.append(uid)
                await db.notifications.update_one(
                    {"notification_id": doc["notification_id"]},
                    {"$set": {"read_by": read_by}},
                )
    except Exception:
        pass
    return {"status": "ok"}

@router.get("/count")
async def unread_count(
    db = Depends(get_db),
    current_user = Depends(get_current_user)
):
    uid  = current_user["user_id"]
    role = current_user["role"]
    try:
        all_notifs = await db.notifications.find({}).to_list(500)
    except Exception:
        return {"unread": 0}

    count = 0
    for doc in all_notifs:
        if doc.get("for_user_id") == uid or role in (doc.get("for_roles") or []):
            if uid not in (doc.get("read_by") or []):
                count += 1
    return {"unread": count}
