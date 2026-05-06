from fastapi import APIRouter, Depends
from typing import Dict
from app.models.privacy import DEFAULT_PRIVACY_POLICY_TEXT

router = APIRouter()

@router.get("/privacy-policy", response_model=Dict[str, str])
async def get_privacy_policy():
    """
    Returns the current HIPAA & DPDP compliant privacy policy of the platform.
    """
    return {
        "version": "1.0",
        "content": DEFAULT_PRIVACY_POLICY_TEXT,
        "effective_date": "2026-05-01T00:00:00Z"
    }

@router.get("/compliance", response_model=Dict[str, bool])
async def get_compliance_status():
    """
    Returns compliance flags for the platform.
    """
    return {
        "hipaa_compliant": True,
        "dpdp_compliant": True,
        "abdm_integrated": True,
        "fips_140_2_encryption": True
    }
