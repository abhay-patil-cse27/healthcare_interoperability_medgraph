import structlog
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from app.models.consent import ConsentRequest, ConsentGrant
from app.dependencies import get_db, get_current_user, require_permission, get_db_background
from app.models.rbac import Permission
from app.services.consent_service import ConsentService
from app.services.audit_service import log_phi_access
from app.config import get_settings

logger = structlog.get_logger()
router = APIRouter()
consent_svc = ConsentService()


async def _audit(action, patient_id, accessor_id, accessor_role, resource_type, request_id, metadata=None):
    db = get_db_background()
    await log_phi_access(
        action=action, patient_id=patient_id, accessor_id=accessor_id,
        accessor_role=accessor_role, resource_type=resource_type,
        request_id=request_id, db=db, metadata=metadata or {},
    )


@router.post("/request", status_code=201)
async def request_consent(
    request: ConsentRequest,
    background_tasks: BackgroundTasks,
    current_user=Depends(require_permission(Permission.CONSENT_REQUEST.value)),
    db=Depends(get_db),
):

    request.doctor_id = current_user["user_id"]
    record = await consent_svc.create_request(request, db)

    background_tasks.add_task(
        _audit, "CONSENT_REQUESTED", request.patient_id,
        current_user["user_id"], "doctor", "Consent", record.consent_id,
        {"scope": request.requested_scope, "purpose": request.purpose},
    )
    return record.model_dump()


@router.post("/grant")
async def grant_consent(
    grant: ConsentGrant,
    background_tasks: BackgroundTasks,
    current_user=Depends(require_permission(Permission.CONSENT_GRANT.value)),
    db=Depends(get_db),
):
    if current_user["user_id"] != grant.patient_id:
        raise HTTPException(status_code=403, detail="You can only manage your own consents")

    try:
        record = await consent_svc.process_grant(grant, db)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    action = "CONSENT_GRANTED" if grant.approved else "CONSENT_DENIED"
    background_tasks.add_task(
        _audit, action, grant.patient_id,
        current_user["user_id"], "patient", "Consent", grant.consent_id,
        {"approved": grant.approved},
    )
    return record.model_dump()


@router.get("/active/{patient_id}")
async def get_active_consents(
    patient_id: str,
    current_user=Depends(get_current_user),
    db=Depends(get_db),
):
    if Permission.CONSENT_VIEW_OWN.value in current_user.get("permissions", []):
        if current_user["user_id"] != patient_id:
            raise HTTPException(status_code=403, detail="Access denied")
        records = await consent_svc.get_patient_consents(patient_id, db)
    elif Permission.CONSENT_REQUEST.value in current_user.get("permissions", []):
        cursor = db["consents"].find(
            {"doctor_id": current_user["user_id"], "patient_id": patient_id}
        )
        records = []
        async for doc in cursor:
            doc.pop("_id", None)
            from app.models.consent import ConsentRecord
            records.append(ConsentRecord(**doc))

    return [r.model_dump() for r in records]


@router.delete("/{consent_id}")
async def revoke_consent(
    consent_id: str,
    background_tasks: BackgroundTasks,
    current_user=Depends(require_permission(Permission.CONSENT_GRANT.value)),
    db=Depends(get_db),
):

    revoked = await consent_svc.revoke(consent_id, current_user["user_id"], db)
    if not revoked:
        raise HTTPException(status_code=404, detail="Consent not found or already revoked")

    background_tasks.add_task(
        _audit, "CONSENT_REVOKED", current_user["user_id"],
        current_user["user_id"], "patient", "Consent", consent_id,
    )
    return {"status": "revoked", "consent_id": consent_id}
