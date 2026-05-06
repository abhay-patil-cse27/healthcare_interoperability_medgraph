import uuid
import structlog
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from app.models.medical import FHIRExchangeRequest, FHIRExchangeResponse
from app.dependencies import get_db, get_current_user, require_permission, get_mongo_client
from app.models.rbac import Permission
from app.services.consent_service import ConsentService
from app.services.neo4j_service import Neo4jService
from app.services.qdrant_service import QdrantService
from app.services.embedding_service import get_embedding_service
from app.services.groq_service import GroqService
from app.services.fhir_service import FHIRService
from app.services.audit_service import log_phi_access
from app.config import get_settings
from app.prompts.clinical_summary import (
    CLINICAL_SUMMARY_SYSTEM_PROMPT,
    build_fhir_summary_prompt,
)

logger = structlog.get_logger()
router = APIRouter()

consent_svc = ConsentService()
neo4j_svc = Neo4jService()
qdrant_svc = QdrantService()
groq_svc = GroqService()
fhir_svc = FHIRService()


async def _audit_fhir(action, patient_id, accessor_id, accessor_role, resource_type, request_id, metadata=None):
    settings = get_settings()
    db = get_mongo_client()[settings.mongodb_db]
    await log_phi_access(
        action=action, patient_id=patient_id, accessor_id=accessor_id,
        accessor_role=accessor_role, resource_type=resource_type,
        request_id=request_id, db=db, metadata=metadata or {},
    )


@router.post("/exchange", response_model=FHIRExchangeResponse)
async def fhir_exchange(
    request: FHIRExchangeRequest,
    background_tasks: BackgroundTasks,
    current_user=Depends(require_permission(Permission.FHIR_EXPORT.value)),
    db=Depends(get_db),
):

    # Validate consent
    access = await consent_svc.check_access(
        requester_id=current_user["user_id"],
        requester_role=current_user["role"],
        patient_id=request.patient_id,
        db=db,
    )
    if not access.allowed:
        raise HTTPException(
            status_code=403,
            detail={"error": "CONSENT_DENIED", "reason": access.reason},
        )

    request_id = str(uuid.uuid4())

    # Get patient graph summary
    graph_data = await neo4j_svc.get_patient_summary(request.patient_id)

    # Get vector context
    embedding_svc = get_embedding_service()
    query_embedding = await embedding_svc.embed(
        f"patient summary {request.patient_id}"
    )
    vector_results = await qdrant_svc.search(
        patient_id=request.patient_id,
        query_embedding=query_embedding,
        scope=access.scope or "full",
        filters=access.filters or {},
        top_k=5,
    )
    vector_context = "\n\n".join(r["content"] for r in vector_results)

    # Generate LLM clinical summary
    summary_prompt = build_fhir_summary_prompt(graph_data, vector_context)
    llm_result = await groq_svc.invoke(
        system_prompt=CLINICAL_SUMMARY_SYSTEM_PROMPT,
        user_message=summary_prompt,
        max_tokens=2048,
        temperature=0.0,
    )
    clinical_summary = llm_result["text"]

    # Build FHIR bundle
    bundle = fhir_svc.build_fhir_bundle(
        patient_id=request.patient_id,
        graph_data=graph_data,
        llm_summary=clinical_summary,
        consent_scope=access.scope or "full",
        request_id=request_id,
    )

    # Store bundle
    bundle_id = await fhir_svc.store_bundle(bundle, db)

    resource_count = len(bundle.get("entry", []))

    background_tasks.add_task(
        _audit_fhir,
        "FHIR_EXCHANGE", request.patient_id,
        current_user["user_id"], "doctor", "FHIRBundle", request_id,
        {"bundle_id": bundle_id, "resource_count": resource_count, "consent_scope": access.scope},
    )

    return FHIRExchangeResponse(
        bundle_id=bundle_id,
        fhir_bundle=bundle,
        clinical_summary=clinical_summary,
        resource_count=resource_count,
    )


@router.get("/bundle/{bundle_id}")
async def get_bundle(
    bundle_id: str,
    current_user=Depends(require_permission(Permission.FHIR_READ.value)),
    db=Depends(get_db),
):

    doc = await db["fhir_bundles"].find_one({"bundle_id": bundle_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Bundle not found")

    doc.pop("_id", None)
    return doc
