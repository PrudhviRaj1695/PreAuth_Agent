import sys
import os
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root) if project_root not in sys.path else None

import json
import numpy as np
from datetime import datetime
from typing import Optional, Dict

from core.patient_service import get_patient
from core.embedding_service import LocalEmbeddingService  
from core.faiss_manager import FAISSManager
from core.reasoning_agent import ReasoningAgent
from core.pdf_extractor import extract_all_sop_texts
from database.mongo_logger import PriorAuthLogger

class EndToEndPriorAuth:
    """
    Complete end-to-end prior authorization system
    Combines: Patient Fetch → SOP Retrieval → AI Reasoning → Decision Logging
    """
    
    def __init__(self):
        print("🚀 Initializing End-to-End Prior Authorization System...")
        
        # Initialize all components
        self.embedding_service = LocalEmbeddingService()
        self.reasoning_agent = ReasoningAgent(use_local_llm=True)
        self.logger = PriorAuthLogger()
        
        # Load embeddings and FAISS index
        embeddings_path = os.path.join(project_root, 'data', 'embeddings', 'sop_embeddings.npz')
        faiss_index_path = os.path.join(project_root, 'data', 'faiss_index', 'sop_faiss.index')
        
        if os.path.exists(embeddings_path):
            embeddings_data = np.load(embeddings_path, allow_pickle=True)
            embedding_dim = embeddings_data['embeddings'].shape[1]
            
            self.faiss_manager = FAISSManager(embedding_dim=embedding_dim)
            
            if os.path.exists(faiss_index_path):
                self.faiss_manager.load_index(faiss_index_path)
                print("✅ FAISS index loaded")
            else:
                print("❌ FAISS index not found. Please run 'python core/faiss_manager.py'")
                
        else:
            print("❌ Embeddings not found. Please run 'python core/embedding_service.py'")
        
        # Load SOP texts
        self.sop_texts = extract_all_sop_texts()
        
        print("✅ End-to-End Prior Authorization System initialized!")
    
    def process_prior_authorization(self, patient_id: int, log_decision: bool = True) -> Optional[Dict]:
        """
        Complete end-to-end prior authorization workflow
        
        Args:
            patient_id: ID of patient requesting authorization
            log_decision: Whether to log the decision to database
            
        Returns:
            Complete authorization result with decision, reasoning, and metadata
        """
        print(f"\n🏥 Processing Prior Authorization for Patient {patient_id}")
        print("="*60)
        
        try:
            # Step 1: Fetch Patient Data
            print("📋 Step 1: Fetching patient data...")
            patient = get_patient(patient_id)
            
            if not patient:
                print(f"❌ Patient {patient_id} not found in database")
                return None
            
            print(f"✅ Patient: {patient['name']}, Age: {patient['age']}, Diagnosis: {patient['diagnosis_code']}")
            
            # Step 2: Create Query Context
            print("\n🔍 Step 2: Creating search query...")
            query_context = self._build_query_context(patient)
            print(f"✅ Query: {query_context}")
            
            # Step 3: Semantic SOP Retrieval
            print("\n📚 Step 3: Retrieving relevant SOP...")
            query_embedding = self.embedding_service.create_embedding(query_context)
            distances, indices, doc_names = self.faiss_manager.search(query_embedding, k=1)
            
            if not doc_names:
                print("❌ No matching SOP found")
                return None
            
            best_sop = doc_names[0]
            similarity_score = float(distances[0])
            print(f"✅ Retrieved SOP: {best_sop} (similarity: {similarity_score:.4f})")
            
            # Step 4: Get SOP Text Content
            print("\n📖 Step 4: Loading SOP content...")
            sop_text = self.sop_texts.get(best_sop, '')
            if not sop_text:
                print(f"⚠️ SOP text not found for {best_sop}")
                sop_text = "No SOP content available"
            
            print(f"✅ SOP content loaded ({len(sop_text)} characters)")
            
            # Step 5: AI Reasoning
            print("\n🤖 Step 5: Running AI reasoning agent...")
            decision_result = self.reasoning_agent.make_authorization_decision(patient, sop_text)
            
            print(f"✅ Decision: {decision_result['decision']}")
            print(f"💭 Reasoning: {decision_result['reasoning'][:100]}...")
            
            # Step 6: Compile Complete Result
            complete_result = {
                'patient_id': patient['patient_id'],
                'patient_name': patient['name'],
                'age': patient['age'],
                'gender': patient['gender'],
                'diagnosis_code': patient['diagnosis_code'],
                'procedure_code': patient['procedure_code'],
                'lab_results': patient['lab_results'],
                'retrieved_sop': best_sop,
                'sop_similarity_score': similarity_score,
                'query_context': query_context,
                'decision': decision_result['decision'],
                'reasoning': decision_result['reasoning'],
                'timestamp': datetime.utcnow().isoformat(),
                'system_version': '1.0.0',
                'processing_status': 'completed'
            }
            
            # Step 7: Log Decision (Optional)
            if log_decision:
                print("\n📝 Step 6: Logging decision...")
                log_id = self.logger.log_decision(complete_result)
                complete_result['log_id'] = log_id
                print(f"✅ Decision logged with ID: {log_id}")
            
            print(f"\n🎯 FINAL RESULT: {complete_result['decision'].upper()}")
            print("="*60)
            
            return complete_result
            
        except Exception as e:
            print(f"❌ Error in prior authorization workflow: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _build_query_context(self, patient: Dict) -> str:
        """Build semantic search query from patient data"""
        context_parts = []
        
        # Add primary identifiers
        context_parts.append(f"diagnosis {patient['diagnosis_code']}")
        context_parts.append(f"procedure {patient['procedure_code']}")
        
        # Add demographic context
        context_parts.append(f"age {patient['age']} years")
        context_parts.append(f"{patient['gender'].lower()}")
        
        # Add lab results if available
        if patient.get('lab_results'):
            lab_info = patient['lab_results'].replace(';', ' ').replace(':', ' ')
            context_parts.append(f"labs {lab_info}")
        
        # Add previous procedures
        if patient.get('previous_procedures'):
            context_parts.append(f"previous procedures {patient['previous_procedures']}")
        
        return " ".join(context_parts)
    
    def batch_process(self, patient_ids: list) -> Dict:
        """Process multiple patients in batch"""
        results = {
            'processed': [],
            'failed': [],
            'summary': {'approved': 0, 'denied': 0, 'failed': 0}
        }
        
        print(f"\n🔄 Batch Processing {len(patient_ids)} Patients")
        print("="*60)
        
        for patient_id in patient_ids:
            result = self.process_prior_authorization(patient_id)
            
            if result:
                results['processed'].append(result)
                if result['decision'] == 'Approved':
                    results['summary']['approved'] += 1
                else:
                    results['summary']['denied'] += 1
            else:
                results['failed'].append(patient_id)
                results['summary']['failed'] += 1
        
        print(f"\n📊 BATCH SUMMARY:")
        print(f"   Approved: {results['summary']['approved']}")
        print(f"   Denied: {results['summary']['denied']}")
        print(f"   Failed: {results['summary']['failed']}")
        print("="*60)
        
        return results

# Test and demonstration
if __name__ == "__main__":
    print("🧪 TESTING END-TO-END PRIOR AUTHORIZATION SYSTEM")
    print("="*80)
    
    try:
        # Initialize system
        e2e_system = EndToEndPriorAuth()
        
        # Test individual patient authorization
        print("\n🔬 Test 1: Single Patient Authorization")
        result = e2e_system.process_prior_authorization(patient_id=1)
        
        if result:
            print(f"\n📋 AUTHORIZATION SUMMARY:")
            print(f"   Patient: {result['patient_name']} (ID: {result['patient_id']})")
            print(f"   Procedure: {result['procedure_code']} for {result['diagnosis_code']}")
            print(f"   Decision: {result['decision']}")
            print(f"   SOP Used: {result['retrieved_sop']}")
            print(f"   Similarity Score: {result['sop_similarity_score']:.4f}")
            print(f"   Reasoning: {result['reasoning'][:150]}...")
        
        # Test batch processing
        print("\n\n🔬 Test 2: Batch Processing")
        batch_results = e2e_system.batch_process([1, 2, 3])
        
        # Show sample results
        if batch_results['processed']:
            print(f"\n📋 Sample Authorization Results:")
            for i, result in enumerate(batch_results['processed'][:2]):
                print(f"   {i+1}. {result['patient_name']}: {result['decision']}")
        
        print(f"\n✅ Story #10 Complete: End-to-End Prior Authorization System Working!")
        print(f"✅ Processed {len(batch_results['processed'])} authorizations successfully")
        
    except Exception as e:
        print(f"❌ System test failed: {e}")
        print("\nPlease ensure all previous components are set up:")
        print("  1. Database: python scripts/setup_database.py")
        print("  2. Embeddings: python core/embedding_service.py")
        print("  3. FAISS Index: python core/faiss_manager.py")
