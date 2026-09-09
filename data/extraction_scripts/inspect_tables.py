import pdfplumber
import pandas as pd
import json

pdf_path = "ตรวจสุขภาพ รปภ. ปี 2569.pdf"

summary_sections = []

with pdfplumber.open(pdf_path) as pdf:
    for i, page in enumerate(pdf.pages):
        text = page.extract_text() or ""
        first_line = text.strip().split('\n')[0] if text.strip() else ""
        tables = page.extract_tables()
        if tables:
            for t_idx, table in enumerate(tables):
                if not table or len(table) == 0:
                    continue
                # get non-empty header candidate
                header = table[0]
                summary_sections.append({
                    "page": i + 1,
                    "title": first_line,
                    "table_index": t_idx + 1,
                    "rows": len(table),
                    "cols": len(header) if header else 0,
                    "sample_header": header[:8] if header else []
                })

print(f"Total tables found: {len(summary_sections)}")
for item in summary_sections:
    print(f"Page {item['page']:3d} | Rows: {item['rows']:3d} | Cols: {item['cols']:2d} | Title: {item['title'][:60]}")
    print(f"         Header sample: {item['sample_header']}")
