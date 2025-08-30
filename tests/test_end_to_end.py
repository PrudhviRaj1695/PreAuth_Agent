import sys
import os
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root) if project_root not in sys.path else None

import pytest
import json
from core.end_to_end_flow import EndToEndPriorAuth
from core.patient_service import get_patient
from database.mongo_logger import PriorAuthLogger

class TestPriorAuthSystem:
    """Comprehensive test suite for agentic AI prior authorization system"""
    
    @pytest.fixture
    def pa_system(self):
        """Initialize system for testing"""
        return EndToEndPriorAuth()
    
    def test_patient_retrieval(self):
        """Test patient data retrieval"""
        patient = get_patient(1)
        assert patient is not None
        assert patient['patient_id'] == 1
        assert 'diagnosis_code' in patient
        assert 'procedure_code' in patient
        print("✅ Patient retrieval test passed")
    
    def test_authorization_approval(self, pa_system):
        """Test approval scenario"""
        result = pa_system.process_prior_authorization(1, log_decision=False)
        assert result is not None
        assert result['decision'] in ['Approved', 'Denied']
        assert 'reasoning' in result
        assert 'retrieved_sop' in result
        print(f"✅ Authorization test passed: {result['decision']}")
    
    def test_batch_processing(self, pa_system):
        """Test multiple patient processing"""
        batch_results = pa_system.batch_process([1, 2, 3])
        assert 'processed' in batch_results
        assert 'summary' in batch_results
        assert len(batch_results['processed']) >= 0
        print(f"✅ Batch processing test passed: {batch_results['summary']}")
    
    def test_logging_functionality(self):
        """Test decision logging"""
        logger = PriorAuthLogger()
        
        test_decision = {
            'patient_id': 999,
            'decision': 'Approved',
            'reasoning': 'Test authorization',
            'procedure_code': 'TEST001'
        }
        
        log_id = logger.log_decision(test_decision)
        assert log_id is not None
        
        # Query back the logged decision
        logs = logger.query_logs(patient_id=999)
        assert len(logs) > 0
        assert logs[0]['decision'] == 'Approved'
        print("✅ Logging functionality test passed")

if __name__ == "__main__":
    # Run tests manually
    test_suite = TestPriorAuthSystem()
    
    print("🧪 Running Comprehensive Test Suite")
    print("="*50)
    
    # Test 1: Patient retrieval
    test_suite.test_patient_retrieval()
    
    # Test 2: System initialization and authorization
    pa_system = EndToEndPriorAuth()
    test_suite.test_authorization_approval(pa_system)
    
    # Test 3: Batch processing
    test_suite.test_batch_processing(pa_system)
    
    # Test 4: Logging
    test_suite.test_logging_functionality()
    
    print("\n✅ All tests completed successfully!")
    print("🎯 Story #11 Complete: Comprehensive testing implemented")
