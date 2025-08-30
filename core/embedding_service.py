import sys
import os
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root) if project_root not in sys.path else None

import numpy as np
from typing import Dict, List
from sentence_transformers import SentenceTransformer

class LocalEmbeddingService:
    """Local embedding service using Sentence Transformers"""
    
    def __init__(self, model_name='all-MiniLM-L6-v2'):
        """
        Initialize with a lightweight local model
        - all-MiniLM-L6-v2: 384 dimensions, fast, good quality
        - all-mpnet-base-v2: 768 dimensions, slower but better quality
        """
        print(f"🔄 Loading local embedding model: {model_name}")
        self.model = SentenceTransformer(model_name)
        self.model_name = model_name
        print(f"✅ Model loaded successfully")
    
    def create_embedding(self, text: str) -> np.ndarray:
        """Create embedding for single text"""
        if not text.strip():
            # Return zero vector for empty text
            return np.zeros(self.model.get_sentence_embedding_dimension(), dtype=np.float32)
        
        embedding = self.model.encode(text, convert_to_numpy=True)
        return embedding.astype(np.float32)
    
    def create_sop_embeddings(self, sop_texts: Dict[str, str]) -> Dict[str, np.ndarray]:
        """Create embeddings for all SOP texts"""
        embeddings = {}
        
        print("🔄 Creating local embeddings for SOP texts...")
        for filename, text in sop_texts.items():
            if text.strip():
                embedding = self.create_embedding(text)
                embeddings[filename] = embedding
                print(f"✅ Created embedding for {filename} (shape: {embedding.shape})")
            else:
                print(f"❌ Skipping empty text for {filename}")
        
        return embeddings
    
    def save_embeddings(self, embeddings: Dict[str, np.ndarray], save_path: str):
        """Save embeddings to disk with metadata"""
        if not embeddings:
            print("❌ No embeddings to save")
            return
        
        embeddings_data = {
            'filenames': list(embeddings.keys()),
            'embeddings': np.array(list(embeddings.values())),
            'metadata': {
                'model_name': self.model_name,
                'embedding_dim': list(embeddings.values())[0].shape[0],
                'num_documents': len(embeddings),
                'model_type': 'sentence-transformers'
            }
        }
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        
        np.savez_compressed(save_path, **embeddings_data)
        print(f"💾 Saved {len(embeddings)} embeddings to {save_path}")
        print(f"   Model: {self.model_name}")
        print(f"   Dimensions: {embeddings_data['metadata']['embedding_dim']}")
    
    def load_embeddings(self, load_path: str) -> Dict[str, np.ndarray]:
        """Load embeddings from disk"""
        if not os.path.exists(load_path):
            print(f"❌ Embedding file not found: {load_path}")
            return {}
        
        data = np.load(load_path, allow_pickle=True)
        embeddings = {}
        
        filenames = data['filenames']
        embedding_arrays = data['embeddings']
        metadata = data['metadata'].item()
        
        for i, filename in enumerate(filenames):
            embeddings[filename] = embedding_arrays[i]
        
        print(f"📂 Loaded {len(embeddings)} embeddings from {load_path}")
        print(f"   Model: {metadata.get('model_name', 'unknown')}")
        print(f"   Dimensions: {metadata.get('embedding_dim', 'unknown')}")
        
        return embeddings

# Test and demonstration
if __name__ == "__main__":
    try:
        # Try to import SOP extraction function
        from core.pdf_extractor import extract_all_sop_texts
        
        # Extract SOP texts from PDFs
        print("📄 Extracting text from SOP PDFs...")
        sop_texts = extract_all_sop_texts()
        
        if not sop_texts:
            # Use sample texts if no PDFs found
            print("📝 No PDFs found. Using sample SOP texts for demonstration...")
            sop_texts = {
                'cardiology_sop.pdf': """
                CARDIOLOGY PRIOR AUTHORIZATION GUIDELINES
                
                Echocardiogram (CPT 93306): APPROVED if patient age >50 with hypertension (ICD I10), 
                previous cardiac procedures documented, abnormal EKG findings. DENIED if routine screening 
                without symptoms or patient age <35 with no cardiac history.
                
                Cardiac Catheterization (CPT 93458): APPROVED if abnormal stress test results, chest pain 
                with risk factors, prior MI or stent placement. DENIED if no documented cardiac symptoms.
                """,
                'diabetes_sop.pdf': """
                DIABETES MANAGEMENT PRIOR AUTHORIZATION
                
                HbA1c Testing (CPT 83036): APPROVED if diabetes diagnosis (E11.x codes), HbA1c >7.0 
                requiring monitoring, new medication initiation. DENIED if HbA1c <6.0 with stable 
                control or testing within 30 days.
                
                Continuous Glucose Monitor (CPT 95250): APPROVED if Type 1 diabetes, Type 2 with 
                HbA1c >8.0, frequent hypoglycemic episodes. DENIED if well-controlled diabetes.
                """,
                'general_procedures_sop.pdf': """
                GENERAL PROCEDURES AUTHORIZATION
                
                Office Visits (99214): APPROVED if established patient with chronic conditions, 
                follow-up for abnormal lab results, medication management required. DENIED if 
                routine annual physical or no medical necessity documented.
                
                Laboratory Tests: APPROVED if age >40 annual screening, chronic disease monitoring, 
                abnormal previous results. DENIED if excessive frequency without indication.
                """
            }
        
        # Create local embedding service
        embedding_service = LocalEmbeddingService(model_name='all-MiniLM-L6-v2')
        
        # Generate embeddings
        embeddings = embedding_service.create_sop_embeddings(sop_texts)
        
        if embeddings:
            # Save embeddings
            embeddings_dir = os.path.join(project_root, 'data', 'embeddings')
            save_path = os.path.join(embeddings_dir, 'sop_embeddings.npz')
            embedding_service.save_embeddings(embeddings, save_path)
            
            print(f"\n✅ Story #4 Complete: Created LOCAL embeddings for {len(embeddings)} SOP documents")
            print(f"   Using model: {embedding_service.model_name}")
            print(f"   Embedding dimension: {list(embeddings.values())[0].shape[0]}")
            print(f"   Saved to: {save_path}")
            
            # Test loading embeddings
            print("\n🔍 Testing embedding loading...")
            loaded_embeddings = embedding_service.load_embeddings(save_path)
            print(f"✅ Successfully loaded {len(loaded_embeddings)} embeddings")
        else:
            print("❌ No embeddings created")
            
    except Exception as e:
        print(f"❌ Error in embedding generation: {e}")
        import traceback
        traceback.print_exc()
