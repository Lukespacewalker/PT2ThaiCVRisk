import pdfplumber

pdf_path = "ตรวจสุขภาพ รปภ. ปี 2569.pdf"

with pdfplumber.open(pdf_path) as pdf:
    for page_num, page in enumerate(pdf.pages, 1):
        tables = page.extract_tables()
        if not tables:
            continue
        text = (page.extract_text() or "").strip()
        title = text.split('\n')[0] if text else ""
        
        # count digit rows across tables in page
        digit_count = 0
        for t in tables:
            for r in t:
                if r and r[0] and str(r[0]).strip().isdigit():
                    digit_count += 1
        
        if digit_count > 0:
            is_abnormal = "รายชื่อพนักงานที่ผล" in title or "พนักงานที่ผล" in title
            abn_tag = " [ABNORMAL LIST]" if is_abnormal else " [DATA PAGE]"
            print(f"Page {page_num:3d} | Digit Rows: {digit_count:2d}{abn_tag} | Title: {title[:55]}")
