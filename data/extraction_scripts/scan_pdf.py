import pdfplumber
import fitz

pdf_path = "ตรวจสุขภาพ รปภ. ปี 2569.pdf"

doc = fitz.open(pdf_path)
print(f"Total pages: {len(doc)}")

with pdfplumber.open(pdf_path) as pdf:
    for i, page in enumerate(pdf.pages):
        text = page.extract_text() or ""
        tables = page.extract_tables()
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        
        # Look for pages with text or tables
        if tables or len(lines) > 5:
            print(f"Page {i+1}: {len(tables)} tables, {len(lines)} text lines")
            if lines:
                print(f"   First line: {lines[0]}")
                if len(lines) > 1:
                    print(f"   Second line: {lines[1]}")
