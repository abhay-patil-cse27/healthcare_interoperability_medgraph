"""
Seed a complete pregnancy demo flow for Sassoon Hospital.
Patient: Sunita Desai (existing)
Doctor: Dr. Sunita Bhosale (Gynecology) at Sassoon

This seeds:
1. Update Dr. Bhosale's specialization to Gynecology
2. Create OPD appointment for Sunita Desai with Dr. Bhosale
3. Create an active consent (patient → doctor)
4. Ingest pregnancy health records into the system
5. Create IPD admission (for delivery)

Run: python -m scripts.seed_pregnancy_demo
"""
import uuid
import boto3
from datetime import datetime, timedelta
from decimal import Decimal

REGION = "us-east-1"
d = boto3.resource('dynamodb', region_name=REGION)
users = d.Table('medgraph-users')
consents = d.Table('medgraph-consents')
appts = d.Table('medgraph-appointments')
admissions = d.Table('medgraph-admissions')
vitals = d.Table('medgraph-vitals')

def find_user(email=None, name_contains=None):
    r = users.scan()
    for u in r['Items']:
        if email and u.get('email') == email:
            return u
        if name_contains and name_contains.lower() in (u.get('full_name') or '').lower():
            return u
    return None

def main():
    print("=" * 60)
    print("  Pregnancy Demo — Sassoon Hospital")
    print("=" * 60)

    # Find our actors
    patient = find_user(email='sunita.desai@gmail.com')
    doctor = find_user(email='dr.bhosale@sassoon.org')
    nurse = find_user(email='nurse.gaikwad@sassoon.org')
    hitl = find_user(email='hitl.pune@medgraph.ai')

    if not patient or not doctor:
        print("ERROR: Required users not found!")
        return

    patient_id = patient['user_id']
    doctor_id = doctor['user_id']
    hospital_id = 'hosp-sassoon-pune-001'

    print(f"\n  Patient: {patient.get('full_name')} ({patient_id[:8]}...)")
    print(f"  Doctor:  {doctor.get('full_name')} ({doctor_id[:8]}...)")
    print(f"  Nurse:   {nurse.get('full_name') if nurse else 'N/A'}")
    print(f"  HITL:    {hitl.get('full_name') if hitl else 'N/A'}")

    now = datetime.utcnow()

    # 1. Update doctor specialization
    print("\n  [1] Setting Dr. Bhosale specialization = Gynecology & Obstetrics")
    users.update_item(
        Key={'user_id': doctor_id},
        UpdateExpression='SET specialization = :spec',
        ExpressionAttributeValues={':spec': 'Gynecology & Obstetrics'}
    )

    # 2. Assign patient to Sassoon hospital
    print("  [2] Assigning Sunita Desai to Sassoon hospital")
    users.update_item(
        Key={'user_id': patient_id},
        UpdateExpression='SET hospital_id = :h, gender = :g, date_of_birth = :dob, blood_group = :bg, mrn = :mrn',
        ExpressionAttributeValues={
            ':h': hospital_id,
            ':g': 'female',
            ':dob': '1992-03-15',
            ':bg': 'B+',
            ':mrn': 'SASS-2026-00001',
        }
    )

    # 3. Create consent (approved, full scope)
    print("  [3] Creating active consent: Sunita Desai → Dr. Bhosale (full, 720h)")
    consent_id = str(uuid.uuid4())
    consents.put_item(Item={
        'consent_id': consent_id,
        'doctor_id': doctor_id,
        'patient_id': patient_id,
        'purpose': 'Pregnancy monitoring and antenatal care - 2nd trimester follow-up',
        'requested_scope': 'full',
        'duration_hours': 720,
        'status': 'approved',
        'created_at': (now - timedelta(days=30)).isoformat(),
        'granted_at': (now - timedelta(days=30)).isoformat(),
        'valid_until': (now + timedelta(days=30)).isoformat(),
    })

    # 4. Create OPD appointments
    print("  [4] Creating OPD appointments (antenatal visits)")
    for i, (days_ago, reason, status) in enumerate([
        (28, 'First antenatal visit - 12 weeks', 'completed'),
        (14, 'Second trimester screening - 20 weeks', 'completed'),
        (3, 'Routine antenatal checkup - 24 weeks', 'completed'),
        (0, 'Follow-up: glucose tolerance test results', 'scheduled'),
    ]):
        aid = str(uuid.uuid4())
        appts.put_item(Item={
            'id': aid,
            'appointment_id': aid,
            'doctor_id': doctor_id,
            'doctor_name': doctor.get('full_name'),
            'patient_id': patient_id,
            'patient_name': patient.get('full_name'),
            'hospital_id': hospital_id,
            'scheduled_time': (now - timedelta(days=days_ago)).isoformat(),
            'status': status,
            'reason': reason,
            'created_at': (now - timedelta(days=days_ago+1)).isoformat(),
        })

    # 5. Create IPD admission (for monitoring)
    print("  [5] Creating IPD admission (observation - high-risk pregnancy)")
    adm_id = str(uuid.uuid4())
    admissions.put_item(Item={
        'id': adm_id,
        'admission_id': adm_id,
        'patient_id': patient_id,
        'patient_name': patient.get('full_name'),
        'admitting_doctor_id': doctor_id,
        'doctor_name': doctor.get('full_name'),
        'hospital_id': hospital_id,
        'ward_id': 'ward-maternity-01',
        'bed_id': 'bed-M-003',
        'admission_time': (now - timedelta(hours=6)).isoformat(),
        'status': 'admitted',
        'diagnosis': 'High-risk pregnancy monitoring - gestational diabetes screening',
        'is_mlc': False,
    })

    # 6. Seed vitals
    print("  [6] Seeding vitals for Sunita Desai")
    for hours_ago, temp, hr, bp_s, bp_d, spo2 in [
        (6, '36.8', 82, 118, 76, 99),
        (3, '37.0', 85, 122, 78, 98),
        (1, '36.9', 80, 120, 75, 99),
    ]:
        vid = str(uuid.uuid4())
        vitals.put_item(Item={
            'id': vid,
            'vital_id': vid,
            'patient_id': patient_id,
            'temperature_c': Decimal(temp),
            'heart_rate': hr,
            'blood_pressure_systolic': bp_s,
            'blood_pressure_diastolic': bp_d,
            'spo2': spo2,
            'recorded_by': nurse['user_id'] if nurse else doctor_id,
            'recorder_name': nurse.get('full_name') if nurse else doctor.get('full_name'),
            'recorded_at': (now - timedelta(hours=hours_ago)).isoformat(),
            'is_alert': False,
        })

    print("\n" + "=" * 60)
    print("  DEMO FLOW READY!")
    print("=" * 60)
    print(f"""
  Login credentials (all passwords: Medgraph@2026):

  1. PATIENT — Sunita Desai
     Email: sunita.desai@gmail.com
     Flow: Upload lab report PDF → View records → Chat about pregnancy

  2. DOCTOR — Dr. Sunita Bhosale (Gynecology)
     Email: dr.bhosale@sassoon.org
     Flow: See patient in dashboard → Clinical Query → FHIR Exchange

  3. NURSE — Smt. Asha Gaikwad
     Email: nurse.gaikwad@sassoon.org
     Flow: See admitted patient → Log vitals → Add notes

  4. HITL VALIDATOR — Shri. Rahul Shinde
     Email: hitl.pune@medgraph.ai
     Flow: Review AI screening → Edit/Accept → Forward to doctor

  5. HOSPITAL ADMIN — Dr. Anita Kulkarni
     Email: admin@sassoonhospital.org
     Flow: View staff → Manage departments → Invite staff

  6. OPD STAFF / RECEPTIONIST
     Flow: Book appointment → View queue → Update status

  7. IPD STAFF
     Flow: Admit patient → View beds → Discharge

  8. PHARMACIST
     Flow: View prescription queue → Dispense

  9. INSURANCE OFFICER
     Flow: Create claim → Track status

  10. SUPER ADMIN
      Email: superadmin@medgraph.ai
      Flow: System stats → Create hospitals → Manage all users

  PREGNANCY WALKTHROUGH:
  ─────────────────────
  Step 1: Login as Sunita Desai (patient)
          → Upload pregnancy lab report (glucose tolerance test PDF)
          → Grant consent to Dr. Bhosale

  Step 2: Login as Dr. Bhosale (doctor)
          → See Sunita in "My Patients" (Active IPD + Today's OPD)
          → Clinical Query: "Summarize pregnancy status for Sunita Desai"
          → FHIR Exchange: Generate FHIR bundle

  Step 3: Login as Nurse Gaikwad
          → See Sunita in admitted patients
          → Log vitals (BP, temp, HR)
          → Add clinical note

  Step 4: Login as HITL Validator
          → See AI screening in queue (from uploaded lab report)
          → Review, edit if needed, forward to Dr. Bhosale

  Step 5: Login as Dr. Bhosale again
          → Check Screening Inbox → See forwarded report
          → Mark as reviewed
""")


if __name__ == "__main__":
    main()
