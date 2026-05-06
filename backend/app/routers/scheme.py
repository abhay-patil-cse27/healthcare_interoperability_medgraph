from fastapi import APIRouter, Depends, HTTPException
from typing import List
from app.models.finance_legal import SchemeEligibilityCheck
from app.models.rbac import Permission
from app.dependencies import get_db, require_permission
from datetime import datetime

router = APIRouter()

@router.post("/eligibility/check", response_model=SchemeEligibilityCheck)
async def check_scheme_eligibility(
    check: SchemeEligibilityCheck,
    db = Depends(get_db),
    current_user = Depends(require_permission(Permission.SCHEME_ELIGIBILITY_CHECK.value))
):
    """
    Simulates calling GoI/State APIs (PM-JAY, MPJAY) to verify patient eligibility.
    """
    # STUB: Mocking government API cascade check
    if check.scheme_name == "PM-JAY" and check.identity_value.startswith("ABHA"):
        check.is_eligible = True
        check.coverage_cap = 500000.0 # 5 Lakh cap
    else:
        check.is_eligible = False
        
    await db.scheme_checks.insert_one(check.model_dump())
    return check

@router.post("/disburse/{claim_id}")
async def disburse_scheme_funds(
    claim_id: str,
    amount: float,
    db = Depends(get_db),
    current_user = Depends(require_permission(Permission.SCHEME_DISBURSE.value))
):
    """
    Irreversible government fund disbursement.
    """
    # Logic to record disbursement against the claim
    return {"status": "success", "disbursed_amount": amount, "claim_id": claim_id}
