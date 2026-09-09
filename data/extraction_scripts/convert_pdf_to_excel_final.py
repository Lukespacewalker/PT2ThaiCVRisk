import pdfplumber
import pandas as pd
import unicodedata
import re
import os
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

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
    row_str = " ".join([clean_cell(c) for c in row if c])
    return any(kw in row_str for kw in ['ลำดับ', 'ชื่อ-สกุล', 'ชื่อ - สกุล', 'RIGHT EAR', 'Left Ear', 'Color'])

def is_data_row(row):
    if not row or len(row) < 2:
        return False
    c0 = clean_cell(row[0])
    c1 = clean_cell(row[1])
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
        "pages": [48, 49, 50],
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
        "pages": [57, 58, 59],
        "columns": ["ลำดับ", "ชื่อ-สกุล", "อายุ", "FBS (mg/dl)", "แปลผล FBS", "คำแนะนำ"]
    },
    {
        "name": "Lipid_Profile",
        "sheet_name": "Lipid_Profile",
        "pages": [62, 63, 64],
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
        "pages": [73, 74, 75],
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

dfs = {}

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
                    if is_header_row(cleaned):
                        continue
                    if is_data_row(cleaned):
                        if len(cleaned) > len(expected_cols):
                            cleaned = cleaned[:len(expected_cols)]
                        elif len(cleaned) < len(expected_cols):
                            cleaned = cleaned + [""] * (len(expected_cols) - len(cleaned))
                        extracted_rows.append(cleaned)
        
        df = pd.DataFrame(extracted_rows, columns=expected_cols)
        if "ลำดับ" in df.columns:
            num_seq = pd.to_numeric(df["ลำดับ"], errors='coerce')
            df["ลำดับ"] = num_seq.where(num_seq.notnull(), df["ลำดับ"])
            
        dfs[sheet] = df
        print(f"Section '{sheet:20s}': Extracted {len(df):3d} records.")

# Build Master Sheet by merging on ('ลำดับ', 'ชื่อ-สกุล', 'อายุ')
master_df = dfs["Physical_Exam"][["ลำดับ", "ชื่อ-สกุล", "อายุ", "ความดัน Systolic", "ความดัน Diastolic", "ชีพจร", "น้ำหนัก (kg)", "ส่วนสูง (cm)", "ค่า BMI", "แปลผล BMI"]].copy()

# Add key results from other sheets
def merge_into_master(master, df_source, cols_to_add, prefix=""):
    if df_source.empty:
        return master
    sub = df_source[["ลำดับ"] + cols_to_add].copy()
    if prefix:
        rename_map = {col: f"{prefix}_{col}" for col in cols_to_add}
        sub.rename(columns=rename_map, inplace=True)
    return pd.merge(master, sub, on="ลำดับ", how="left")

master_df = merge_into_master(master_df, dfs["Vision_Test"], ["สรุปผลการตรวจสายตา"], prefix="Vision")
master_df = merge_into_master(master_df, dfs["CBC"], ["Hb", "Hct", "WBC Count", "Platelet Count", "แปลผล CBC"], prefix="CBC")
master_df = merge_into_master(master_df, dfs["FBS_Sugar"], ["FBS (mg/dl)", "แปลผล FBS"], prefix="Diabetes")
master_df = merge_into_master(master_df, dfs["Lipid_Profile"], ["Total Cholesterol", "Triglyceride", "HDL-C", "LDL-C", "แปลผล Lipid Profile"], prefix="Lipid")
master_df = merge_into_master(master_df, dfs["Liver_Function"], ["SGOT (AST)", "SGPT (ALT)", "แปลผล Liver Function"], prefix="Liver")
master_df = merge_into_master(master_df, dfs["Uric_Acid"], ["Uric Acid (mg/dl)", "แปลผล Uric Acid"], prefix="Uric")
master_df = merge_into_master(master_df, dfs["Hepatitis_B"], ["HBsAg", "แปลผล HBsAg"], prefix="HepB")
master_df = merge_into_master(master_df, dfs["Urine_Analysis"], ["สรุปผล UA"], prefix="UA")
master_df = merge_into_master(master_df, dfs["Amphetamine_Drug"], ["Amphetamine in Urine"], prefix="Drug")
master_df = merge_into_master(master_df, dfs["Chest_XRay"], ["Chest X-Ray Result"], prefix="XRay")
master_df = merge_into_master(master_df, dfs["EKG"], ["EKG Result"], prefix="EKG")
master_df = merge_into_master(master_df, dfs["Occ_Vision"], ["สรุปผลตรวจสมรรถภาพสายตา"], prefix="OccVision")
master_df = merge_into_master(master_df, dfs["Audiogram"], ["สรุปผลการได้ยิน"], prefix="Audiogram")
master_df = merge_into_master(master_df, dfs["Spirometry"], ["สรุปผลตรวจสมรรถภาพปอด"], prefix="Spirometry")

# Export to Excel with styling
writer = pd.ExcelWriter(excel_path, engine='openpyxl')

# Write Master Sheet first
master_df.to_excel(writer, sheet_name="Master_Summary", index=False)

# Write individual test sheets
for sheet_name, df in dfs.items():
    df.to_excel(writer, sheet_name=sheet_name, index=False)

# Apply formatting using openpyxl
wb = writer.book

# Styling definitions
header_fill = PatternFill(start_color="1F4E79", end_color="1F4E79", fill_type="solid") # Dark navy blue
header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
data_font = Font(name="Calibri", size=10)
thin_border = Border(
    left=Side(style='thin', color='D9D9D9'),
    right=Side(style='thin', color='D9D9D9'),
    top=Side(style='thin', color='D9D9D9'),
    bottom=Side(style='thin', color='D9D9D9')
)

for sheet in wb.sheetnames:
    ws = wb[sheet]
    ws.views.sheetView[0].showGridLines = True
    
    # Format headers
    for cell in ws[1]:
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    
    ws.row_dimensions[1].height = 28
    
    # Format data rows & auto-adjust column width
    for col in ws.columns:
        max_len = 0
        col_letter = get_column_letter(col[0].column)
        for cell in col:
            if cell.row > 1:
                cell.font = data_font
                cell.border = thin_border
                # center short values/numbers, left align text
                val_str = str(cell.value or "")
                if len(val_str) <= 6 or val_str.replace('.', '').isdigit():
                    cell.alignment = Alignment(horizontal="center", vertical="center")
                else:
                    cell.alignment = Alignment(horizontal="left", vertical="center")
            
            val_len = len(str(cell.value or ''))
            if val_len > max_len:
                max_len = val_len
        
        ws.column_dimensions[col_letter].width = max(max_len + 4, 12)

wb.save(excel_path)
writer.close()

print(f"\nFINISHED SUCCESSFULLY! Exported {len(master_df)} master records and {len(dfs)} test sheets to:\n{os.path.abspath(excel_path)}")
