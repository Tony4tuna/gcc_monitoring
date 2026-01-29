#!/usr/bin/env python3
"""Quick test: Generate PDF for ticket #33 and check page count"""

from core.ticket_document import generate_ticket_pdf
import os

try:
    print("Generating PDF for ticket #33...")
    pdf_path, pdf_bytes = generate_ticket_pdf(33)
    print(f"✓ PDF generated: {pdf_path}")
    print(f"✓ PDF size: {len(pdf_bytes)} bytes")
    
    # Check if file exists
    if os.path.exists(pdf_path):
        file_size = os.path.getsize(pdf_path)
        print(f"✓ File verified: {file_size} bytes")
    
    # Try to count pages using PyPDF2 if available
    try:
        from PyPDF2 import PdfReader
        with open(pdf_path, 'rb') as f:
            reader = PdfReader(f)
            page_count = len(reader.pages)
            print(f"✓ Page count: {page_count}")
    except ImportError:
        print("⚠ PyPDF2 not installed (can't auto-detect page count)")
    except Exception as e:
        print(f"⚠ Error reading PDF: {e}")
    
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
