import requests
import json
import time

BASE_URL = "http://localhost:8000"

def seed_data():
    # Login
    print("Logging in as Ramesh...")
    res = requests.post(f"{BASE_URL}/auth/login", json={
        "email": "patient.ramesh@gmail.com",
        "password": "Patient@123"
    })
    
    if res.status_code != 200:
        print("Login failed:", res.text)
        return
        
    data = res.json()
    token = data.get("access_token")
    user_id = data.get("user_id")
    
    if not token or not user_id:
        print("Could not extract token or user_id. Response:", data)
        return
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    records = [
        "Patient complains of severe chest pain that started 2 days ago. Pain radiates to the left arm and is accompanied by shortness of breath and sweating. Patient has a history of hypertension for 5 years, currently taking Amlodipine 5mg daily.",
        "Follow-up visit. The patient's blood pressure is 140/90 mmHg. Diagnosed with Type 2 Diabetes Mellitus. Prescribed Metformin 500mg twice daily and advised lifestyle modifications including diet and exercise.",
        "Patient reported a mild allergic reaction, presenting with hives and itching on the arms after consuming peanuts. Advised to avoid peanuts and prescribed Cetirizine 10mg once daily as needed."
    ]
    
    print(f"User ID: {user_id}")
    for idx, text in enumerate(records):
        print(f"Ingesting record {idx+1}...")
        payload = {
            "patient_id": user_id,
            "text": text,
            "source": "doctor_notes",
            "encounter_date": "2023-10-15"
        }
        ingest_res = requests.post(f"{BASE_URL}/memory/ingest", json=payload, headers=headers)
        if ingest_res.status_code in [200, 201]:
            print(f"Success! {ingest_res.json().get('status', 'Ingested')}")
        else:
            print(f"Failed! {ingest_res.text}")
        
        time.sleep(2) # Sleep to allow GROQ rate limits or pipeline to finish comfortably

if __name__ == "__main__":
    seed_data()
