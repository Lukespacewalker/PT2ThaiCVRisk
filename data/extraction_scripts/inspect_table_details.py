import pdfplumber

pdf_path = "ตรวจสุขภาพ รปภ. ปี 2569.pdf"

with pdfplumber.open(pdf_path) as pdf:
    for page_num in range(6, 115):
        page = pdf.pages[page_num - 1]
        text_lines = [l.strip() for l in (page.extract_text() or "").split("\n") if l.strip()]
        title = text_lines[0] if text_lines else "No Text"
        tables = page.extract_tables()
        if tables:
            for idx, table in enumerate(tables):
                header = table[0] if len(table) > 0 else []
                # print non-empty header entries
                clean_header = [c.replace('\n', ' ') for c in header if c] if header else []
                print(f"P.{page_num} | Title: {title[:50]} | Rows: {len(table)} | Cols: {len(header)} | Header: {clean_header[:5]}")
