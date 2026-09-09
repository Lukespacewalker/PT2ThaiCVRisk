import pdfplumber
import pandas as pd
import unicodedata
import re
import os

pdf_path = "ตรวจสุขภาพ รปภ. ปี 2569.pdf"
excel_path = "ตรวจสุขภาพ_รปภ_ปี2569_extracted.xlsx"

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
    val = re.sub(r'\s+', ' ', val).strip()
    return val

def is_header_row(row):
    # Check if a row is a header row (e.g. contains 'ลำดับ', 'ชื่อ-สกุล', 'No.')
    row_str = " ".join([clean_cell(c) for c in row if c])
    return any(keyword in row_str for keyword in ['ลำดับ', 'ชื่อ-สกุล', 'ชื่อ - สกุล', 'RIGHT EAR', 'Left Ear', 'Color'])

def is_data_row(row):
    # A valid data row usually has a numeric ID in the first column or employee name in 2nd column
    if not row or len(row) < 2:
        return False
    c0 = clean_cell(row[0])
    c1 = clean_cell(row[1])
    # Check if c0 is a number or c1 starts with Mr./Ms. (นาย/นาง/นางสาว)
    if c0.isdigit():
        return True
    if any(c1.startswith(prefix) for prefix in ['นาย', 'นาง', 'น.ส.', 'นางสาว']):
        return True
    return False

sections_config = [
    {
        "name": "General_Physical",
        "sheet_name": "Physical_Exam",
        "pages": [12, 13, 14],
        "columns": ["ลำดับ", "ชื่อ-สกุล", "อายุ", "ความดัน Systolic", "ความดัน Diastolic", "แปลผลความดัน", "ชีพจร", "แปลผลชีพจร", "น้ำหนัก (kg)", "ส่วนสูง (cm)", "ค่า BMI", "แปลผล BMI"]
    },
    {
        "name": "Visual_Acuity",
        "sheet_name": "Vision_Test",
        "pages": [34, 35, 36],
        "columns": ["ลำดับ", "ชื่อ-สกุล", "อายุ", "ตาขวา (ระยะไกล)", "ตาซ้าย (ระยะไกล)", "แปลผลระยะไกล", "ตาขวา (ระยะใกล้)", "ตาซ้าย (ระยะใกล้)", "แปลผลระยะใกล้", "สายตาเอียง ตาขวา", "สายตาเอียง ตาซ้าย", "แปลผลสายตาเอียง", "ตาบอดสี", "แปลผลตาบอดสี", "สรุปผลการตรวจสายตา"]
    },
    {
        "name": "CBC",
        "sheet_name": "CBC",
        "pages": [47, 48, 49],
        "columns": ["ลำดับ", "ชื่อ-สกุล", "อายุ", "Hb", "Hct", "RBC Count", "WBC Count", "PMN/Neu", "Lym", "Mono", "Eos", "Baso", "Platelet Count", "Platelet Smear", "RBC Morphology", "แปลผล CBC", "คำแนะนำ"]
    },
    {
        "name": "Blood_Chem_Summary",
        "sheet_name": "Blood_Chem_Summary",
        "pages": [53, 54, 55],
        "columns": ["ลำดับ", "ชื่อ-สกุล", "อายุ", "FBS", "Cholesterol", "Triglyceride", "SGOT (AST)", "SGPT (ALT)", "Alk Phos", "BUN", "Creatinine", "Uric Acid", "สรุปผล Blood Chem", "คำแนะนำ"]
    },
    {
        "name": "FBS_Detail",
        "sheet_name": "FBS_Sugar",
        "pages": [57, 58, 59, 60],
        "columns": ["ลำดับ", "ชื่อ-สกุล", "อายุ", "FBS (mg/dl)", "แปลผล FBS", "คำแนะนำ"]
    },
    {
        "name": "Lipid_Profile",
        "sheet_name": "Lipid_Profile",
        "pages": [63, 64, 65],
        "columns": ["ลำดับ", "ชื่อ-สกุล", "อายุ", "Total Cholesterol", "Triglyceride", "HDL-C", "LDL-C", "แปลผล Lipid Profile", "คำแนะนำ"]
    },
    {
        "name": "Liver_Function",
        "sheet_name": "Liver_Function",
        "pages": [68, 69, 70],
        "columns": ["ลำดับ", "ชื่อ-สกุล", "อายุ", "SGOT (AST)", "SGPT (ALT)", "แปลผล Liver Function", "คำแนะนำ"]
    },
    {
        "name": "Uric_Acid",
        "sheet_name": "Uric_Acid",
        "pages": [73, 74, 75, 76],
        "columns": ["ลำดับ", "ชื่อ-สกุล", "อายุ", "Uric Acid (mg/dl)", "แปลผล Uric Acid", "คำแนะนำ"]
    },
    {
        "name": "Hepatitis_B",
        "sheet_name": "Hepatitis_B",
        "pages": [78, 79, 80],
        "columns": ["ลำดับ", "ชื่อ-สกุล", "อายุ", "HBsAg", "แปลผล HBsAg", "คำแนะนำ"]
    },
    {
        "name": "Urine_Analysis",
        "sheet_name": "Urine_Analysis",
        "pages": [83, 84, 85],
        "columns": ["ลำดับ", "ชื่อ-สกุล", "Color", "Appearance", "Sp.gr.", "pH", "Leucocytes", "Nitrite", "Protein", "Glucose", "Ketone", "Bilirubin", "Blood", "WBC", "RBC", "Bacteria", "Epithelial", "สรุปผล UA", "คำแนะนำ"]
    },
    {
        "name": "Amphetamine",
        "sheet_name": "Amphetamine_Drug",
        "pages": [87, 88, 89],
        "columns": ["ลำดับ", "ชื่อ-สกุล", "อายุ", "Amphetamine in Urine", "แปลผล Amphetamine", "คำแนะนำ"]
    },
    {
        "name": "Chest_XRay",
        "sheet_name": "Chest_XRay",
        "pages": [92, 93, 94],
        "columns": ["ลำดับ", "ชื่อ-สกุล", "อายุ", "Chest X-Ray Result", "รายละเอียดผลการตรวจ X-Ray"]
    },
    {
        "name": "EKG",
        "sheet_name": "EKG",
        "pages": [98, 99, 100],
        "columns": ["ลำดับ", "ชื่อ-สกุล", "อายุ", "EKG Result", "รายละเอียดผลการตรวจ EKG"]
    },
    {
        "name": "Occupational_Vision",
        "sheet_name": "Occ_Vision",
        "pages": [104],
        "columns": ["ลำดับ", "ชื่อ-สกุล", "อายุ", "การมองระยะไกล", "การมองระยะใกล้", "ความชัดลึก", "การแยกสี", "สมดุลแนวดิ่ง", "สมดุลแนวนอน", "ลานสายตา", "สรุปผลตรวจสมรรถภาพสายตา"]
    },
    {
        "name": "Audiogram",
        "sheet_name": "Audiogram",
        "pages": [107],
        "columns": [
            "ลำดับ", "ชื่อ-สกุล", "อายุ",
            "R_500", "R_1K", "R_2K", "R_PTA", "R_3K", "R_4K", "R_6K", "R_8K", "R_PTA_High", "R_Result",
            "L_500", "L_1K", "L_2K", "L_PTA", "L_3K", "L_4K", "L_6K", "L_8K", "L_PTA_High", "L_Result",
            "สรุปผลการได้ยิน"
        ]
    },
    {
        "name": "Spirometry",
        "sheet_name": "Spirometry",
        "pages": [110],
        "columns": ["ลำดับ", "ชื่อ-สกุล", "อายุ", "FVC (%)", "FEV1 (%)", "FEV1/FVC (%)", "สรุปผลตรวจสมรรถภาพปอด"]
    }
]

