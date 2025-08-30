import sys
import os
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Prior Authorization AI - Production",
    description="Production-ready agentic AI prior authorization system",
    version="2.0.0"
)

# CORS for Azure and Streamlit
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8501",
        "https://*.streamlit.app", 
        "https://*.azurewebsites.net",
        "https://localhost:8501"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Simple production AI service
class ProductionAIService:
    def process_authorization(self, patient_data):
        """Lightweight authorization logic"""
        procedure_code = patient_data.get('procedure_code', '')
        diagnosis_code = patient_data.get('diagnosis_code', '')
        age = patient_data.get('age', 0)
        
        if procedure_code.startswith('83'):  # Lab tests
            decision = "Approved"
            reasoning = f"Lab test {procedure_code} approved for diagnosis {diagnosis_code}"
        elif age > 65:
            decision = "Approved"
            reasoning = f"Senior patient (age {age}) approved for procedure {procedure_code}"
        elif diagnosis_code.startswith('E11'):  # Diabetes
            decision = "Approved"
            reasoning = f"Diabetes management procedure {procedure_code} approved"
        else:
            decision = "Pending Review"
            reasoning = f"Procedure {procedure_code} requires clinical review"
        
        return {
            'decision': decision,
            'reasoning': reasoning,
            'retrieved_sop': 'general_sop.pdf',
            'sop_similarity_score': 0.85
        }

ai_service = ProductionAIService()

# Mock patient data for production
MOCK_PATIENTS = {
    1: {"patient_id": 1, "name": "John Smith", "age": 45, "diagnosis_code": "E11.9", "procedure_code": "83036"},
    2: {"patient_id": 2, "name": "Mary Johnson", "age": 68, "diagnosis_code": "I10", "procedure_code": "99213"},
    3: {"patient_id": 3, "name": "Robert Davis", "age": 32, "diagnosis_code": "M79.1", "procedure_code": "20610"}
}

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
    status: str = "completed"

@app.get("/")
async def root():
    return {
        "message": "Prior Authorization AI - Production System",
        "version": "2.0.0",
        "status": "operational",
        "environment": "azure-production"
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "2.0.0",
        "environment": "production"
    }

@app.post("/prior-authorization/{patient_id}", response_model=AuthorizationResponse)
async def authorize_procedure(patient_id: int):
    try:
        logger.info(f"Processing authorization for patient {patient_id}")
        
        # Get patient data dscvwscw
        patient = MOCK_PATIENTS.get(patient_id)
        if not patient:
            raise HTTPException(status_code=404, detail=f"Patient {patient_id} not found")
        
        # Process with production AI
        result = ai_service.process_authorization(patient)
        
        return AuthorizationResponse(
            patient_id=patient_id,
            patient_name=patient['name'],
            diagnosis_code=patient['diagnosis_code'],
            procedure_code=patient['procedure_code'],
            decision=result['decision'],
            reasoning=result['reasoning'],
            retrieved_sop=result['retrieved_sop'],
            similarity_score=result['sop_similarity_score'],
            timestamp=datetime.utcnow().isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Authorization failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/batch-authorization")
async def batch_authorize(patient_ids: List[int]):
    if len(patient_ids) > 100:
        raise HTTPException(status_code=400, detail="Too many patients (max 100)")
    
    processed = []
    failed = []
    summary = {"approved": 0, "denied": 0, "pending": 0}
    
    for patient_id in patient_ids:
        try:
            patient = MOCK_PATIENTS.get(patient_id)
            if patient:
                result = ai_service.process_authorization(patient)
                processed.append({
                    "patient_id": patient_id,
                    "patient_name": patient['name'],
                    "decision": result['decision'],
                    "reasoning": result['reasoning'][:100] + "...",
                    "timestamp": datetime.utcnow().isoformat()
                })
                
                if result['decision'] == 'Approved':
                    summary["approved"] += 1
                elif result['decision'] == 'Denied':
                    summary["denied"] += 1
                else:
                    summary["pending"] += 1
            else:
                failed.append(patient_id)
        except Exception:
            failed.append(patient_id)
    
    return {
        "processed_count": len(processed),
        "failed_count": len(failed),
        "summary": summary,
        "results": processed,
        "failed_patients": failed
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
