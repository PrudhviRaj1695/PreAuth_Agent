
import json
import numpy as np  # Add this line
from datetime import datetime
from typing import Optional, Dict
import sys
import os
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root) if project_root not in sys.path else None

import numpy as np
import faiss
from typing import Dict, List, Tuple
import pickle

class FAISSManager:
    """FAISS vector database manager for SOP semantic search"""
    
    def __init__(self, embedding_dim: int):
        self.embedding_dim = embedding_dim
        self.index = None
        self.document_map = {}  # Maps FAISS indices to document metadata
        
    def build_index(self, embeddings: np.ndarray, document_names: List[str] = None):
        """
        Create FAISS index and add embeddings
        Args:
            embeddings: numpy array of shape (n_docs, embedding_dim)
            document_names: list of document names corresponding to embeddings
        """
        if embeddings.shape[1] != self.embedding_dim:
            raise ValueError(f"Embedding dimension mismatch: expected {self.embedding_dim}, got {embeddings.shape[11]}")
        
        # Create L2 distance index for similarity search
        self.index = faiss.IndexFlatL2(self.embedding_dim)
        
        # Ensure embeddings are float32 (required by FAISS)
        embeddings_f32 = embeddings.astype('float32')
        
        # Add embeddings to index
        self.index.add(embeddings_f32)
        
        # Create document mapping
        if document_names:
            for i, doc_name in enumerate(document_names):
                self.document_map[i] = {
                    'name': doc_name,
                    'index': i
                }
        
        print(f"✅ FAISS index created with {self.index.ntotal} documents")
        print(f"   Embedding dimension: {self.embedding_dim}")
        print(f"   Index type: {type(self.index).__name__}")
        
    def search(self, query_embedding: np.ndarray, k: int = 5) -> Tuple[np.ndarray, np.ndarray, List[str]]:
        """
        Search FAISS index for most similar documents
        Returns: (distances, indices, document_names)
        """
        if self.index is None:
            raise ValueError("Index not initialized. Call build_index() first.")
            
        # Ensure query is 2D array with float32 dtype
        if query_embedding.ndim == 1:
            query_embedding = query_embedding.reshape(1, -1)
        query_embedding = query_embedding.astype('float32')
        
        # Search index
        distances, indices = self.index.search(query_embedding, k)
        
        # Get document names
        doc_names = []
        for idx in indices[0]:
            if idx in self.document_map:
                doc_names.append(self.document_map[idx]['name'])
            else:
                doc_names.append(f"Document_{idx}")
                
        return distances[0], indices[0], doc_names
    
    def save_index(self, index_path: str, metadata_path: str = None):
        """Save FAISS index and metadata to disk"""
        if self.index is None:
            raise ValueError("No index to save")
            
        # Create directory if needed
        os.makedirs(os.path.dirname(index_path), exist_ok=True)
        
        # Save FAISS index
        faiss.write_index(self.index, index_path)
        print(f"💾 Saved FAISS index to {index_path}")
        
        # Save document metadata
        if metadata_path is None:
            metadata_path = index_path.replace('.index', '_metadata.pkl')
            
        metadata = {
            'document_map': self.document_map,
            'embedding_dim': self.embedding_dim,
            'num_documents': self.index.ntotal
        }
        
        with open(metadata_path, 'wb') as f:
            pickle.dump(metadata, f)
        print(f"💾 Saved metadata to {metadata_path}")
        
    def load_index(self, index_path: str, metadata_path: str = None):
        """Load FAISS index and metadata from disk"""
        if not os.path.exists(index_path):
            raise FileNotFoundError(f"Index file not found: {index_path}")
            
        # Load FAISS index
        self.index = faiss.read_index(index_path)
        print(f"📂 Loaded FAISS index from {index_path}")
        print(f"   Documents in index: {self.index.ntotal}")
        
        # Load metadata
        if metadata_path is None:
            metadata_path = index_path.replace('.index', '_metadata.pkl')
            
        if os.path.exists(metadata_path):
            with open(metadata_path, 'rb') as f:
                metadata = pickle.load(f)
            
            self.document_map = metadata.get('document_map', {})
            self.embedding_dim = metadata.get('embedding_dim', self.embedding_dim)
            print(f"📂 Loaded metadata: {len(self.document_map)} document mappings")
        else:
            print(f"⚠️  Metadata file not found: {metadata_path}")

    def get_document_info(self, index: int) -> Dict:
        """Get document information by FAISS index"""
        return self.document_map.get(index, {'name': f'Unknown_Document_{index}', 'index': index})

