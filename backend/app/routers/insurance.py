from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional
from app.models.rbac import Permission
from app.dependencies import get_db, require_permission
from datetime import datetime

router = APIRouter()

@router.post("/claims", status_code=201)
async def create_claim(
    claim: dict,
    db = Depends(get_db),
    current_user = Depends(require_permission(Permission.INSURANCE_CLAIM_CREATE.value))
):
    """Insurance officer initiates a claim."""
    import uuid
    if "claim_id" not in claim:
        claim["claim_id"] = str(uuid.uuid4())
    claim["submitted_at"] = datetime.utcnow()
    if current_user.get("hospital_id") and "hospital_id" not in claim:
        claim["hospital_id"] = current_user["hospital_id"]
    await db.insurance_claims.insert_one(claim)
    claim.pop("_id", None)
    return claim

@router.get("/claims")
async def list_claims(
    status: Optional[str] = Query(None),
    db = Depends(get_db),
    current_user = Depends(require_permission(Permission.INSURANCE_CLAIM_READ.value))
):
    """List insurance claims — scoped to hospital for insurance_officer."""
    query: dict = {}
    hospital_id = current_user.get("hospital_id")
    if hospital_id:
        query["hospital_id"] = hospital_id
    if status:
        query["status"] = status
    cursor = db.insurance_claims.find(query).sort("submitted_at", -1).limit(200)
    results = []
    async for doc in cursor:
        doc.pop("_id", None)
        results.append(doc)
    return results

@router.get("/claims/stats")
async def claim_stats(
    db = Depends(get_db),
    current_user = Depends(require_permission(Permission.INSURANCE_CLAIM_READ.value))
):
    """Stats for insurance dashboard."""
    hospital_id = current_user.get("hospital_id")
    base = {"hospital_id": hospital_id} if hospital_id else {}
    initiated   = await db.insurance_claims.count_documents({**base, "status": "initiated"})
    pre_auth    = await db.insurance_claims.count_documents({**base, "status": "pre_auth_pending"})
    approved    = await db.insurance_claims.count_documents({**base, "status": "approved"})
    rejected    = await db.insurance_claims.count_documents({**base, "status": "rejected"})
    settled     = await db.insurance_claims.count_documents({**base, "status": "settled"})
    # total approved_amount
    pipeline = [
        {"$match": {**base, "status": "settled"}},
        {"$group": {"_id": None, "total": {"$sum": "$approved_amount"}}}
    ]
    agg = await db.insurance_claims.aggregate(pipeline).to_list(1)
    total_settled_amount = agg[0]["total"] if agg else 0
    return {
        "initiated": initiated, "pre_auth_pending": pre_auth,
        "approved": approved, "rejected": rejected, "settled": settled,
        "total_settled_amount": total_settled_amount,
    }

@router.patch("/claims/{claim_id}/status")
async def update_claim_status(
    claim_id: str,
    status: str,
    db = Depends(get_db),
    current_user = Depends(require_permission(Permission.INSURANCE_PREAUTH.value))
):
    update_data = {"status": status}
    if status == "settled":
        update_data["settled_at"] = datetime.utcnow()
    result = await db.insurance_claims.update_one(
        {"claim_id": claim_id}, {"$set": update_data}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Claim not found")
    return {"status": "success", "new_status": status}
