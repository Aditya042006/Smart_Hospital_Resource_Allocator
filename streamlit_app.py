"""
Streamlit Role-Based Frontend (streamlit_app.py)
Connects to the Flask REST API at http://127.0.0.1:5000/api.
Automatically starts the Flask server in a background thread if it is not already running,
so this project works both locally AND on Streamlit Cloud / mobile devices!
"""

import threading
import time
import requests
import streamlit as st
import db_engine

BASE_URL = "http://127.0.0.1:5000/api"


@st.cache_resource
def ensure_backend_server():
    """
    Checks if the Flask API server is reachable on port 5000.
    If not (e.g., on Streamlit Cloud), starts app.py in a background daemon thread.
    """
    try:
        r = requests.get(f"{BASE_URL}/health", timeout=1)
        if r.status_code == 200:
            return True
    except Exception:
        pass

    from app import app as flask_app
    server_thread = threading.Thread(
        target=lambda: flask_app.run(host="0.0.0.0", port=5000, debug=False, use_reloader=False),
        daemon=True
    )
    server_thread.start()
    time.sleep(0.8)
    return True


ensure_backend_server()

st.set_page_config(page_title="Smart Hospital System", page_icon="🏥", layout="wide")

st.title("🏥 Smart Hospital Resource Allocator")

# Sidebar navigation for switching between role-based dashboards
dashboard = st.sidebar.radio(
    "Select Dashboard / Role",
    [
        "1. Admin / Reception Counter",
        "2. Doctor Dashboard",
        "3. Lab / Radiology Dashboard",
        "4. Pharmacy Dashboard",
        "5. Patient Portal"
    ]
)

st.sidebar.markdown("---")
available_beds = db_engine.get_available_beds()
st.sidebar.metric(label="🛏️ Available ICU Beds (SQLite)", value=available_beds)
st.sidebar.info("Flask API active on http://127.0.0.1:5000/api")

# ========================================================
# 1. ADMIN / RECEPTION COUNTER UI
# ========================================================
if dashboard == "1. Admin / Reception Counter":
    st.header("📋 Patient Registration & Resource Counter")
    st.write("Admit new patients and allocate ICU beds via OS Safety Engine.")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Patient Triage Registration")
        patient_id = st.text_input("Patient ID", value="P101")
        name = st.text_input("Patient Name", value="Rahul")
        condition = st.selectbox(
            "Condition / Emergency",
            ["Heart Attack", "Accident", "Stroke", "Emergency", "Fever", "General Routine"]
        )

        if st.button("Submit Registration", type="primary"):
            payload = {
                "patient_id": patient_id,
                "name": name,
                "condition": condition
            }
            try:
                response = requests.post(f"{BASE_URL}/admit_patient", json=payload, timeout=5)
                data = response.json()

                if data.get("status") == "Success":
                    st.success(
                        f"✅ Patient {patient_id} admitted successfully! "
                        f"Priority Assigned: {data.get('priority')} | "
                        f"Remaining ICU Beds: {data.get('remaining_beds')}"
                    )
                elif data.get("status") == "Queued":
                    st.warning(
                        f"⚠️ System Unsafe (Banker's Algorithm). "
                        f"Patient {patient_id} placed on waitlist (Priority {data.get('priority')})."
                    )
                else:
                    st.error(f"❌ Allocation Failed: {data.get('message')}")
            except Exception as e:
                st.error(f"Failed to connect to backend server: {e}")

    with col2:
        st.subheader("OS Simulator & Resource State")
        st.info("System uses *Banker's Algorithm* for safety checks and *Mutex Locks* to prevent race conditions.")
        st.markdown(f"**Current Available ICU Beds:** `{db_engine.get_available_beds()}`")

