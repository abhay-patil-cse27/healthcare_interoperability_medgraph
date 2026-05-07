from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional
from app.models.rbac import Permission
from app.dependencies import get_db, require_permission
import uuid
import re
from datetime import datetime

router = APIRouter()


def _sanitize_text_input(value):
    """
    Sanitize text inputs from staff to prevent injection attacks.
    Strips HTML/script tags and null bytes while preserving clinical content.
    """
    if not isinstance(value, str):
        return value
    # Remove null bytes
    value = value.replace("\x00", "")
    # Strip HTML/script tags
    value = re.sub(r"<script[^>]*>.*?</script>", "", value, flags=re.IGNORECASE | re.DOTALL)
    value = re.sub(r"<[^>]+>", "", value)
    # Limit length to prevent abuse (10KB per field)
    return value[:10240]


def _sanitize_dict(data: dict) -> dict:
    """Recursively sanitize all string values in a dict."""
    sanitized = {}
    for k, v in data.items():
        if isinstance(v, str):
            sanitized[k] = _sanitize_text_input(v)
        elif isinstance(v, dict):
            sanitized[k] = _sanitize_dict(v)
        elif isinstance(v, list):
            sanitized[k] = [_sanitize_text_input(i) if isinstance(i, str) else i for i in v]
        else:
            sanitized[k] = v
    return sanitized

# ── Doctor Patient endpoints ──────────────────────────────────────────────

@router.get("/my-patients")
async def get_my_patients(
    db = Depends(get_db),
    current_user = Depends(require_permission(Permission.PATIENT_READ_ASSIGNED.value))
):
    """
    Returns 3 categories for a doctor/surgeon:
      - active_admissions: current IPD patients admitted under this doctor
      - todays_appointments: today's OPD appointments with this doctor
      - patient_history: all past completed appointments & discharged admissions
    """
    doctor_id = current_user["user_id"]

    # 1) Active IPD admissions
    try:
        adm_results = await db.admissions.find({"admitting_doctor_id": doctor_id, "status": "admitted"}).to_list(100)
    except Exception:
        adm_results = []
    active_admissions = adm_results

    # 2) All OPD appointments under this doctor
    try:
        all_appointments = await db.appointments.find({"doctor_id": doctor_id}).to_list(100)
    except Exception:
        all_appointments = []

    # 3) Past history - discharged admissions
    try:
        past_admissions = await db.admissions.find({"admitting_doctor_id": doctor_id, "status": "discharged"}).to_list(50)
    except Exception:
        past_admissions = []

    past_appointments = [a for a in all_appointments if a.get("status") == "completed"]

    # 4) Unique registered patients
    seen_patients = set()
    registered_patients = []
    for a in all_appointments:
        pid = a.get("patient_id")
        if pid and pid not in seen_patients:
            seen_patients.add(pid)
            try:
                patient = await db.users.find_one({"user_id": pid})
                if patient:
                    registered_patients.append({
                        "user_id":   patient.get("user_id"),
                        "full_name": patient.get("full_name"),
                        "email":     patient.get("email"),
                        "phone":     patient.get("phone"),
                        "abha_id":   patient.get("abha_id"),
                        "last_visit": a.get("scheduled_time"),
                    })
            except Exception:
                pass

    return {
        "active_admissions":    active_admissions,
        "todays_appointments":  all_appointments[:20],
        "past_admissions":      past_admissions,
        "past_appointments":    past_appointments[:30],
        "registered_patients":  registered_patients,
        "summary": {
            "active_inpatients":  len(active_admissions),
            "todays_opd":         len(all_appointments),
            "total_history":      len(past_admissions) + len(past_appointments),
            "registered_count":   len(registered_patients),
        }
    }

