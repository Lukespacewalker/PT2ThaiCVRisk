import pdfplumber
import unicodedata
import re
import json

pdf_path = "ตรวจสุขภาพ รปภ. ปี 2569.pdf"

THAI_PUA_MAP = {
    '\uf700': 'ั', '\uf701': 'ิ', '\uf702': 'ี', '\uf703': 'ึ', '\uf704': 'ื',
    '\uf705': '่', '\uf706': '้', '\uf707': '๊', '\uf708': '๋', '\uf709': '์',
    '\uf70a': '่', '\uf70b': '้', '\uf70c': '๊', '\uf70d': '๋', '\uf70e': '์',
    '\uf70f': '็', '\uf710': 'ั', '\uf711': 'ิ', '\uf712': 'ี', '\uf713': 'ึ',
    '\uf714': 'ื', '\uf715': '็', '\uf718': 'ุ', '\uf719': 'ู', '\uf71a': 'ฺ'
}

def clean_cell(val):
    if val is None:
        return ""
    val = str(val)
    for pua, std in THAI_PUA_MAP.items():
        val = val.replace(pua, std)
    val = unicodedata.normalize('NFC', val)
    val = re.sub(r'[\r\n]+', ' ', val)
    return re.sub(r'\s+', ' ', val).strip()

pages_to_check = [
    (12, "General Physical"),
    (34, "Visual Acuity"),
    (44, "CBC"),
    (53, "Blood Chem Summary"),
    (57, "FBS"),
    (63, "Lipid"),
    (68, "Liver"),
    (73, "Uric"),
    (83, "Urine Analysis"),
    (87, "Amphetamine"),
    (92, "Chest XRay"),
    (98, "EKG"),
    (104, "Occupational Vision"),
    (107, "Audiogram"),
    (110, "Spirometry"),
]

with pdfplumber.open(pdf_path) as pdf:
    for page_num, label in pages_to_check:
        page = pdf.pages[page_num - 1]
        tables = page.extract_tables()
        print(f"\n=========================================")
        print(f"Page {page_num}: {label} | Found {len(tables)} tables")
        print(f"=========================================")
        for t_idx, t in enumerate(tables):
            print(f"--- Table {t_idx+1} ({len(t)} rows x {len(t[0]) if t else 0} cols) ---")
            for row in t[:4]: # print first 4 rows
                cleaned_row = [clean_cell(c) for c in row]
                print(cleaned_row)
