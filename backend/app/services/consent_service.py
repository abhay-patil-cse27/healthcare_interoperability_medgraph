import structlog
from datetime import datetime, timedelta
from typing import List
from app.models.consent import (
    ConsentRequest,
    ConsentRecord,
    ConsentGrant,
    ConsentCheckResult,
    ConsentScope,
    ConsentStatus,
)

logger = structlog.get_logger()

COLLECTION = "consents"


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
        await db[COLLECTION].insert_one(record.model_dump())
        logger.info("consent_request_created", consent_id=record.consent_id)
        return record

    async def process_grant(self, grant: ConsentGrant, db) -> ConsentRecord:
        doc = await db[COLLECTION].find_one({"consent_id": grant.consent_id})
        if not doc:
            raise ValueError(f"Consent {grant.consent_id} not found")
        if doc["patient_id"] != grant.patient_id:
            raise ValueError("Patient ID mismatch")
        if doc["status"] != "pending":
            raise ValueError(f"Consent already {doc['status']}")

        new_status = ConsentStatus.APPROVED if grant.approved else ConsentStatus.DENIED
        valid_until = None
        if grant.approved:
            valid_until = datetime.utcnow() + timedelta(hours=doc["duration_hours"])

        await db[COLLECTION].update_one(
            {"consent_id": grant.consent_id},
            {
                "$set": {
                    "status": new_status.value,
                    "valid_until": valid_until,
                    "granted_at": datetime.utcnow(),
                }
            },
        )

        doc.update({"status": new_status.value, "valid_until": valid_until})
        doc.pop("_id", None)
        return ConsentRecord(**doc)

    async def check_access(
        self, requester_id: str, requester_role: str, patient_id: str, db
    ) -> ConsentCheckResult:
        # Patients always have full access to their own data
        if requester_role == "patient" and requester_id == patient_id:
            return ConsentCheckResult(
                allowed=True, reason="Self-access", scope="full", filters={}
            )

        query = {
            "doctor_id": requester_id,
            "patient_id": patient_id,
            "status": "approved",
            "valid_until": {"$gt": datetime.utcnow()},
        }
        logger.info("consent_check_query", query_params={
            "doctor_id": requester_id,
            "patient_id": patient_id,
        })
        consent = await db[COLLECTION].find_one(query)

        if not consent:
            # Debug: find any consent between this doctor and patient regardless of status/expiry
            debug = await db[COLLECTION].find_one({
                "doctor_id": requester_id,
                "patient_id": patient_id,
            })
            if debug:
                debug.pop("_id", None)
                logger.warning("consent_check_failed_debug", found_consent={
                    "status": debug.get("status"),
                    "valid_until": str(debug.get("valid_until")),
                    "doctor_id": debug.get("doctor_id"),
                    "patient_id": debug.get("patient_id"),
                })
            else:
                logger.warning("consent_check_no_record_found", doctor_id=requester_id, patient_id=patient_id)
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
        cursor = db[COLLECTION].find({"patient_id": patient_id})
        records = []
        async for doc in cursor:
            doc.pop("_id", None)
            records.append(ConsentRecord(**doc))
        return records

    async def revoke(self, consent_id: str, patient_id: str, db) -> bool:
        result = await db[COLLECTION].update_one(
            {"consent_id": consent_id, "patient_id": patient_id},
            {"$set": {"status": "revoked"}},
        )
        return result.modified_count > 0