print("Starting PDF Extraction to Excel...")

writer = pd.ExcelWriter(excel_path, engine='openpyxl')

with pdfplumber.open(pdf_path) as pdf:
    for sec in sections_config:
        sheet = sec["sheet_name"]
        pages = sec["pages"]
        expected_cols = sec["columns"]
        
        extracted_rows = []
        for page_num in pages:
            page = pdf.pages[page_num - 1]
            tables = page.extract_tables()
            for t in tables:
                for row in t:
                    if not row:
                        continue
                    cleaned = [clean_cell(c) for c in row]
                    # Filter out header rows and empty rows
                    if is_header_row(cleaned):
                        continue
                    # Check if first cell is digit or employee name
                    if is_data_row(cleaned):
                        # Filter out empty trailing columns if table has extra empty cells
                        # Match length to expected columns or pad/crop
                        if len(cleaned) > len(expected_cols):
                            cleaned = cleaned[:len(expected_cols)]
                        elif len(cleaned) < len(expected_cols):
                            cleaned = cleaned + [""] * (len(expected_cols) - len(cleaned))
                        extracted_rows.append(cleaned)
        
        df = pd.DataFrame(extracted_rows, columns=expected_cols)
        
        # Clean numeric ID column if possible
        if "ลำดับ" in df.columns:
            numeric_seq = pd.to_numeric(df["ลำดับ"], errors='coerce')
            df["ลำดับ"] = numeric_seq.where(numeric_seq.notnull(), df["ลำดับ"])
            
        df.to_excel(writer, sheet_name=sheet, index=False)
        print(f"Sheet '{sheet:20s}': Extracted {len(df):3d} records across pages {pages}")

writer.close()
print(f"\nSUCCESS! File saved to {excel_path}")
