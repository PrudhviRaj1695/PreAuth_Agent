import sys
import os
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root) if project_root not in sys.path else None

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import json
from datetime import datetime

# Import your system components
from core.end_to_end_flow import EndToEndPriorAuth
from database.mongo_logger import PriorAuthLogger


# Initialize FastAPI app
app = FastAPI(
    title="Agentic AI Prior Authorization API",
    description="RAG-powered medical prior authorization system",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8501", "http://127.0.0.1:8501"],  # Streamlit ports
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global PA system instance
pa_system = None

@app.on_event("startup")
async def startup_event():
    """Initialize prior authorization system on startup"""
    global pa_system
    try:
        print("🚀 Initializing Prior Authorization System...")
        pa_system = EndToEndPriorAuth()
        print("✅ Prior Authorization System initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize PA system: {e}")
        # Don't raise - allow API to start even if PA system has issues

# Pydantic models for request/response
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

class BatchResponse(BaseModel):
    processed_count: int
    failed_count: int
    summary: dict
    results: List[dict]
    failed_patients: List[int]

# API Endpoints
@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "🏥 Agentic AI Prior Authorization API",
        "version": "1.0.0",
        "description": "RAG-powered medical prior authorization system",
        "endpoints": {
            "health": "/health",
            "docs": "/docs",
            "single_auth": "/prior-authorization/{patient_id}",
            "batch_auth": "/batch-authorization",
            "patient_history": "/patient/{patient_id}/history",
            "analytics": "/analytics/decisions"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
        "pa_system_ready": pa_system is not None
    }

@app.post("/prior-authorization/{patient_id}")
async def authorize_procedure(patient_id: int):
    """
    Main prior authorization endpoint
    Process authorization for a single patient
    """
    if not pa_system:
        raise HTTPException(status_code=503, detail="Prior Authorization System not initialized")
    
    try:
        print(f"🔍 Processing authorization for patient {patient_id}")
        
        # Process authorization
        result = pa_system.process_prior_authorization(patient_id, log_decision=True)
        
        if not result:
            raise HTTPException(
                status_code=404, 
                detail=f"Patient {patient_id} not found or authorization processing failed"
            )
        
        print(f"✅ Authorization completed for patient {patient_id}: {result['decision']}")
        
        # Return structured response
        return {
            "patient_id": result['patient_id'],
            "patient_name": result['patient_name'],
            "diagnosis_code": result['diagnosis_code'],
            "procedure_code": result['procedure_code'],
            "decision": result['decision'],
            "reasoning": result['reasoning'],
            "retrieved_sop": result['retrieved_sop'],
            "similarity_score": result.get('sop_similarity_score', 0.0),
            "timestamp": result['timestamp'],
            "log_id": result.get('log_id'),
            "status": result.get('processing_status', 'completed')
        }
        
    except Exception as e:
        print(f"❌ Authorization error for patient {patient_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Authorization processing failed: {str(e)}")

@app.post("/batch-authorization")
async def batch_authorize(patient_ids: List[int]):
    """Batch process multiple authorizations"""
    if not pa_system:
        raise HTTPException(status_code=503, detail="Prior Authorization System not initialized")
    
    if not patient_ids:
        raise HTTPException(status_code=400, detail="No patient IDs provided")
    
    if len(patient_ids) > 100:  # Reasonable limit
        raise HTTPException(status_code=400, detail="Too many patients (max 100)")
    
    try:
        print(f"📊 Processing batch authorization for {len(patient_ids)} patients")
        
        batch_results = pa_system.batch_process(patient_ids)
        
        return {
            "processed_count": len(batch_results['processed']),
            "failed_count": len(batch_results['failed']),
            "summary": batch_results['summary'],
            "results": batch_results['processed'],
            "failed_patients": batch_results['failed']
        }
        
    except Exception as e:
        print(f"❌ Batch processing error: {e}")
        raise HTTPException(status_code=500, detail=f"Batch processing failed: {str(e)}")

@app.get("/patient/{patient_id}/history")
async def get_patient_history(patient_id: int):
    """Get authorization history for a specific patient"""
    try:
        logger = PriorAuthLogger()
        history = logger.get_patient_history(patient_id)
        
        return {
            "patient_id": patient_id,
            "authorization_count": len(history),
            "history": history
        }
        
    except Exception as e:
        print(f"❌ Error retrieving history for patient {patient_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve patient history: {str(e)}")

@app.get("/analytics/decisions")
async def get_decision_analytics():
    """Get decision analytics and statistics"""
    try:
        logger = PriorAuthLogger()
        stats = logger.get_decision_stats()
        
        return {
            "decision_statistics": stats,
            "generated_at": datetime.utcnow().isoformat(),
            "total_decisions": stats.get('total', 0),
            "approval_rate": (stats.get('Approved', 0) / max(stats.get('total', 1), 1)) * 100,
            "denial_rate": (stats.get('Denied', 0) / max(stats.get('total', 1), 1)) * 100
        }
        
    except Exception as e:
        print(f"❌ Error retrieving analytics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve analytics: {str(e)}")

# Additional utility endpoints
@app.get("/patients")
async def list_patients():
    """Get list of available patients (for testing)"""
    try:
        from core.patient_service import get_all_patients
        patients = get_all_patients()
        return {"patients": patients, "count": len(patients)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve patients: {str(e)}")

@app.get("/sops")
async def list_sops():
    """Get list of available SOPs"""
    try:
        from core.pdf_extractor import extract_all_sop_texts
        sop_texts = extract_all_sop_texts()
        return {
            "sops": list(sop_texts.keys()),
            "count": len(sop_texts),
            "total_characters": sum(len(text) for text in sop_texts.values())
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve SOPs: {str(e)}")

# Run the app
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
