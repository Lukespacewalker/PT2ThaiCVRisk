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

doc = fitz.open(pdf_path)

for page_num in range(len(doc)):
    page = doc[page_num]
    text = clean_text(page.get_text("text"))
    lines = [l.strip() for l in text.split('\n') if l.strip()]
    if not lines:
        continue
    
    title = lines[0]
    
    # check for employee rows: lines starting with numbers 1..74 followed by name or age
    # or check table lines
    digit_lines = [l for l in lines if re.match(r'^\d{1,2}\s+(นาย|นาง|น\.ส\.|นางสาว)', l)]
    
    is_abnormal = "รายชื่อพนักงานที่ผล" in title or "พนักงานที่ผล" in title
    abn_tag = " [ABNORMAL LIST]" if is_abnormal else " [MAIN LIST]"
    
    if len(lines) > 10:
        print(f"Page {page_num+1:3d} | Total Lines: {len(lines):3d} | Match Lines: {len(digit_lines):2d}{abn_tag} | Title: {title[:55]}")
