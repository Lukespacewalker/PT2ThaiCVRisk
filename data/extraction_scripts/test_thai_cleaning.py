import pdfplumber
import fitz
import unicodedata

pdf_path = "ตรวจสุขภาพ รปภ. ปี 2569.pdf"

# Test map for Thai PUA characters commonly found in Thai PDF fonts
THAI_PUA_MAP = {
    '\uf700': 'ั', '\uf701': 'ิ', '\uf702': 'ี', '\uf703': 'ึ', '\uf704': 'ื',
    '\uf705': '่', '\uf706': '้', '\uf707': '๊', '\uf708': '๋', '\uf709': '์',
    '\uf70a': '่', '\uf70b': '้', '\uf70c': '๊', '\uf70d': '๋', '\uf70e': '์',
    '\uf70f': '็', '\uf710': 'ั', '\uf711': 'ิ', '\uf712': 'ี', '\uf713': 'ึ',
    '\uf714': 'ื', '\uf715': '็', '\uf718': 'ุ', '\uf719': 'ู', '\uf71a': 'ฺ'
}

def clean_thai_text(text):
    if not text:
        return ""
    for pua, std in THAI_PUA_MAP.items():
        text = text.replace(pua, std)
    return unicodedata.normalize('NFKC', text)

with pdfplumber.open(pdf_path) as pdf:
    page = pdf.pages[11] # Page 12
    table = page.extract_table()
    print("Raw sample row:")
    print(table[0])
    print(table[1])
    print("\nCleaned sample row:")
    print([clean_thai_text(c) for c in table[0]])
    print([clean_thai_text(c) for c in table[1]])
