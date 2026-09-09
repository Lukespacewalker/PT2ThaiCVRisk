import fitz
import unicodedata
import re

pdf_path = "ตรวจสุขภาพ รปภ. ปี 2569.pdf"

THAI_PUA_MAP = {
    '\uf700': 'ั', '\uf701': 'ิ', '\uf702': 'ี', '\uf703': 'ึ', '\uf704': 'ื',
    '\uf705': '่', '\uf706': '้', '\uf707': '๊', '\uf708': '๋', '\uf709': '์',
    '\uf70a': '่', '\uf70b': '้', '\uf70c': '๊', '\uf70d': '๋', '\uf70e': '์',
    '\uf70f': '็', '\uf710': 'ั', '\uf711': 'ิ', '\uf712': 'ี', '\uf713': 'ึ',
    '\uf714': 'ื', '\uf715': '็', '\uf718': 'ุ', '\uf719': 'ู', '\uf71a': 'ฺ'
}

def clean_text(val):
    if not val:
        return ""
    for pua, std in THAI_PUA_MAP.items():
        val = val.replace(pua, std)
    return unicodedata.normalize('NFC', val)

category_rules = [
    ("General_Physical", r"ผลการตรวจร่างกายทั่วไปรายบุคคล|General Appearance"),
    ("BP_Detail", r"ผลการตรวจร่างกายทั่วไปรายบุคคล \(ความดันโลหิต"),
    ("Pulse_Detail", r"ผลการตรวจร่างกายทั่วไปรายบุคคล \(ชีพจร"),
    ("BMI_Detail", r"ผลการตรวจร่างกายทั่วไปรายบุคคล \(ดัชนีมวลกาย"),
    ("Visual_Acuity", r"ผลการตรวจสายตาด้วยระบบคอมพิวเตอร์"),
    ("CBC", r"ผลการตรวจความสมบูรณ์ของเม็ดเลือด|CBC|Complete Blood Count"),
    ("FBS_Diabetes", r"ผลการตรวจสารเคมีในเลือด.*น้ำตาลในเลือด|FBS|Blood Sugar"),
    ("Lipid_Profile", r"ผลการตรวจสารเคมีในเลือด.*ไขมันในเลือด|Lipid"),
    ("Liver_Function", r"ผลการตรวจสารเคมีในเลือด.*การทำงานของตับ|Liver"),
    ("Kidney_Function", r"ผลการตรวจสารเคมีในเลือด.*การทำงานของไต|Kidney"),
    ("Uric_Acid", r"ผลการตรวจสารเคมีในเลือด.*กรดยูริค|Uric"),
    ("Urine_Analysis", r"ผลการตรวจวิเคราะห์ปัสสาวะ|Urine Analysis"),
    ("Amphetamine", r"ผลการตรวจสารเสพติดแอมเฟตามีน"),
    ("Chest_XRay", r"ผลการตรวจเอกซเรย์ปอดและทรวงอก|Chest X-Ray"),
    ("EKG", r"ผลการตรวจคลื่นไฟฟ้าหัวใจ|EKG"),
    ("Occupational_Vision", r"ผลการตรวจสมรรถภาพสายตาอาชีวอนามัย"),
    ("Audiogram", r"ผลการตรวจสมรรถภาพการได้ยิน|Audiogram"),
    ("Spirometry", r"ผลการตรวจสมรรถภาพการทำงานของปอด|Spirometry"),
]

doc = fitz.open(pdf_path)
page_categories = {}

for i in range(len(doc)):
    page = doc[i]
    raw_text = clean_text(page.get_text("text"))
    lines = [l.strip() for l in raw_text.split('\n') if l.strip()]
    header_text = " ".join(lines[:3]) if lines else ""
    
    is_abnormal_list = "รายชื่อพนักงานที่ผล" in header_text or "พนักงานที่ผล" in header_text
    
    matched_cat = None
    for cat_name, pattern in category_rules:
        if re.search(pattern, header_text, re.IGNORECASE):
            matched_cat = cat_name
            break
    
    if matched_cat:
        page_categories[i + 1] = {
            "category": matched_cat,
            "is_abnormal": is_abnormal_list,
            "header": header_text[:70]
        }

print(f"Categorized {len(page_categories)} pages out of {len(doc)}.")
for p, info in sorted(page_categories.items()):
    abn = " [ABNORMAL]" if info['is_abnormal'] else " [MAIN]"
    print(f"P.{p:3d} | {info['category']:20s}{abn} | {info['header']}")