# Integration function to build FAISS from embeddings
def build_faiss_from_embeddings(embeddings_path: str, faiss_save_path: str) -> FAISSManager:
    """
    Load embeddings and build FAISS index
    """
    # Load embeddings
    if not os.path.exists(embeddings_path):
        raise FileNotFoundError(f"Embeddings file not found: {embeddings_path}")
        
    data = np.load(embeddings_path, allow_pickle=True)
    embeddings_array = data['embeddings']
    filenames = data['filenames']
    metadata = data['metadata'].item()
    
    print(f"📂 Loaded {embeddings_array.shape[0]} embeddings of dimension {embeddings_array.shape[1]}")
    print(f"   Model: {metadata.get('model_name', 'unknown')}")
    
    # Initialize FAISS manager
    faiss_manager = FAISSManager(embedding_dim=embeddings_array.shape[1])
    
    # Build index
    faiss_manager.build_index(embeddings_array, document_names=list(filenames))
    
    # Save FAISS index
    faiss_manager.save_index(faiss_save_path)
    
    return faiss_manager

# Test and demonstration
if __name__ == "__main__":
    try:
        # Paths
        embeddings_path = os.path.join(project_root, 'data', 'embeddings', 'sop_embeddings.npz')
        faiss_dir = os.path.join(project_root, 'data', 'faiss_index')
        faiss_save_path = os.path.join(faiss_dir, 'sop_faiss.index')
        
        os.makedirs(faiss_dir, exist_ok=True)
        
        # Build FAISS index from embeddings
        print("🚀 Building FAISS index from SOP embeddings...")
        faiss_manager = build_faiss_from_embeddings(embeddings_path, faiss_save_path)
        
        # Test loading the saved index
        print("\n🔍 Testing FAISS index loading and search...")
        test_manager = FAISSManager(embedding_dim=384)  # Default MiniLM dimension
        test_manager.load_index(faiss_save_path)
        
        # Load embeddings for testing search
        data = np.load(embeddings_path, allow_pickle=True)
        embeddings_array = data['embeddings']
        filenames = data['filenames']
        
        # Test search with first embedding as query
        query_embedding = embeddings_array[0]
        distances, indices, doc_names = test_manager.search(query_embedding, k=3)
        
        print(f"\n🔍 Search results for query document: {filenames[0]}")
        for i, (dist, idx, doc_name) in enumerate(zip(distances, indices, doc_names)):
            print(f"  {i+1}. {doc_name} (distance: {dist:.4f})")
            
        # Test with a different query
        if len(embeddings_array) > 1:
            query_embedding2 = embeddings_array[1]
            distances2, indices2, doc_names2 = test_manager.search(query_embedding2, k=2)
            
            print(f"\n🔍 Search results for query document: {filenames[1]}")
            for i, (dist, idx, doc_name) in enumerate(zip(distances2, indices2, doc_names2)):
                print(f"  {i+1}. {doc_name} (distance: {dist:.4f})")
        
        print(f"\n✅ Story #5 Complete: FAISS vector store setup successful!")
        print(f"   Index path: {faiss_save_path}")
        print(f"   Documents indexed: {test_manager.index.ntotal}")
        print(f"   Ready for semantic SOP retrieval!")
        
    except FileNotFoundError as e:
        print(f"❌ File not found: {e}")
        print("   Please run 'python core/embedding_service.py' first to create embeddings")
    except Exception as e:
        print(f"❌ Error building FAISS index: {e}")
        import traceback
        traceback.print_exc()
