import pandas as pd

excel_path = "ตรวจสุขภาพ_รปภ_ปี2569_extracted.xlsx"

for sheet in ["FBS_Sugar", "Lipid_Profile", "Liver_Function", "Hepatitis_B", "Uric_Acid"]:
    df = pd.read_excel(excel_path, sheet_name=sheet)
    print(f"\nSheet [{sheet}]: Columns = {df.columns.tolist()}")
    res_cols = [c for c in df.columns if 'แปลผล' in c]
    if res_cols:
        col = res_cols[0]
        print(f"Unique values in [{col}]:")
        print(df[col].value_counts().to_dict())
