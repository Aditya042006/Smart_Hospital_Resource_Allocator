"""
OS Engine Module (os_engine.py)
Handles Priority Triage Mapping and Banker's Algorithm Resource Safety Check.
"""

EMERGENCY_KEYWORDS = ["Heart Attack", "Accident", "Stroke", "Emergency"]


def assign_priority(condition: str) -> int:
    """
    Maps emergency conditions to Priority 1 (High/Immediate)
    and general/routine conditions to Priority 4 (Normal FCFS).
    """
    if not condition:
        return 4
    for keyword in EMERGENCY_KEYWORDS:
        if keyword.lower() in condition.lower():
            return 1
    return 4


def check_safety(requested_beds: int, available_beds: int) -> bool:
    """
    Simplified Banker's Algorithm safety check for ICU bed allocation.
    Ensures requested resources do not exceed currently available resources
    so the system remains in a safe state without deadlock.
    """
    if requested_beds <= 0:
        return False
    if available_beds >= requested_beds:
        return True
    return False
