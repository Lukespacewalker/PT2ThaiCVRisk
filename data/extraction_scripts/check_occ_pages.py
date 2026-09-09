import pdfplumber

pdf_path = "ตรวจสุขภาพ รปภ. ปี 2569.pdf"

with pdfplumber.open(pdf_path) as pdf:
    for p in [104, 105, 107, 108, 110, 111]:
        page = pdf.pages[p - 1]
        tables = page.extract_tables()
        text = page.extract_text() or ""
        first_line = text.strip().split('\n')[0] if text.strip() else ""
        print(f"Page {p:3d}: Title='{first_line}' | Tables={len(tables)}")
        for idx, t in enumerate(tables):
            digit_rows = [r for r in t if r and r[0] and str(r[0]).strip().isdigit()]
            print(f"   Table {idx+1}: total rows={len(t)}, digit rows={len(digit_rows)}")
