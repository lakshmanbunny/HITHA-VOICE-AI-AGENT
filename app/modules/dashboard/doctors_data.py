"""Shared doctor and department seed data.

Used by both the API layer and the response generator for slot presentation.
"""
from __future__ import annotations

DOCTORS = [
    {
        "id": "doc-001",
        "name": "Dr. Priya Sharma",
        "specialty": "Cardiology",
        "qualification": "MD, DM Cardiology",
        "experience_years": 12,
        "language": ["English", "Hindi", "Telugu"],
    },
    {
        "id": "doc-002",
        "name": "Dr. Anil Reddy",
        "specialty": "Cardiology",
        "qualification": "MD, DM Cardiology",
        "experience_years": 15,
        "language": ["English", "Telugu"],
    },
    {
        "id": "doc-003",
        "name": "Dr. Venkat Rao",
        "specialty": "ENT",
        "qualification": "MS ENT",
        "experience_years": 10,
        "language": ["English", "Telugu", "Hindi"],
    },
    {
        "id": "doc-004",
        "name": "Dr. Meena Iyer",
        "specialty": "Dermatology",
        "qualification": "MD Dermatology",
        "experience_years": 8,
        "language": ["English", "Hindi"],
    },
    {
        "id": "doc-005",
        "name": "Dr. Suresh Babu",
        "specialty": "Orthopedics",
        "qualification": "MS Orthopedics",
        "experience_years": 20,
        "language": ["English", "Telugu"],
    },
    {
        "id": "doc-006",
        "name": "Dr. Lakshmi Naidu",
        "specialty": "General Medicine",
        "qualification": "MD General Medicine",
        "experience_years": 14,
        "language": ["English", "Telugu", "Hindi"],
    },
    {
        "id": "doc-007",
        "name": "Dr. Ramesh Gupta",
        "specialty": "Neurology",
        "qualification": "DM Neurology",
        "experience_years": 11,
        "language": ["English", "Hindi"],
    },
    {
        "id": "doc-008",
        "name": "Dr. Kavitha Reddy",
        "specialty": "Gynecology",
        "qualification": "MS OBG",
        "experience_years": 9,
        "language": ["English", "Telugu"],
    },
]

DEPARTMENTS = sorted({d["specialty"] for d in DOCTORS})

AVAILABLE_SLOTS = [
    "09:00 AM", "09:30 AM", "10:00 AM", "10:30 AM",
    "11:00 AM", "11:30 AM", "02:00 PM", "02:30 PM",
    "03:00 PM", "03:30 PM", "04:00 PM", "04:30 PM",
]


def get_available_slots(doctor_name: str | None = None) -> list[str]:
    """Return available time slots for a doctor. Static for now."""
    return list(AVAILABLE_SLOTS)
