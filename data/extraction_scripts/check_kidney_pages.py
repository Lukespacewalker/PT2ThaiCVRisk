import pdfplumber

pdf_path = "ตรวจสุขภาพ รปภ. ปี 2569.pdf"

with pdfplumber.open(pdf_path) as pdf:
    for page_num in range(77, 82):
        page = pdf.pages[page_num - 1]
        tables = page.extract_tables()
        text = (page.extract_text() or "").strip()
        first_line = text.split('\n')[0] if text else ""
        print(f"P.{page_num}: {first_line[:60]} | Tables: {len(tables)}")
        if tables:
            for idx, t in enumerate(tables):
                print(f"   Table {idx+1}: {len(t)} rows, row0={t[0][:5] if t else []}")
