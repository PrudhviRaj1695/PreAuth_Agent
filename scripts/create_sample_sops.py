import sys
import os
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root) if project_root not in sys.path else None

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer

def create_sop_pdfs():
    """Create sample SOP PDF files using ReportLab"""
    sop_dir = os.path.join(project_root, 'data', 'sop_pdfs')
    os.makedirs(sop_dir, exist_ok=True)
    
    # SOP content definitions
    sops = {
        'cardiology_sop.pdf': {
            'title': 'CARDIOLOGY PRIOR AUTHORIZATION GUIDELINES',
            'content': [
                'Echocardiogram (CPT 93306):',
                '- APPROVED if:',
                '  * Patient age >50 with hypertension (ICD I10)',
                '  * Previous cardiac procedures documented',
                '  * Abnormal EKG findings',
                '  * Heart failure symptoms present',
                '- DENIED if:',
                '  * Routine screening without symptoms',
                '  * Patient age <35 with no cardiac history',
                '  * Recent normal echo within 6 months',
                '',
                'Cardiac Catheterization (CPT 93458):',
                '- APPROVED if:',
                '  * Abnormal stress test results',
                '  * Chest pain with risk factors',
                '  * Prior MI or stent placement',
                '  * Acute coronary syndrome',
                '- DENIED if:',
                '  * No documented cardiac symptoms',
                '  * Recent normal cardiac imaging',
                '  * Low-risk patient profile'
            ]
        },
        
        'diabetes_sop.pdf': {
            'title': 'DIABETES MANAGEMENT PRIOR AUTHORIZATION',
            'content': [
                'HbA1c Testing (CPT 83036):',
                '- APPROVED if:',
                '  * Diabetes diagnosis (E11.x codes)',
                '  * HbA1c >7.0 requiring monitoring',
                '  * New medication initiation',
                '  * Quarterly monitoring for poor control',
                '- DENIED if:',
                '  * HbA1c <6.0 with stable control',
                '  * Testing within 30 days',
                '  * No diabetes diagnosis',
                '',
                'Continuous Glucose Monitor (CPT 95250):',
                '- APPROVED if:',
                '  * Type 1 diabetes',
                '  * Type 2 with HbA1c >8.0',
                '  * Frequent hypoglycemic episodes',
                '  * Multiple daily insulin injections',
                '- DENIED if:',
                '  * Well-controlled diabetes (HbA1c <7.0)',
                '  * No documented glucose variability',
                '  * Diet-controlled diabetes only'
            ]
        },
        
        'general_procedures_sop.pdf': {
            'title': 'GENERAL PROCEDURES AUTHORIZATION',
            'content': [
                'Office Visits (CPT 99214):',
                '- APPROVED if:',
                '  * Established patient with chronic conditions',
                '  * Follow-up for abnormal lab results',
                '  * Medication management required',
                '  * Multiple diagnoses requiring evaluation',
                '- DENIED if:',
                '  * Routine annual physical (use 99395)',
                '  * No medical necessity documented',
                '  * Simple prescription refills',
                '',
                'Laboratory Tests:',
                '- APPROVED if:',
                '  * Age >40 annual screening',
                '  * Chronic disease monitoring',
                '  * Abnormal previous results',
                '  * Medication monitoring requirements',
                '- DENIED if:',
                '  * Excessive frequency without indication',
                '  * Screening in low-risk patients',
                '  * Duplicate recent testing'
            ]
        }
    }
    
    # Create PDFs
    for filename, sop_data in sops.items():
        filepath = os.path.join(sop_dir, filename)
        
        # Create canvas
        c = canvas.Canvas(filepath, pagesize=letter)
        width, height = letter
        
        # Title
        c.setFont("Helvetica-Bold", 16)
        c.drawString(50, height - 50, sop_data['title'])
        
        # Content
        c.setFont("Helvetica", 12)
        y_position = height - 100
        
        for line in sop_data['content']:
            if y_position < 50:  # New page if needed
                c.showPage()
                y_position = height - 50
                c.setFont("Helvetica", 12)
            
            c.drawString(50, y_position, line)
            y_position -= 20
        
        c.save()
        print(f"✅ Created {filepath}")

if __name__ == "__main__":
    create_sop_pdfs()
