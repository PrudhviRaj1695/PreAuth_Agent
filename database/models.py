from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

Base = declarative_base()

class Patient(Base):
    __tablename__ = 'patients'
    
    patient_id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    age = Column(Integer, nullable=False)
    gender = Column(String(10), nullable=False)
    diagnosis_code = Column(String(20), nullable=False)
    procedure_code = Column(String(20), nullable=False)
    lab_results = Column(Text)  # JSON-like string: "HbA1c:6.5;Cholesterol:190"
    previous_procedures = Column(Text)  # Comma-separated: "P100;P200"
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<Patient(id={self.patient_id}, name='{self.name}', age={self.age})>"

class AuthorizationLog(Base):
    __tablename__ = 'authorization_logs'
    
    log_id = Column(Integer, primary_key=True)
    patient_id = Column(Integer, nullable=False)
    decision = Column(String(20), nullable=False)  # "Approved" or "Denied"
    reasoning = Column(Text, nullable=False)
    sop_references = Column(Text)  # References to SOPs used
    timestamp = Column(DateTime, default=datetime.utcnow)
