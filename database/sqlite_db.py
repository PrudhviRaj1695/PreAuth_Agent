from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database.models import Base, Patient
import os

DATABASE_URL = "sqlite:///patients.db"

class DatabaseManager:
    def __init__(self, database_url=DATABASE_URL):
        self.engine = create_engine(database_url, echo=False)
        self.SessionLocal = sessionmaker(bind=self.engine)
        
    def create_tables(self):
        """Create all database tables"""
        Base.metadata.create_all(self.engine)
        
    def get_session(self):
        """Get database session"""
        return self.SessionLocal()
        
    def seed_sample_data(self):
        """Insert sample patient data for testing"""
        session = self.get_session()
        try:
            # Clear existing data
            session.query(Patient).delete()
            
            # Sample patients with varied medical conditions
            sample_patients = [
                Patient(
                    patient_id=1,
                    name='Alice Johnson',
                    age=45,
                    gender='Female',
                    diagnosis_code='E11.9',  # Type 2 diabetes
                    procedure_code='99214',  # Office visit
                    lab_results='HbA1c:6.5;Cholesterol:190;BUN:15',
                    previous_procedures='99213;81001'
                ),
                Patient(
                    patient_id=2,
                    name='Bob Smith',
                    age=60,
                    gender='Male',
                    diagnosis_code='I10',  # Hypertension
                    procedure_code='93306',  # Echocardiogram
                    lab_results='HbA1c:7.8;Cholesterol:220;BP:150/90',
                    previous_procedures='99214;93000'
                ),
                Patient(
                    patient_id=3,
                    name='Carol Lee',
                    age=30,
                    gender='Female',
                    diagnosis_code='Z00.00',  # General examination
                    procedure_code='99395',  # Preventive visit
                    lab_results='HbA1c:5.4;Cholesterol:180;CBC:Normal',
                    previous_procedures=''
                )
            ]
            
            session.add_all(sample_patients)
            session.commit()
            print(f"✅ Seeded {len(sample_patients)} sample patients")
            
        except Exception as e:
            session.rollback()
            print(f"❌ Error seeding data: {e}")
        finally:
            session.close()

# Initialize database manager
db_manager = DatabaseManager()
