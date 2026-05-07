import structlog
from datetime import datetime, timedelta
from typing import List
from boto3.dynamodb.conditions import Key, Attr

from app.models.consent import (
    ConsentRequest,
    ConsentRecord,
    ConsentGrant,
    ConsentCheckResult,
    ConsentScope,
    ConsentStatus,
)

logger = structlog.get_logger()


class ConsentService:
    async def create_request(self, request: ConsentRequest, db) -> ConsentRecord:
        record = ConsentRecord(
            doctor_id=request.doctor_id,
            patient_id=request.patient_id,
            purpose=request.purpose,
            requested_scope=request.requested_scope,
            disease_filter=request.disease_filter,
            date_range_start=request.date_range_start,
            date_range_end=request.date_range_end,
            duration_hours=request.duration_hours,
            status=ConsentStatus.PENDING,
        )
        item = record.model_dump()
        # Convert datetime objects to ISO strings for DynamoDB
        for k, v in item.items():
            if isinstance(v, datetime):
                item[k] = v.isoformat()
        await db.consents.insert_one(item)
        logger.info("consent_request_created", consent_id=record.consent_id)
        return record

    async def process_grant(self, grant: ConsentGrant, db) -> ConsentRecord:
        doc = await db.consents.find_one({"consent_id": grant.consent_id})
        if not doc:
            raise ValueError(f"Consent {grant.consent_id} not found")
        if doc["patient_id"] != grant.patient_id:
            raise ValueError("Patient ID mismatch")
        if doc["status"] != "pending":
            raise ValueError(f"Consent already {doc['status']}")

        new_status = ConsentStatus.APPROVED if grant.approved else ConsentStatus.DENIED
        valid_until = None
        if grant.approved:
            valid_until = (datetime.utcnow() + timedelta(hours=doc["duration_hours"])).isoformat()

        await db.consents.update_one(
            {"consent_id": grant.consent_id},
            {"$set": {
                "status": new_status.value,
                "valid_until": valid_until,
                "granted_at": datetime.utcnow().isoformat(),
            }},
        )

        doc.update({"status": new_status.value, "valid_until": valid_until})
        return ConsentRecord(**doc)

    async def check_access(
        self, requester_id: str, requester_role: str, patient_id: str, db
    ) -> ConsentCheckResult:
        # Patients always have full access to their own data
        if requester_role == "patient" and requester_id == patient_id:
            return ConsentCheckResult(
                allowed=True, reason="Self-access", scope="full", filters={}
            )

        # Query the doctor-patient-index GSI
        now = datetime.utcnow().isoformat()
        results = await db.consents.find(
            filter_dict={"status": "approved"},
            index_name="doctor-patient-index",
            key_condition=Key("doctor_id").eq(requester_id) & Key("patient_id").eq(patient_id),
        )

        # Filter for valid (non-expired) consents
        consent = None
        for r in results:
            if r.get("status") == "approved" and r.get("valid_until", "") > now:
                consent = r
                break

        if not consent:
            logger.warning("consent_check_no_active_found", doctor_id=requester_id, patient_id=patient_id)
            return ConsentCheckResult(
                allowed=False, reason="No active consent found"
            )

        scope = consent["requested_scope"]
        filters = {}
        if scope == ConsentScope.DISEASE_SPECIFIC.value:
            filters["diseases"] = consent.get("disease_filter", [])
        elif scope == ConsentScope.TIME_BOUND.value:
            filters["date_start"] = str(consent.get("date_range_start", ""))
            filters["date_end"] = str(
                consent.get("date_range_end", datetime.utcnow().isoformat())
            )

        return ConsentCheckResult(
            allowed=True,
            reason="Active consent found",
            scope=scope,
            filters=filters,
            consent_id=consent["consent_id"],
        )

    async def get_patient_consents(self, patient_id: str, db) -> List[ConsentRecord]:
        results = await db.consents.find(
            index_name="patient-index",
            key_condition=Key("patient_id").eq(patient_id),
        )
        records = []
        for doc in results:
            try:
                records.append(ConsentRecord(**doc))
            except Exception:
                pass
        return records

    async def revoke(self, consent_id: str, patient_id: str, db) -> bool:
        doc = await db.consents.find_one({"consent_id": consent_id})
        if not doc or doc.get("patient_id") != patient_id:
            return False
        await db.consents.update_one(
            {"consent_id": consent_id},
            {"$set": {"status": "revoked"}},
        )
        return True