# ========================================================
# 2. DOCTOR DASHBOARD
# ========================================================
elif dashboard == "2. Doctor Dashboard":
    st.header("👨‍⚕️ Doctor Consultation & Ordering Module")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Request Lab / Radiology Test")
        doctor_id = st.text_input("Doctor ID", value="D505")
        p_id_test = st.text_input("Patient ID for Test", value="P101")
        test_type = st.selectbox("Select Test", ["MRI Scan", "CT Scan", "X-Ray", "Blood Test", "ECG"])

        if st.button("Request Test"):
            payload = {
                "doctor_id": doctor_id,
                "patient_id": p_id_test,
                "test_type": test_type
            }
            try:
                response = requests.post(f"{BASE_URL}/request_test", json=payload, timeout=5)
                data = response.json()
                st.success(f"✅ Test Requested! Status: {data.get('status')}")
            except Exception as e:
                st.error(f"Connection Error: {e}")

    with col2:
        st.subheader("Write e-Prescription")
        doc_id_rx = st.text_input("Doctor ID (Rx)", value="D505", key="doc_rx")
        p_id_rx = st.text_input("Patient ID (Rx)", value="P101", key="pat_rx")
        medicine = st.text_input("Medicine Name", value="Aspirin")

        if st.button("Send Prescription to Pharmacy"):
            payload = {
                "doctor_id": doc_id_rx,
                "patient_id": p_id_rx,
                "medicine_name": medicine
            }
            try:
                response = requests.post(f"{BASE_URL}/send_prescription", json=payload, timeout=5)
                data = response.json()
                st.success(f"✅ Prescription Processed! Status: {data.get('status')}")
            except Exception as e:
                st.error(f"Connection Error: {e}")

# ========================================================
# 3. LAB / RADIOLOGY DASHBOARD
# ========================================================
elif dashboard == "3. Lab / Radiology Dashboard":
    st.header("🔬 Lab & Radiology Operations")

    patient_id = st.text_input("Patient ID", value="P101")
    doctor_id = st.text_input("Assigned Doctor ID", value="D505")
    result = st.text_area("Test Results / Findings", value="Critical Blockage found in imaging.")

    if st.button("Complete Test & Notify Doctor", type="primary"):
        payload = {
            "patient_id": patient_id,
            "doctor_id": doctor_id,
            "result": result
        }
        try:
            response = requests.post(f"{BASE_URL}/complete_test", json=payload, timeout=5)
            data = response.json()
            st.success(f"✅ {data.get('status')}! Alert notification triggered for Doctor [{doctor_id}].")
        except Exception as e:
            st.error(f"Connection Error: {e}")

# ========================================================
# 4. PHARMACY DASHBOARD
# ========================================================
elif dashboard == "4. Pharmacy Dashboard":
    st.header("💊 Pharmacy Inventory & Prescriptions")

    patient_id = st.text_input("Patient ID", value="P101")
    medicine = st.text_input("Medicine Name", value="Aspirin")

    if st.button("Dispense Medicine"):
        payload = {
            "doctor_id": "D505",
            "patient_id": patient_id,
            "medicine_name": medicine
        }
        try:
            response = requests.post(f"{BASE_URL}/dispense_medicine", json=payload, timeout=5)
            data = response.json()
            st.success(f"✅ Inventory updated: {data.get('status')}")
        except Exception as e:
            st.error(f"Connection Error: {e}")

# ========================================================
# 5. PATIENT PORTAL
# ========================================================
elif dashboard == "5. Patient Portal":
    st.header("📱 Patient Queue & Status Kiosk")

    patient_id = st.text_input("Enter Patient ID to Check Status", value="P101")

    if st.button("Check Queue Status"):
        try:
            response = requests.get(f"{BASE_URL}/patient_status/{patient_id}", timeout=5)
            data = response.json()
            st.info(f"Showing priority and bed allocation status for *{patient_id}*.")
            if data.get("found"):
                st.success(
                    f"Patient: {data.get('name')} | Condition: {data.get('condition')} | "
                    f"Priority Level: {data.get('priority')} | Status: {data.get('status')}"
                )
            else:
                st.success(f"Status: {data.get('status')}")
        except Exception as e:
            st.error(f"Connection Error: {e}")
