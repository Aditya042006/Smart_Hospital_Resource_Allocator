"""
Flask Backend API (app.py)
Exposes REST API endpoints for Admission, Lab Tests, Reports, and Pharmacy.
Protected by Python threading.Lock for concurrency safety.
"""

import threading
from flask import Flask, request, jsonify
import os_engine
import db_engine

app = Flask(__name__)

# Mutex lock to prevent race conditions during concurrent ICU admissions
admission_lock = threading.Lock()

# Initialize SQLite tables on startup
db_engine.init_db()


@app.route("/api/health", methods=["GET"])
def health_check():
    return jsonify({
        "status": "ok",
        "available_icu_beds": db_engine.get_available_beds()
    }), 200


@app.route("/api/admit_patient", methods=["POST"])
def admit_patient():
    data = request.get_json(silent=True) or {}
    patient_id = data.get("patient_id", "P101").strip()
    name = data.get("name", "Unknown").strip()
    condition = data.get("condition", "General Routine").strip()

    with admission_lock:
        priority = os_engine.assign_priority(condition)
        available_beds = db_engine.get_available_beds()
        is_safe = os_engine.check_safety(requested_beds=1, available_beds=available_beds)

        tx_result = db_engine.allocate_bed_and_admit(
            patient_id=patient_id,
            name=name,
            condition=condition,
            priority=priority,
            is_safe=is_safe
        )

        if tx_result.get("status") == "Error":
            return jsonify({
                "status": "Failed",
                "message": tx_result.get("error", "Database transaction error")
            }), 500

        if tx_result.get("admitted"):
            return jsonify({
                "status": "Success",
                "patient_id": patient_id,
                "priority": priority,
                "remaining_beds": tx_result.get("remaining_beds"),
                "message": f"Patient {patient_id} admitted to ICU."
            }), 200
        else:
            return jsonify({
                "status": "Queued",
                "patient_id": patient_id,
                "priority": priority,
                "remaining_beds": tx_result.get("remaining_beds", 0),
                "message": "No ICU beds safely available. Patient added to priority waitlist."
            }), 200


@app.route("/api/request_test", methods=["POST"])
def request_test():
    data = request.get_json(silent=True) or {}
    doctor_id = data.get("doctor_id", "D505")
    patient_id = data.get("patient_id", "P101")
    test_type = data.get("test_type", "Blood Test")

    print(f"[LAB LOG] Doctor {doctor_id} requested '{test_type}' for Patient {patient_id}.")
    return jsonify({
        "status": f"Test '{test_type}' scheduled for Patient {patient_id}",
        "doctor_id": doctor_id,
        "patient_id": patient_id,
        "test_type": test_type
    }), 200


@app.route("/api/complete_test", methods=["POST"])
def complete_test():
    data = request.get_json(silent=True) or {}
    patient_id = data.get("patient_id", "P101")
    doctor_id = data.get("doctor_id", "D505")
    result = data.get("result", "Normal")

    print(f"[ALERT LOG] Test completed for Patient {patient_id}. Notifying Doctor {doctor_id}: {result}")
    return jsonify({
        "status": "Report Generated & Sent",
        "patient_id": patient_id,
        "doctor_id": doctor_id,
        "result": result
    }), 200


@app.route("/api/send_prescription", methods=["POST"])
def send_prescription():
    data = request.get_json(silent=True) or {}
    doctor_id = data.get("doctor_id", "D505")
    patient_id = data.get("patient_id", "P101")
    medicine_name = data.get("medicine_name", "Aspirin")

    print(f"[PHARMACY LOG] e-Prescription from Doctor {doctor_id} for Patient {patient_id}: {medicine_name}")
    return jsonify({
        "status": f"e-Prescription for '{medicine_name}' sent to Pharmacy",
        "doctor_id": doctor_id,
        "patient_id": patient_id,
        "medicine_name": medicine_name
    }), 200


@app.route("/api/dispense_medicine", methods=["POST"])
def dispense_medicine():
    data = request.get_json(silent=True) or {}
    patient_id = data.get("patient_id", "P101")
    medicine_name = data.get("medicine_name", "Aspirin")

    print(f"[PHARMACY DISPENSE] Dispensed '{medicine_name}' to Patient {patient_id}.")
    return jsonify({
        "status": f"Medicine '{medicine_name}' dispensed to Patient {patient_id}",
        "patient_id": patient_id,
        "medicine_name": medicine_name
    }), 200


@app.route("/api/patient_status/<patient_id>", methods=["GET"])
def patient_status(patient_id):
    record = db_engine.get_patient_status(patient_id)
    if record:
        return jsonify({
            "found": True,
            "patient_id": record["patient_id"],
            "name": record["name"],
            "condition": record["condition"],
            "priority": record["priority"],
            "status": record["status"],
            "bed_allocated": bool(record["bed_allocated"])
        }), 200
    return jsonify({
        "found": False,
        "patient_id": patient_id,
        "priority": 1,
        "status": "ICU Bed Allocated | Priority Level 1 (Emergency) [Sample Status]"
    }), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
