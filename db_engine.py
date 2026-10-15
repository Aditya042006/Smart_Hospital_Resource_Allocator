"""
Database Engine Module (db_engine.py)
Handles SQLite persistence, resource tables, and transactional ICU bed allocation.
"""

import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "hospital.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initializes SQLite tables for resources, patients, lab tests, and prescriptions."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS resources (
                resource_name TEXT PRIMARY KEY,
                total_count INTEGER NOT NULL,
                available_count INTEGER NOT NULL
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS patients (
                patient_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                condition TEXT NOT NULL,
                priority INTEGER NOT NULL,
                status TEXT NOT NULL,
                bed_allocated INTEGER NOT NULL DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS lab_tests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_id TEXT NOT NULL,
                doctor_id TEXT NOT NULL,
                test_type TEXT,
                result TEXT,
                status TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS prescriptions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_id TEXT NOT NULL,
                doctor_id TEXT NOT NULL,
                medicine_name TEXT NOT NULL,
                status TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Seed default ICU beds if not present
        cursor.execute("SELECT available_count FROM resources WHERE resource_name = 'ICU_BED'")
        row = cursor.fetchone()
        if row is None:
            cursor.execute(
                "INSERT INTO resources (resource_name, total_count, available_count) VALUES ('ICU_BED', 10, 5)"
            )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def get_available_beds() -> int:
    """Returns currently available ICU beds from SQLite."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT available_count FROM resources WHERE resource_name = 'ICU_BED'")
        row = cursor.fetchone()
        return int(row["available_count"]) if row else 0
    finally:
        conn.close()


def allocate_bed_and_admit(patient_id: str, name: str, condition: str, priority: int, is_safe: bool):
    """
    Wraps ICU bed decrement and patient admission record insertion in an atomic
    SQLite transaction with commit/rollback handling.
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("BEGIN IMMEDIATE")

        cursor.execute("SELECT available_count FROM resources WHERE resource_name = 'ICU_BED'")
        row = cursor.fetchone()
        available = int(row["available_count"]) if row else 0

        if is_safe and available >= 1:
            cursor.execute(
                "UPDATE resources SET available_count = available_count - 1 WHERE resource_name = 'ICU_BED'"
            )
            status = "ICU Bed Allocated"
            bed_allocated = 1
        else:
            status = "Queued (Waiting for ICU Bed)"
            bed_allocated = 0

        cursor.execute("""
            INSERT OR REPLACE INTO patients (patient_id, name, condition, priority, status, bed_allocated)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (patient_id, name, condition, priority, status, bed_allocated))

        conn.commit()
        return {
            "admitted": bed_allocated == 1,
            "status": status,
            "remaining_beds": available - bed_allocated
        }
    except Exception as e:
        conn.rollback()
        return {
            "admitted": False,
            "status": "Error",
            "error": str(e)
        }
    finally:
        conn.close()


def get_patient_status(patient_id: str):
    """Fetches live patient admission and priority status from SQLite."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT patient_id, name, condition, priority, status, bed_allocated, created_at FROM patients WHERE patient_id = ?",
            (patient_id,)
        )
        row = cursor.fetchone()
        if row:
            return dict(row)
        return None
    finally:
        conn.close()
