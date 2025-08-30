import sys
import os
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root) if project_root not in sys.path else None

from PyPDF2 import PdfReader
import os

def extract_text_from_pdf(pdf_path: str) -> str:
    """
    Extract text content from PDF file using PyPDF2
    Returns concatenated text from all pages
    """
    try:
        reader = PdfReader(pdf_path)
        all_text = []
        
        for page_num, page in enumerate(reader.pages):
            text = page.extract_text()
            if text.strip():  # Only add non-empty text
                all_text.append(f"--- Page {page_num + 1} ---\n{text}")
        
        return '\n\n'.join(all_text)
    
    except Exception as e:
        print(f"Error extracting text from {pdf_path}: {e}")
        return ""

def extract_all_sop_texts() -> dict:
    """
    Extract text from all SOP PDFs in the data/sop_pdfs directory
    Returns dict with filename as key and extracted text as value
    """
    sop_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'sop_pdfs')
    sop_texts = {}
    
    if not os.path.exists(sop_dir):
        print(f"SOP directory not found: {sop_dir}")
        return sop_texts
    
    pdf_files = [f for f in os.listdir(sop_dir) if f.endswith('.pdf')]
    
    if not pdf_files:
        print(f"No PDF files found in {sop_dir}")
        return sop_texts
    
    for pdf_file in pdf_files:
        pdf_path = os.path.join(sop_dir, pdf_file)
        text = extract_text_from_pdf(pdf_path)
        if text:
            sop_texts[pdf_file] = text
            print(f"✅ Extracted {len(text)} characters from {pdf_file}")
        else:
            print(f"❌ Failed to extract text from {pdf_file}")
    
    return sop_texts

# Test extraction
if __name__ == "__main__":
    print("🔍 Extracting text from SOP PDFs...")
    sop_texts = extract_all_sop_texts()
    
    if sop_texts:
        print(f"\n✅ Successfully extracted text from {len(sop_texts)} PDF files:")
        for filename, text in sop_texts.items():
            print(f"\n--- {filename} ---")
            print(text[:300] + "..." if len(text) > 300 else text)
    else:
        print("❌ No SOP texts extracted. Please ensure PDF files exist in data/sop_pdfs/")
