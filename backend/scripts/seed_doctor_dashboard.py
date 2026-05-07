"""
Seed demo data for doctor dashboards.
Run: python -m scripts.seed_doctor_dashboard
"""
import uuid
import boto3
from datetime import datetime, timedelta
from decimal import Decimal

REGION = "us-east-1"
d = boto3.resource('dynamodb', region_name=REGION)

users_table = d.Table('medgraph-users')
appts_table = d.Table('medgraph-appointments')
admissions_table = d.Table('medgraph-admissions')
vitals_table = d.Table('medgraph-vitals')


def put_appointment(doctor_id, doctor_name, patient_id, patient_name, hospital_id, scheduled, status, reason):
    aid = str(uuid.uuid4())
    appts_table.put_item(Item={
        'id': aid,
        'appointment_id': aid,
        'doctor_id': doctor_id,
        'doctor_name': doctor_name,
        'patient_id': patient_id,
        'patient_name': patient_name,
        'hospital_id': hospital_id,
        'scheduled_time': scheduled.isoformat(),
        'status': status,
        'reason': reason,
        'created_at': (scheduled - timedelta(days=1)).isoformat(),
    })
    return aid


def put_admission(doctor_id, doctor_name, patient_id, patient_name, hospital_id, admission_time, status):
    aid = str(uuid.uuid4())
    admissions_table.put_item(Item={
        'id': aid,
        'admission_id': aid,
        'patient_id': patient_id,
        'patient_name': patient_name,
        'admitting_doctor_id': doctor_id,
        'doctor_name': doctor_name,
        'hospital_id': hospital_id,
        'ward_id': 'ward-general-01',
        'bed_id': f'bed-{hash(patient_id) % 50 + 1:03d}',
        'admission_time': admission_time.isoformat(),
        'status': status,
        'diagnosis': 'Under observation',
        'is_mlc': False,
    })
    return aid


def put_vital(patient_id, doctor_id, doctor_name):
    vid = str(uuid.uuid4())
    vitals_table.put_item(Item={
        'id': vid,
        'vital_id': vid,
        'patient_id': patient_id,
        'temperature_c': Decimal('37.2'),
        'heart_rate': 78,
        'spo2': 98,
        'blood_pressure_systolic': 120,
        'blood_pressure_diastolic': 80,
        'recorded_by': doctor_id,
        'recorder_name': doctor_name,
        'recorded_at': datetime.utcnow().isoformat(),
        'is_alert': False,
    })


def seed():
    print("Seeding doctor dashboard demo data...\n")

    all_users = users_table.scan()['Items']
    doctors = [u for u in all_users if u.get('role') in ['doctor', 'surgeon']]
    patients = [u for u in all_users if u.get('role') == 'patient']

    if not doctors or not patients:
        print("ERROR: No doctors or patients found. Run seed_test_users first.")
        return

    now = datetime.utcnow()
    reasons = ['Follow-up consultation', 'Routine checkup', 'Lab review', 'Post-op follow-up', 'Medication review']

    for i, doctor in enumerate(doctors):
        did = doctor['user_id']
        dname = doctor.get('full_name', 'Doctor')
        hosp = doctor.get('hospital_id', 'hosp-default')

        # Assign 2-4 patients per doctor
        start_idx = (i * 3) % len(patients)
        assigned = patients[start_idx:start_idx+3]
        if len(assigned) < 2:
            assigned = patients[:3]

        print(f"  {dname} ({hosp})")

        for j, patient in enumerate(assigned):
            pid = patient['user_id']
            pname = patient.get('full_name', 'Patient')

            # Today's appointment
            put_appointment(did, dname, pid, pname, hosp, now - timedelta(hours=j), 'scheduled', reasons[j % len(reasons)])

            # Past completed appointment
            put_appointment(did, dname, pid, pname, hosp, now - timedelta(days=3+j), 'completed', reasons[(j+1) % len(reasons)])

            # First patient gets an IPD admission
            if j == 0:
                put_admission(did, dname, pid, pname, hosp, now - timedelta(days=1), 'admitted')
                put_vital(pid, did, dname)

        print(f"    → {len(assigned)} patients, {len(assigned)*2} appointments, 1 admission")

    print(f"\n  Final counts:")
    print(f"    Appointments: {appts_table.scan(Select='COUNT')['Count']}")
    print(f"    Admissions:   {admissions_table.scan(Select='COUNT')['Count']}")
    print(f"    Vitals:       {vitals_table.scan(Select='COUNT')['Count']}")
    print("\n  Done! Restart the backend.")


if __name__ == "__main__":
    seed()
