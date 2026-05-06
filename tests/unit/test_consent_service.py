"""
Unit tests for ConsentService.
Run: venv/Scripts/python.exe -m pytest tests/unit/test_consent_service.py -v
"""
import sys
import os
import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "backend"))

from app.services.consent_service import ConsentService
from app.models.consent import (
    ConsentRequest, ConsentGrant, ConsentScope, ConsentStatus, ConsentRecord
)


def make_db(find_one_result=None):
    """Create a mock MongoDB database."""
    collection = MagicMock()
    collection.find_one = AsyncMock(return_value=find_one_result)
    collection.insert_one = AsyncMock(return_value=MagicMock())
    collection.update_one = AsyncMock(return_value=MagicMock(modified_count=1))

    db = MagicMock()
    db.__getitem__ = MagicMock(return_value=collection)
    return db, collection


def make_consent_doc(
    consent_id="test-consent-id",
    doctor_id="doctor-123",
    patient_id="patient-456",
    status="pending",
    scope="full",
    duration_hours=24,
    valid_until=None,
):
    return {
        "consent_id": consent_id,
        "doctor_id": doctor_id,
        "patient_id": patient_id,
        "purpose": "Annual review",
        "requested_scope": scope,
        "disease_filter": None,
        "date_range_start": None,
        "date_range_end": None,
        "duration_hours": duration_hours,
        "status": status,
        "created_at": datetime.utcnow(),
        "valid_until": valid_until,
        "granted_at": None,
    }


class TestConsentService:
    def setup_method(self):
        self.svc = ConsentService()

    # ── check_access ──────────────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_patient_self_access_always_allowed(self):
        db, _ = make_db()
        result = await self.svc.check_access("patient-456", "patient", "patient-456", db)
        assert result.allowed is True
        assert result.scope == "full"
        assert result.reason == "Self-access"

    @pytest.mark.asyncio
    async def test_patient_cannot_access_other_patient(self):
        db, col = make_db(find_one_result=None)
        result = await self.svc.check_access("patient-456", "patient", "patient-999", db)
        assert result.allowed is False

    @pytest.mark.asyncio
    async def test_doctor_no_consent_denied(self):
        db, col = make_db(find_one_result=None)
        result = await self.svc.check_access("doctor-123", "doctor", "patient-456", db)
        assert result.allowed is False
        assert "No active consent" in result.reason

    @pytest.mark.asyncio
    async def test_doctor_valid_full_consent_allowed(self):
        valid_until = datetime.utcnow() + timedelta(hours=24)
        doc = make_consent_doc(status="approved", scope="full", valid_until=valid_until)
        db, _ = make_db(find_one_result=doc)
        result = await self.svc.check_access("doctor-123", "doctor", "patient-456", db)
        assert result.allowed is True
        assert result.scope == "full"
        assert result.consent_id == "test-consent-id"

    @pytest.mark.asyncio
    async def test_doctor_disease_specific_consent_returns_filters(self):
        valid_until = datetime.utcnow() + timedelta(hours=24)
        doc = make_consent_doc(status="approved", scope="disease_specific", valid_until=valid_until)
        doc["disease_filter"] = ["diabetes", "hypertension"]
        db, _ = make_db(find_one_result=doc)
        result = await self.svc.check_access("doctor-123", "doctor", "patient-456", db)
        assert result.allowed is True
        assert result.scope == "disease_specific"
        assert "diseases" in result.filters
        assert "diabetes" in result.filters["diseases"]

    @pytest.mark.asyncio
    async def test_doctor_time_bound_consent_returns_date_filters(self):
        valid_until = datetime.utcnow() + timedelta(hours=24)
        doc = make_consent_doc(status="approved", scope="time_bound", valid_until=valid_until)
        doc["date_range_start"] = datetime(2025, 1, 1)
        doc["date_range_end"] = datetime(2025, 12, 31)
        db, _ = make_db(find_one_result=doc)
        result = await self.svc.check_access("doctor-123", "doctor", "patient-456", db)
        assert result.allowed is True
        assert "date_start" in result.filters
        assert "date_end" in result.filters

    # ── create_request ────────────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_create_request_returns_consent_record(self):
        db, col = make_db()
        request = ConsentRequest(
            doctor_id="doctor-123",
            patient_id="patient-456",
            purpose="Cardiology review",
            requested_scope=ConsentScope.FULL,
            duration_hours=24,
        )
        record = await self.svc.create_request(request, db)
        assert record.status == ConsentStatus.PENDING
        assert record.doctor_id == "doctor-123"
        assert record.patient_id == "patient-456"
        col.insert_one.assert_called_once()

    # ── process_grant ─────────────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_grant_approve_sets_approved_status(self):
        doc = make_consent_doc(status="pending")
        db, col = make_db(find_one_result=doc)
        grant = ConsentGrant(consent_id="test-consent-id", patient_id="patient-456", approved=True)
        record = await self.svc.process_grant(grant, db)
        assert record.status == ConsentStatus.APPROVED
        col.update_one.assert_called_once()

    @pytest.mark.asyncio
    async def test_grant_deny_sets_denied_status(self):
        doc = make_consent_doc(status="pending")
        db, col = make_db(find_one_result=doc)
        grant = ConsentGrant(consent_id="test-consent-id", patient_id="patient-456", approved=False)
        record = await self.svc.process_grant(grant, db)
        assert record.status == ConsentStatus.DENIED

    @pytest.mark.asyncio
    async def test_grant_not_found_raises(self):
        db, _ = make_db(find_one_result=None)
        grant = ConsentGrant(consent_id="nonexistent", patient_id="patient-456", approved=True)
        with pytest.raises(ValueError, match="not found"):
            await self.svc.process_grant(grant, db)

    @pytest.mark.asyncio
    async def test_grant_patient_mismatch_raises(self):
        doc = make_consent_doc(status="pending", patient_id="patient-456")
        db, _ = make_db(find_one_result=doc)
        grant = ConsentGrant(consent_id="test-consent-id", patient_id="wrong-patient", approved=True)
        with pytest.raises(ValueError, match="mismatch"):
            await self.svc.process_grant(grant, db)

    @pytest.mark.asyncio
    async def test_grant_already_approved_raises(self):
        doc = make_consent_doc(status="approved")
        db, _ = make_db(find_one_result=doc)
        grant = ConsentGrant(consent_id="test-consent-id", patient_id="patient-456", approved=True)
        with pytest.raises(ValueError, match="already"):
            await self.svc.process_grant(grant, db)

    # ── revoke ────────────────────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_revoke_returns_true_on_success(self):
        db, col = make_db()
        col.update_one = AsyncMock(return_value=MagicMock(modified_count=1))
        result = await self.svc.revoke("test-consent-id", "patient-456", db)
        assert result is True

    @pytest.mark.asyncio
    async def test_revoke_returns_false_when_not_found(self):
        db, col = make_db()
        col.update_one = AsyncMock(return_value=MagicMock(modified_count=0))
        result = await self.svc.revoke("nonexistent", "patient-456", db)
        assert result is False
