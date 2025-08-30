import sys
import os
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root) if project_root not in sys.path else None

import numpy as np
from typing import Optional, Dict
from core.faiss_manager import FAISSManager
from core.embedding_service import LocalEmbeddingService  
from core.reasoning_agent import ReasoningAgent
from core.pdf_extractor import extract_all_sop_texts
from core.patient_service import get_patient

class PriorAuthorizationSystem:
    """
    Complete RAG-based Prior Authorization System
    Combines patient data retrieval, SOP semantic search, and AI reasoning
    """
    
    def __init__(self):
        print("🚀 Initializing Prior Authorization System...")
        
        # Initialize embedding service
        self.embedding_service = LocalEmbeddingService()
        
        # Load embeddings data
        self.embeddings_path = os.path.join(project_root, 'data', 'embeddings', 'sop_embeddings.npz')
        self.sop_texts = None
        
        if os.path.exists(self.embeddings_path):
            self.embeddings_data = np.load(self.embeddings_path, allow_pickle=True)
            print(f"✅ Loaded embeddings: {len(self.embeddings_data['filenames'])} documents")
        else:
            print("❌ Embeddings not found. Please run 'python core/embedding_service.py' first")
            raise FileNotFoundError(f"Embeddings file not found: {self.embeddings_path}")
        
        # Initialize FAISS manager
        embedding_dim = self.embeddings_data['embeddings'].shape[1]
        self.faiss_manager = FAISSManager(embedding_dim=embedding_dim)
        
        # Load or build FAISS index
        self.faiss_index_path = os.path.join(project_root, 'data', 'faiss_index', 'sop_faiss.index')
        
        if os.path.exists(self.faiss_index_path):
            self.faiss_manager.load_index(self.faiss_index_path)
            print("✅ FAISS index loaded from disk")
        else:
            print("Building FAISS index...")
            embedding_vectors = self.embeddings_data['embeddings']
            document_names = list(self.embeddings_data['filenames'])
            self.faiss_manager.build_index(embedding_vectors, document_names)
            self.faiss_manager.save_index(self.faiss_index_path)
            print("✅ FAISS index built and saved")
        
        # Initialize reasoning agent
        self.reasoning_agent = ReasoningAgent(use_local_llm=True)
        
        # Load SOP texts for retrieval
        self.sop_texts = extract_all_sop_texts()
        if not self.sop_texts:
            print("⚠️  No SOP texts found. Using empty context.")
            self.sop_texts = {}
        
        print("✅ Prior Authorization System ready!")
    
    def process_prior_authorization(self, patient_id: int, k_neighbors: int = 1) -> Optional[Dict]:
        """
        Complete prior authorization workflow:
        1. Fetch patient data
        2. Create query embedding from patient context  
        3. Retrieve relevant SOP using FAISS
        4. Run reasoning agent with patient + SOP context
        5. Return structured decision
        """
        print(f"\n🔍 Processing prior authorization for patient {patient_id}...")
        
        # Step 1: Fetch patient data
        patient = get_patient(patient_id)
        if not patient:
            print(f"❌ Patient {patient_id} not found in database")
            return None
        
        print(f"📋 Patient: {patient['name']}, {patient['age']}y, {patient['diagnosis_code']}")
        
        # Step 2: Create query embedding from patient context
        query_context = f"diagnosis: {patient['diagnosis_code']} procedure: {patient['procedure_code']} age: {patient['age']}"
        
        # Add lab results if available
        if patient.get('lab_results'):
            query_context += f" labs: {patient['lab_results']}"
            
        query_embedding = self.embedding_service.create_embedding(query_context)
        print(f"🔍 Query context: {query_context}")
        
        # Step 3: Retrieve relevant SOP using FAISS
        try:
            distances, indices, doc_names = self.faiss_manager.search(query_embedding, k=k_neighbors)
            
            if not doc_names:
                print("❌ No matching SOP found")
                return None
            
            # Get the most relevant SOP
            best_sop_name = doc_names[0]
            best_distance = distances[0]
            
            print(f"📖 Retrieved SOP: {best_sop_name} (distance: {best_distance:.4f})")
            
            # Get SOP text content
            sop_text = self.sop_texts.get(best_sop_name, '')
            if not sop_text:
                print(f"⚠️  SOP text not found for {best_sop_name}")
                sop_text = "No SOP content available"
            
        except Exception as e:
            print(f"❌ Error in FAISS retrieval: {e}")
            return None
        
        # Step 4: Run reasoning agent
        try:
            decision_result = self.reasoning_agent.make_authorization_decision(patient, sop_text)
            
            print(f"🤖 Decision: {decision_result['decision']}")
            print(f"💭 Reasoning: {decision_result['reasoning'][:100]}...")
            
        except Exception as e:
            print(f"❌ Error in reasoning agent: {e}")
            return None
        
        # Step 5: Return structured result
        return {
            'patient_id': patient_id,
            'patient_name': patient['name'],
            'diagnosis_code': patient['diagnosis_code'],
            'procedure_code': patient['procedure_code'],
            'retrieved_sop': best_sop_name,
            'sop_similarity_distance': float(best_distance),
            'decision': decision_result['decision'],
            'reasoning': decision_result['reasoning'],
            'timestamp': None,  # Will be added in logging (Story #9)
            'status': 'completed'
        }

# Test and demonstration
if __name__ == "__main__":
    try:
        # Initialize the complete system
        pa_system = PriorAuthorizationSystem()
        
        print("\n" + "="*60)
        print("🧪 Testing Complete Prior Authorization System")
        print("="*60)
        
        # Test multiple patients
        test_patients = [1, 2, 3]
        
        for patient_id in test_patients:
            result = pa_system.process_prior_authorization(patient_id)
            
            if result:
                print(f"\n✅ AUTHORIZATION RESULT:")
                print(f"   Patient: {result['patient_name']} (ID: {result['patient_id']})")
                print(f"   Diagnosis: {result['diagnosis_code']}")
                print(f"   Procedure: {result['procedure_code']}")
                print(f"   Retrieved SOP: {result['retrieved_sop']}")
                print(f"   Decision: {result['decision']}")
                print(f"   Reasoning: {result['reasoning']}")
                print(f"   Similarity Score: {result['sop_similarity_distance']:.4f}")
            else:
                print(f"\n❌ Failed to process authorization for patient {patient_id}")
            
            print("-" * 40)
        
        print("\n✅ Story #8 Complete: FAISS retrieval connected to reasoning agent!")
        print("🎯 RAG pipeline working: Retrieval → Augmented → Generation")
        
    except Exception as e:
        print(f"❌ System initialization failed: {e}")
        print("\nMake sure you've run the previous steps:")
        print("  1. python core/embedding_service.py")
        print("  2. python core/faiss_manager.py") 
        print("  3. python scripts/setup_database.py")
