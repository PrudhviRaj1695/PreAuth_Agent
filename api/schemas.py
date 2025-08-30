from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class AuthorizationRequest(BaseModel):
    patient_id: int

class AuthorizationResponse(BaseModel):
    patient_id: int
    patient_name: str
    diagnosis_code: str
    procedure_code: str
    decision: str
    reasoning: str
    retrieved_sop: str
    similarity_score: float
    timestamp: str
    log_id: Optional[str] = None
    status: str = "completed"

class BatchAuthorizationRequest(BaseModel):
    patient_ids: list[int]

class HealthResponse(BaseModel):
    status: str
    timestamp: str
    version: str
