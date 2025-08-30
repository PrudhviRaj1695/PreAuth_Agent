import sys
import os
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root) if project_root not in sys.path else None

import pymongo
from datetime import datetime
from typing import Dict, List, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class MongoDBLogger:
    """
    MongoDB logger for prior authorization decisions
    Stores PA decision, reasoning, patient_id, procedure, retrieved rules, timestamp
    """
    
    def __init__(self, mongo_uri: str = None, db_name: str = 'prior_auth', collection_name: str = 'authorization_logs'):
        self.mongo_uri = mongo_uri or os.getenv('MONGODB_URL', 'mongodb://localhost:27017/')
        self.db_name = db_name
        self.collection_name = collection_name
        
        try:
            # Connect to MongoDB
            self.client = pymongo.MongoClient(self.mongo_uri, serverSelectionTimeoutMS=5000)
            
            # Test connection
            self.client.admin.command('ping')
            
            self.db = self.client[db_name]
            self.collection = self.db[collection_name]
            
            # Create indexes for better query performance
            self.collection.create_index("patient_id")
            self.collection.create_index("timestamp")
            self.collection.create_index("decision")
            
            print(f"✅ Connected to MongoDB: {self.mongo_uri}")
            print(f"   Database: {db_name}")
            print(f"   Collection: {collection_name}")
            
        except pymongo.errors.ServerSelectionTimeoutError:
            print(f"❌ Failed to connect to MongoDB at {self.mongo_uri}")
            print("   Make sure MongoDB is running locally or update MONGODB_URL in .env")
            self.client = None
            
        except Exception as e:
            print(f"❌ MongoDB connection error: {e}")
            self.client = None
    
    def log_decision(self, decision_record: Dict) -> str:
        """
        Log prior authorization decision to MongoDB
        
        Args:
            decision_record: Dictionary containing decision details
            
        Returns:
            MongoDB document ID as string
        """
        if not self.client:
            print("❌ MongoDB not connected, cannot log decision")
            return None
        
        # Ensure timestamp is included
        if 'timestamp' not in decision_record:
            decision_record['timestamp'] = datetime.utcnow()
        
        # Add metadata
        decision_record['logged_at'] = datetime.utcnow()
        decision_record['system_version'] = '1.0.0'
        
        try:
            # Insert document
            result = self.collection.insert_one(decision_record)
            doc_id = str(result.inserted_id)
            
            print(f"✅ Logged PA decision - Patient: {decision_record.get('patient_id')}, Decision: {decision_record.get('decision')}")
            print(f"   MongoDB ID: {doc_id}")
            
            return doc_id
            
        except Exception as e:
            print(f"❌ Error logging decision: {e}")
            return None
    
    def query_logs(self, patient_id: int = None, 
                   start_date: datetime = None, 
                   end_date: datetime = None,
                   decision: str = None,
                   limit: int = 100) -> List[Dict]:
        """
        Query authorization logs with filters
        
        Args:
            patient_id: Filter by patient ID
            start_date: Filter by start date
            end_date: Filter by end date  
            decision: Filter by decision (Approved/Denied)
            limit: Maximum number of records to return
            
        Returns:
            List of authorization log documents
        """
        if not self.client:
            print("❌ MongoDB not connected, cannot query logs")
            return []
        
        # Build query filter
        query_filter = {}
        
        if patient_id is not None:
            query_filter['patient_id'] = patient_id
            
        if decision:
            query_filter['decision'] = decision
            
        if start_date or end_date:
            timestamp_filter = {}
            if start_date:
                timestamp_filter['$gte'] = start_date
            if end_date:
                timestamp_filter['$lte'] = end_date
            query_filter['timestamp'] = timestamp_filter
        
        try:
            # Execute query
            cursor = self.collection.find(query_filter).sort("timestamp", -1).limit(limit)
            results = list(cursor)
            
            # Convert ObjectId to string for JSON serialization
            for result in results:
                result['_id'] = str(result['_id'])
            
            print(f"📂 Found {len(results)} authorization logs")
            return results
            
        except Exception as e:
            print(f"❌ Error querying logs: {e}")
            return []
    
    def get_patient_history(self, patient_id: int) -> List[Dict]:
        """Get all authorization history for a specific patient"""
        return self.query_logs(patient_id=patient_id)
    
    def get_recent_decisions(self, hours: int = 24) -> List[Dict]:
        """Get recent decisions within specified hours"""
        start_date = datetime.utcnow() - datetime.timedelta(hours=hours)
        return self.query_logs(start_date=start_date)
    
    def get_decision_stats(self) -> Dict:
        """Get aggregated statistics on decisions"""
        if not self.client:
            return {}
        
        try:
            pipeline = [
                {
                    '$group': {
                        '_id': '$decision',
                        'count': {'$sum': 1}
                    }
                }
            ]
            
            results = list(self.collection.aggregate(pipeline))
            stats = {result['_id']: result['count'] for result in results}
            
            # Add total count
            stats['total'] = sum(stats.values())
            
            print(f"📊 Decision Statistics: {stats}")
            return stats
            
        except Exception as e:
            print(f"❌ Error getting stats: {e}")
            return {}

# Test function
if __name__ == "__main__":
    print("🧪 Testing MongoDB Logger...")
    
    # Initialize logger
    mongo_logger = MongoDBLogger()
    
    if mongo_logger.client:
        # Test logging a decision
        sample_decision = {
            'patient_id': 1,
            'patient_name': 'Alice Johnson',
            'diagnosis_code': 'E11.9',
            'procedure_code': '83036',
            'decision': 'Approved',
            'reasoning': 'Patient meets diabetes monitoring criteria with HbA1c > 7.0',
            'retrieved_sop': 'diabetes_sop.pdf',
            'sop_similarity_distance': 0.234,
            'timestamp': datetime.utcnow()
        }
        
        # Log the decision
        doc_id = mongo_logger.log_decision(sample_decision)
        
        # Query logs for this patient
        print("\n🔍 Querying logs for patient 1...")
        patient_logs = mongo_logger.query_logs(patient_id=1)
        
        for log in patient_logs:
            print(f"   Decision: {log.get('decision')}")
            print(f"   Procedure: {log.get('procedure_code')}")
            print(f"   Timestamp: {log.get('timestamp')}")
            print(f"   Reasoning: {log.get('reasoning', '')[:50]}...")
        
        # Get decision statistics
        print("\n📊 Getting decision statistics...")
        stats = mongo_logger.get_decision_stats()
        
        print(f"\n✅ Story #9 Complete: MongoDB logging setup successful!")
        print(f"   Total decisions logged: {stats.get('total', 0)}")
        
    else:
        print("❌ MongoDB connection failed. Please ensure MongoDB is running.")
        print("   Install MongoDB locally or use MongoDB Atlas cloud service")
        print("   Update MONGODB_URL in .env file if needed")
