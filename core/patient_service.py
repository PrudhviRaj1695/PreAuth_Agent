import sys
import os
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root) if project_root not in sys.path else None

from database.sqlite_db import db_manager
from database.models import Patient
from typing import Optional, Dict

def get_patient(patient_id: int) -> Optional[Dict]:
    """
    Fetch patient data by patient_id
    Returns patient dict or None if not found
    """
    session = db_manager.get_session()
    try:
        patient = session.query(Patient).filter(Patient.patient_id == patient_id).first()
        if patient:
            return {
                'patient_id': patient.patient_id,
                'name': patient.name,
                'age': patient.age,
                'gender': patient.gender,
                'diagnosis_code': patient.diagnosis_code,
                'procedure_code': patient.procedure_code,
                'lab_results': patient.lab_results,
                'previous_procedures': patient.previous_procedures,
                'created_at': patient.created_at.isoformat() if patient.created_at else None
            }
        return None
    finally:
        session.close()

def get_all_patients() -> list:
    """Get all patients for testing"""
    session = db_manager.get_session()
    try:
        patients = session.query(Patient).all()
        return [
            {
                'patient_id': p.patient_id,
                'name': p.name,
                'age': p.age,
                'gender': p.gender,
                'diagnosis_code': p.diagnosis_code,
                'procedure_code': p.procedure_code
            }
            for p in patients
        ]
    finally:
        session.close()

# Test function
if __name__ == "__main__":
    print("🔍 Testing patient data retrieval...")
    
    # Test specific patient
    patient = get_patient(1)
    if patient:
        print(f"✅ Found patient: {patient['name']}")
        print(f"   Age: {patient['age']}, Gender: {patient['gender']}")
        print(f"   Diagnosis: {patient['diagnosis_code']}")
        print(f"   Procedure: {patient['procedure_code']}")
        print(f"   Lab Results: {patient['lab_results']}")
    else:
        print("❌ Patient not found")
    
    # Test all patients
    all_patients = get_all_patients()
    print(f"\n📋 All patients in database ({len(all_patients)}):")
    for p in all_patients:
        print(f"  - ID {p['patient_id']}: {p['name']}, {p['age']}y, {p['diagnosis_code']}")
