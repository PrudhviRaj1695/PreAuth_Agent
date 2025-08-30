import sys
import os
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root) if project_root not in sys.path else None

from typing import Dict, Optional
import re
import json

class ReasoningAgent:
    """
    LLM-powered reasoning agent that makes prior authorization decisions
    Takes patient data + SOP context and outputs decision + reasoning
    """
    
    def __init__(self, use_local_llm=True):
        self.use_local_llm = use_local_llm
        if not use_local_llm:
            # For future OpenAI integration
            pass
    
    def make_authorization_decision(self, patient_data: Dict, sop_context: str) -> Dict:
        """
        Core reasoning function: patient + SOP -> decision + reasoning
        
        Args:
            patient_data: Dictionary with patient information
            sop_context: Retrieved SOP text containing authorization rules
            
        Returns:
            Dictionary with 'decision' and 'reasoning' keys
        """
        if self.use_local_llm:
            return self._local_reasoning(patient_data, sop_context)
        else:
            return self._llm_reasoning(patient_data, sop_context)
    
    def _local_reasoning(self, patient_data: Dict, sop_context: str) -> Dict:
        """
        Local rule-based reasoning (simulates LLM logic)
        In production, replace with actual LLM calls
        """
        # Extract key patient information
        diagnosis_code = patient_data.get('diagnosis_code', '').upper()
        procedure_code = patient_data.get('procedure_code', '')
        age = patient_data.get('age', 0)
        gender = patient_data.get('gender', '').lower()
        lab_results = patient_data.get('lab_results', '').lower()
        previous_procedures = patient_data.get('previous_procedures', '')
        
        # Initialize decision
        decision = "Denied"
        reasoning_points = []
        
        # Parse SOP context for approval/denial criteria
        sop_upper = sop_context.upper()
        
        # Check diagnosis code matching
        if diagnosis_code in sop_upper or diagnosis_code[:3] in sop_upper:
            reasoning_points.append(f"✓ Diagnosis code {diagnosis_code} matches SOP criteria")
            decision = "Approved"
        else:
            reasoning_points.append(f"✗ Diagnosis code {diagnosis_code} not found in SOP criteria")
        
        # Check procedure code matching  
        if procedure_code in sop_upper:
            reasoning_points.append(f"✓ Procedure code {procedure_code} is covered in SOP")
            if decision != "Approved":
                decision = "Approved"
        else:
            reasoning_points.append(f"✗ Procedure code {procedure_code} not explicitly covered")
        
        # Age-based criteria
        if age > 50 and "AGE >50" in sop_upper:
            reasoning_points.append(f"✓ Patient age {age} meets >50 requirement")
            decision = "Approved"
        elif age < 35 and "AGE <35" in sop_upper and "DENIED" in sop_upper:
            reasoning_points.append(f"✗ Patient age {age} is <35, which is a denial criteria")
            decision = "Denied"
        
        # Lab results analysis
        if 'hba1c' in lab_results:
            hba1c_value = self._extract_lab_value(lab_results, 'hba1c')
            if hba1c_value:
                if hba1c_value > 7.0 and ">7.0" in sop_upper:
                    reasoning_points.append(f"✓ HbA1c {hba1c_value} > 7.0 supports authorization")
                    decision = "Approved"
                elif hba1c_value < 6.0 and "<6.0" in sop_upper and "DENIED" in sop_upper:
                    reasoning_points.append(f"✗ HbA1c {hba1c_value} < 6.0 indicates good control, authorization not needed")
                    decision = "Denied"
        
        # Hypertension check
        if 'i10' in diagnosis_code.lower() and 'hypertension' in sop_context.lower():
            reasoning_points.append("✓ Hypertension diagnosis (I10) matches cardiology SOP criteria")
            decision = "Approved"
        
        # Previous procedures consideration
        if previous_procedures and 'previous' in sop_context.lower():
            reasoning_points.append("✓ Previous procedures documented, supporting current request")
            decision = "Approved"
        
        # Final reasoning compilation
        reasoning = " | ".join(reasoning_points)
        
        # Add SOP reference
        sop_reference = self._extract_sop_reference(sop_context)
        if sop_reference:
            reasoning += f" | Applied SOP: {sop_reference}"
        
        return {
            'decision': decision,
            'reasoning': reasoning,
            'patient_id': patient_data.get('patient_id'),
            'procedure_code': procedure_code,
            'diagnosis_code': diagnosis_code
        }
    
    def _extract_lab_value(self, lab_results: str, lab_name: str) -> Optional[float]:
        """Extract numeric value from lab results string"""
        try:
            pattern = rf'{lab_name}:(\d+\.?\d*)'
            match = re.search(pattern, lab_results, re.IGNORECASE)
            if match:
                return float(match.group(1))
        except:
            pass
        return None
    
    def _extract_sop_reference(self, sop_context: str) -> str:
        """Extract SOP title/reference from context"""
        lines = sop_context.split('\n')
        for line in lines:
            if 'AUTHORIZATION' in line.upper() or 'GUIDELINES' in line.upper():
                return line.strip()
        return "Medical SOP"
    
    def _llm_reasoning(self, patient_data: Dict, sop_context: str) -> Dict:
        """
        Future: Use actual LLM (OpenAI, local model) for reasoning
        For now, returns placeholder
        """
        # Placeholder for LLM integration
        prompt = f"""
        You are a medical prior authorization specialist. Based on the patient data and SOP guidelines, 
        make an authorization decision.

        Patient Data:
        {json.dumps(patient_data, indent=2)}

        SOP Guidelines:
        {sop_context}

        Provide your decision (Approved/Denied) and detailed medical reasoning.
        """
        
        # TODO: Replace with actual LLM call
        return {
            'decision': 'Pending',
            'reasoning': 'LLM reasoning not yet implemented',
            'patient_id': patient_data.get('patient_id')
        }

