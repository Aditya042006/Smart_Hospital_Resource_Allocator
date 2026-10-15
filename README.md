# Smart Hospital Resource Allocator

A three-tier hospital triage and ICU bed allocation system using **Operating System** concepts (Priority Triage, Banker's Safety Check, Mutex Locks) and **DBMS** transactions (SQLite atomic commit/rollback).

## Architecture & Files
- `streamlit_app.py`: Five-screen role-based Streamlit UI (Admin/Reception, Doctor, Lab/Radiology, Pharmacy, Patient Portal). Automatically starts the Flask backend in a background thread if not already running, so it works out-of-the-box on **Streamlit Cloud** as well as locally.
- `app.py`: Flask REST API (`http://127.0.0.1:5000/api`) with `threading.Lock()` concurrency protection.
- `os_engine.py`: Priority mapping (`Priority 1` for Emergency, `Priority 4` for Routine) and Banker's algorithm bed-safety check.
- `db_engine.py`: SQLite database (`hospital.db`) initialization and transactional ICU bed allocation.
- `run_demo.py`: Automated sequential test suite for validating API routes and database transactions.
- `requirements.txt`: Python dependencies for local run and Streamlit Cloud deployment.

## How to Run Locally
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Run the Streamlit app (it will automatically boot the Flask API server in the background if not running):
   ```bash
   streamlit run streamlit_app.py
   ```
   *(Optional)* You can also run `python app.py` in a separate terminal and `python run_demo.py` to test the REST API directly.
