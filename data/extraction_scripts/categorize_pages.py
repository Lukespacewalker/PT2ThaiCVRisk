import pdfplumber
import pandas as pd
import unicodedata
import re

pdf_path = "ตรวจสุขภาพ รปภ. ปี 2569.pdf"

# Comprehensive Thai PUA character mapping
THAI_PUA_MAP = {
    '\uf700': 'ั', '\uf701': 'ิ', '\uf702': 'ี', '\uf703': 'ึ', '\uf704': 'ื',
    '\uf705': '่', '\uf706': '้', '\uf707': '๊', '\uf708': '๋', '\uf709': '์',
    '\uf70a': '่', '\uf70b': '้', '\uf70c': '๊', '\uf70d': '๋', '\uf70e': '์',
    '\uf70f': '็', '\uf710': 'ั', '\uf711': 'ิ', '\uf712': 'ี', '\uf713': 'ึ',
    '\uf714': 'ื', '\uf715': '็', '\uf718': 'ุ', '\uf719': 'ู', '\uf71a': 'ฺ'
}

def clean_text(val):
    if val is None:
        return ""
    val = str(val)
    for pua, std in THAI_PUA_MAP.items():
        val = val.replace(pua, std)
    val = unicodedata.normalize('NFC', val)
    # Replace multiple spaces / newlines cleanly
    val = re.sub(r'[\r\n]+', ' ', val)
    val = re.sub(r'\s+', ' ', val).strip()
    return val

# Identify categories by page headers
category_rules = [
    ("General_Physical", r"ผลการตรวจรางกายทั่วไปรายบุคคล|General Appearance"),
    ("Visual_Acuity", r"ผลการตรวจสายตาดวยระบบคอมพิวเตอร"),
    ("CBC", r"ผลการตรวจความสมบูรณของเม็ดเลือด|CBC|Complete Blood Count"),
    ("FBS_Diabetes", r"ผลการตรวจสารเคมีในเลือด.*น้ําตาลในเลือด|FBS|Blood Sugar"),
    ("Lipid_Profile", r"ผลการตรวจสารเคมีในเลือด.*ไขมันในเลือด|Lipid"),
    ("Liver_Function", r"ผลการตรวจสารเคมีในเลือด.*การทํางานของตับ|Liver"),
    ("Kidney_Function", r"ผลการตรวจสารเคมีในเลือด.*การทํางานของไต|Kidney"),
    ("Uric_Acid", r"ผลการตรวจสารเคมีในเลือด.*กรดยูริค|Uric"),
    ("Urine_Analysis", r"ผลการตรวจวิเคราะหปสสาวะ|Urine Analysis"),
    ("Amphetamine", r"ผลการตรวจสารเสพติดแอมเฟตามีน"),
    ("Chest_XRay", r"ผลการตรวจเอกซเรยปอดและทรวงอก|Chest X-Ray"),
    ("EKG", r"ผลการตรวจคลื่นไฟฟาหัวใจ|EKG"),
    ("Occupational_Vision", r"ผลการตรวจสมรรถภาพสายตาอาชีวอนามัย"),
    ("Audiogram", r"ผลการตรวจสมรรถภาพการไดยิน|Audiogram"),
    ("Spirometry", r"ผลการตรวจสมรรถภาพการทํางานของปอด|Spirometry"),
]

page_categories = {}

with pdfplumber.open(pdf_path) as pdf:
    for i, page in enumerate(pdf.pages):
        text = page.extract_text() or ""
        lines = [l.strip() for l in text.split('\n') if l.strip()]
        header_text = " ".join(lines[:3]) if lines else ""
        
        # Skip abnormal summary pages ("รายชื่อพนักงานที่ผล...") if we want main full lists
        is_abnormal_list = "รายชื่อพนักงานที่ผล" in header_text
        
        matched_cat = None
        for cat_name, pattern in category_rules:
            if re.search(pattern, header_text, re.IGNORECASE):
                matched_cat = cat_name
                break
        
        if matched_cat:
            page_categories[i + 1] = {
                "category": matched_cat,
                "is_abnormal": is_abnormal_list,
                "header": header_text[:80]
            }

print(f"Categorized {len(page_categories)} pages.")
for p, info in sorted(page_categories.items()):
    abn = " [ABNORMAL ONLY]" if info['is_abnormal'] else ""
    print(f"P.{p:3d} | {info['category']:20s}{abn} | {info['header']}")
