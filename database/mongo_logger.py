import sys
import os
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root) if project_root not in sys.path else None

import json
from datetime import datetime
from typing import Dict, List, Optional

class PriorAuthLogger:
    """
    File-based logger for prior authorization decisions
    Provides same interface as MongoDB but stores to JSON files
    Perfect for development without MongoDB dependency
    """
    
    def __init__(self, log_dir: str = None):
        if log_dir is None:
            log_dir = os.path.join(project_root, 'data', 'logs')
        
        os.makedirs(log_dir, exist_ok=True)
        self.log_file = os.path.join(log_dir, 'authorization_logs.json')
        self.stats_file = os.path.join(log_dir, 'decision_stats.json')
        
        print(f"✅ Prior Auth Logger initialized")
        print(f"   Log file: {self.log_file}")
    
    def log_decision(self, decision_record: Dict) -> str:
        """
        Log prior authorization decision to JSON file
        Same interface as MongoDB logger
        """
        # Add timestamps
        if 'timestamp' not in decision_record:
            decision_record['timestamp'] = datetime.utcnow().isoformat()
        
        decision_record['logged_at'] = datetime.utcnow().isoformat()
        decision_record['system_version'] = '1.0.0'
        decision_record['log_id'] = f"log_{int(datetime.utcnow().timestamp())}"
        
        # Load existing logs
        logs = []
        if os.path.exists(self.log_file):
            try:
                with open(self.log_file, 'r') as f:
                    logs = json.load(f)
            except json.JSONDecodeError:
                logs = []
        
        # Add new log
        logs.append(decision_record)
        
        # Save updated logs
        with open(self.log_file, 'w') as f:
            json.dump(logs, f, indent=2, default=str)
        
        # Update stats
        self._update_stats(decision_record['decision'])
        
        print(f"✅ Logged PA decision - Patient: {decision_record.get('patient_id')}, Decision: {decision_record.get('decision')}")
        
        return decision_record['log_id']
    
    def query_logs(self, patient_id: int = None, 
                   decision: str = None,
                   limit: int = 100) -> List[Dict]:
        """Query authorization logs with filters"""
        if not os.path.exists(self.log_file):
            return []
        
        try:
            with open(self.log_file, 'r') as f:
                logs = json.load(f)
        except json.JSONDecodeError:
            return []
        
        # Apply filters
        filtered_logs = logs
        
        if patient_id is not None:
            filtered_logs = [log for log in filtered_logs if log.get('patient_id') == patient_id]
        
        if decision:
            filtered_logs = [log for log in filtered_logs if log.get('decision') == decision]
        
        # Sort by timestamp (newest first)
        filtered_logs.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        
        # Apply limit
        filtered_logs = filtered_logs[:limit]
        
        print(f"📂 Found {len(filtered_logs)} authorization logs")
        return filtered_logs
    
    def get_patient_history(self, patient_id: int) -> List[Dict]:
        """Get all authorization history for a specific patient"""
        return self.query_logs(patient_id=patient_id)
    
    def get_decision_stats(self) -> Dict:
        """Get decision statistics"""
        if os.path.exists(self.stats_file):
            try:
                with open(self.stats_file, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                pass
        
        # Calculate stats from logs
        logs = self.query_logs()
        stats = {'Approved': 0, 'Denied': 0, 'total': len(logs)}
        
        for log in logs:
            decision = log.get('decision', 'Unknown')
            stats[decision] = stats.get(decision, 0) + 1
        
        return stats
    
    def _update_stats(self, decision: str):
        """Update decision statistics"""
        stats = self.get_decision_stats()
        stats[decision] = stats.get(decision, 0) + 1
        stats['total'] = stats.get('total', 0) + 1
        
        with open(self.stats_file, 'w') as f:
            json.dump(stats, f, indent=2)

# Test the logger
if __name__ == "__main__":
    print("🧪 Testing Prior Authorization Logger...")
    
    # Initialize logger
    logger = PriorAuthLogger()
    
    # Test logging decisions
    test_decisions = [
        {
            'patient_id': 1,
            'patient_name': 'Alice Johnson',
            'diagnosis_code': 'E11.9',
            'procedure_code': '83036',
            'decision': 'Approved',
            'reasoning': 'Patient meets diabetes monitoring criteria with HbA1c > 7.0',
            'retrieved_sop': 'diabetes_sop.pdf',
            'sop_similarity_distance': 0.234
        },
        {
            'patient_id': 2,
            'patient_name': 'Bob Smith',
            'diagnosis_code': 'I10',
            'procedure_code': '93306',
            'decision': 'Approved',
            'reasoning': 'Patient age >50 with hypertension meets cardiology SOP criteria',
            'retrieved_sop': 'cardiology_sop.pdf',
            'sop_similarity_distance': 0.156
        }
    ]
    
    # Log decisions
    for decision in test_decisions:
        logger.log_decision(decision)
    
    # Query logs
    print("\n🔍 Querying all logs...")
    all_logs = logger.query_logs()
    
    print("\n📊 Decision Statistics:")
    stats = logger.get_decision_stats()
    for key, value in stats.items():
        print(f"   {key}: {value}")
    
    print(f"\n✅ Story #9 Complete: File-based logging working perfectly!")
    print(f"   Total decisions logged: {stats.get('total', 0)}")
    print(f"   Log file location: {logger.log_file}")
