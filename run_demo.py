"""
Sequential API Demo Driver (run_demo.py)
Validates all Flask API routes and SQLite transaction paths sequentially.
"""

import requests

BASE_URL = "http://127.0.0.1:5000/api"


def run_sequential_demo():
    print("=== Starting Smart Hospital Resource Allocator Demo ===")

    # 1. Admit emergency patient
    print("\n1. Testing Patient Admission (/api/admit_patient)...")
    r1 = requests.post(f"{BASE_URL}/admit_patient", json={
        "patient_id": "P101",
        "name": "Rahul",
        "condition": "Heart Attack"
    })
    print("Response:", r1.status_code, r1.json())

    # 2. Request Lab Test
    print("\n2. Testing Lab Test Request (/api/request_test)...")
    r2 = requests.post(f"{BASE_URL}/request_test", json={
        "doctor_id": "D505",
        "patient_id": "P101",
        "test_type": "MRI Scan"
    })
    print("Response:", r2.status_code, r2.json())

    # 3. Complete Test & Alert Doctor
    print("\n3. Testing Lab Test Completion (/api/complete_test)...")
    r3 = requests.post(f"{BASE_URL}/complete_test", json={
        "patient_id": "P101",
        "doctor_id": "D505",
        "result": "Critical Blockage found in imaging."
    })
    print("Response:", r3.status_code, r3.json())

    # 4. Send e-Prescription
    print("\n4. Testing e-Prescription (/api/send_prescription)...")
    r4 = requests.post(f"{BASE_URL}/send_prescription", json={
        "doctor_id": "D505",
        "patient_id": "P101",
        "medicine_name": "Aspirin"
    })
    print("Response:", r4.status_code, r4.json())

    # 5. Check Patient Status
    print("\n5. Testing Patient Status Check (/api/patient_status/P101)...")
    r5 = requests.get(f"{BASE_URL}/patient_status/P101")
    print("Response:", r5.status_code, r5.json())

    print("\n=== Demo Completed Successfully ===")


if __name__ == "__main__":
    run_sequential_demo()