@router.get("/patient/{patient_id}/full-history")
async def get_patient_full_history(
    patient_id: str,
    db = Depends(get_db),
    current_user = Depends(require_permission(Permission.PATIENT_READ_ASSIGNED.value))
):
    """Full clinical history for a specific patient — for doctor's patient detail view."""
    patient = await db.users.find_one({"user_id": patient_id})
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    patient.pop("_id", None)
    patient.pop("hashed_password", None)

    # Admissions
    adm_cursor = db.admissions.find({"patient_id": patient_id}).sort("admission_time", -1)
    admissions = []
    async for doc in adm_cursor:
        doc.pop("_id", None)
        admissions.append(doc)

    # Appointments
    apt_cursor = db.appointments.find({"patient_id": patient_id}).sort("scheduled_time", -1)
    appointments = []
    async for doc in apt_cursor:
        doc.pop("_id", None)
        appointments.append(doc)

    # Prescriptions
    rx_cursor = db.prescriptions.find({"patient_id": patient_id}).sort("created_at", -1)
    prescriptions = []
    async for doc in rx_cursor:
        doc.pop("_id", None)
        prescriptions.append(doc)

    # Vitals (last 10)
    vit_cursor = db.vitals.find({"patient_id": patient_id}).sort("recorded_at", -1).limit(10)
    vitals = []
    async for doc in vit_cursor:
        doc.pop("_id", None)
        vitals.append(doc)

    # IPD Notes
    notes_cursor = db.ipd_notes.find({"patient_id": patient_id}).sort("timestamp", -1).limit(20)
    notes = []
    async for doc in notes_cursor:
        doc.pop("_id", None)
        notes.append(doc)

    return {
        "patient":       {k: patient[k] for k in ["user_id","full_name","email","phone","role"] if k in patient},
        "admissions":    admissions,
        "appointments":  appointments,
        "prescriptions": prescriptions,
        "vitals":        vitals,
        "notes":         notes,
    }


# ── Notes & Vitals (flexible dict) ────────────────────────────────────────

@router.post("/notes", status_code=201)
async def add_ipd_note(
    note: dict,
    db = Depends(get_db),
    current_user = Depends(require_permission(Permission.PATIENT_READ_ASSIGNED.value))
):
    note = _sanitize_dict(note)
    if "note_id" not in note:
        note["note_id"] = str(uuid.uuid4())
    note["author_id"]   = current_user["user_id"]
    note["author_name"] = current_user.get("full_name", "")
    note["author_role"] = current_user["role"]
    note["timestamp"]   = datetime.utcnow()
    await db.ipd_notes.insert_one(note)

    # Log activity
    await db.activity_logs.insert_one({
        "log_id":      str(uuid.uuid4()),
        "actor_id":    current_user["user_id"],
        "actor_name":  current_user.get("full_name", ""),
        "actor_role":  current_user["role"],
        "action":      "ipd_note_added",
        "resource":    f"patient/{note.get('patient_id','?')}",
        "hospital_id": current_user.get("hospital_id"),
        "timestamp":   datetime.utcnow(),
    })
    note.pop("_id", None)
    return note

@router.post("/vitals", status_code=201)
async def log_vitals(
    vital: dict,
    db = Depends(get_db),
    current_user = Depends(require_permission(Permission.VITALS_WRITE.value))
):
    vital = _sanitize_dict(vital)
    if "vital_id" not in vital:
        vital["vital_id"] = str(uuid.uuid4())
    vital["recorded_by"]   = current_user["user_id"] if current_user["role"] != "ward_bot" else "ward_bot"
    vital["recorder_name"] = current_user.get("full_name", "Ward Bot")
    vital["recorded_at"]   = datetime.utcnow()

    # Alert logic
    temp = vital.get("temperature_c")
    hr   = vital.get("heart_rate")
    spo2 = vital.get("spo2") or vital.get("sp02")
    vital["is_alert"] = bool(
        (temp and (temp > 38.5 or temp < 35.0)) or
        (hr   and (hr > 110 or hr < 50)) or
        (spo2 and spo2 < 94)
    )
    await db.vitals.insert_one(vital)

    # Create notification if alert
    if vital["is_alert"]:
        await db.notifications.insert_one({
            "notification_id": str(uuid.uuid4()),
            "type":      "vitals_alert",
            "priority":  "high",
            "title":     "⚠️ Critical Vitals Alert",
            "message":   f"Abnormal vitals recorded for patient {vital.get('patient_id','?')}. Immediate review required.",
            "patient_id":vital.get("patient_id"),
            "for_roles": ["doctor", "surgeon", "nurse", "ward_incharge"],
            "hospital_id": current_user.get("hospital_id"),
            "read_by":   [],
            "created_at":datetime.utcnow(),
        })

    vital.pop("_id", None)
    return vital

@router.get("/patients/{patient_id}/vitals")
async def get_patient_vitals(
    patient_id: str,
    db = Depends(get_db),
    current_user = Depends(require_permission(Permission.VITALS_READ.value))
):
    cursor = db.vitals.find({"patient_id": patient_id}).sort("recorded_at", -1).limit(50)
    results = []
    async for doc in cursor:
        doc.pop("_id", None)
        results.append(doc)
    return results
