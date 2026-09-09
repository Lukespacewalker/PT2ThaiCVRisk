import sys
import pdfplumber
import fitz # PyMuPDF
import json

pdf_path = "ตรวจสุขภาพ รปภ. ปี 2569.pdf"

print("--- Inspecting with PyMuPDF ---")
doc = fitz.open(pdf_path)
print(f"Total pages: {len(doc)}")

for i in range(min(5, len(doc))):
    page = doc[i]
    text = page.get_text("text")
    print(f"--- Page {i+1} Sample Text (first 500 chars) ---")
    print(text[:500])

print("\n--- Inspecting Tables with pdfplumber ---")
with pdfplumber.open(pdf_path) as pdf:
    for i, page in enumerate(pdf.pages[:3]):
        tables = page.extract_tables()
        print(f"Page {i+1}: Found {len(tables)} tables")
        for t_idx, table in enumerate(tables):
            print(f"  Table {t_idx+1} (Rows: {len(table)}):")
            for row_idx, row in enumerate(table[:5]): # show first 5 rows
                print(f"    Row {row_idx}: {row}")
