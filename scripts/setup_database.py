#!/usr/bin/env python3
"""
Script to setup the SQLAlchemy database with sample patient data
Story #1: Setup Local Patient Database
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.sqlite_db import db_manager

def setup_database():
    """Setup database and seed with sample data"""
    print("🚀 Setting up patient database...")
    
    # Create tables
    db_manager.create_tables()
    print("✅ Database tables created")
    
    # Seed with sample data
    db_manager.seed_sample_data()
    
    # Verify data was inserted
    session = db_manager.get_session()
    try:
        from database.models import Patient
        patient_count = session.query(Patient).count()
        print(f"✅ Database setup complete with {patient_count} patient records")
        
        # Display sample patients
        patients = session.query(Patient).all()
        for patient in patients:
            print(f"  - {patient.name} (ID: {patient.patient_id}, Age: {patient.age}, Diagnosis: {patient.diagnosis_code})")
            
    finally:
        session.close()

if __name__ == "__main__":
    setup_database()