# Test function
if __name__ == "__main__":
    print("🤖 Testing Reasoning Agent...")
    
    # Sample test data
    test_patient = {
        'patient_id': 1,
        'name': 'Alice Johnson',
        'age': 45,
        'gender': 'Female',
        'diagnosis_code': 'E11.9',  # Type 2 diabetes
        'procedure_code': '83036',   # HbA1c test
        'lab_results': 'HbA1c:8.2;Cholesterol:190',
        'previous_procedures': '99213;81001'
    }
    
    test_sop = """
    DIABETES MANAGEMENT PRIOR AUTHORIZATION
    
    HbA1c Testing (CPT 83036):
    - APPROVED if:
      * Diabetes diagnosis (E11.x codes)
      * HbA1c >7.0 requiring monitoring
      * New medication initiation
    - DENIED if:
      * HbA1c <6.0 with stable control
      * Testing within 30 days
    """
    
    # Test reasoning agent
    agent = ReasoningAgent(use_local_llm=True)
    result = agent.make_authorization_decision(test_patient, test_sop)
    
    print(f"✅ Decision: {result['decision']}")
    print(f"🔍 Reasoning: {result['reasoning']}")
    
    # Test different scenarios
    print("\n" + "="*50)
    print("🧪 Testing different scenarios...")
    
    # Scenario 2: Cardiology case
    cardiology_patient = {
        'patient_id': 2,
        'name': 'Bob Smith',
        'age': 60,
        'gender': 'Male',
        'diagnosis_code': 'I10',     # Hypertension
        'procedure_code': '93306',   # Echocardiogram
        'lab_results': 'BP:150/90;Cholesterol:220',
        'previous_procedures': '99214;93000'
    }
    
    cardiology_sop = """
    CARDIOLOGY PRIOR AUTHORIZATION GUIDELINES
    
    Echocardiogram (CPT 93306):
    - APPROVED if:
      * Patient age >50 with hypertension (ICD I10)
      * Previous cardiac procedures documented
      * Abnormal EKG findings
    - DENIED if:
      * Routine screening without symptoms
      * Patient age <35 with no cardiac history
    """
    
    cardiology_result = agent.make_authorization_decision(cardiology_patient, cardiology_sop)
    print(f"✅ Cardiology Decision: {cardiology_result['decision']}")
    print(f"🔍 Cardiology Reasoning: {cardiology_result['reasoning']}")
