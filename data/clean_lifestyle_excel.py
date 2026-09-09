import pandas as pd
import unicodedata
import re

df_health = pd.read_excel('data/ตรวจสุขภาพ_รปภ_ปี2569_extracted.xlsx')
df_life_raw = pd.read_excel('data/ประวัติดื่มเหล้า บุหรี่ รปภ. ปี 2569 ปท.2.xlsx', sheet_name='27.08.69', header=None)
df_life = df_life_raw.iloc[5:80].copy()

def clean_name(n):
    if not isinstance(n, str): return ''
    n = unicodedata.normalize('NFKD', n)
    n = n.replace('\u0e4d\u0e32', '\u0e33')
    n = n.replace('ปืึน', 'ปิ่น').replace('ปัืน', 'ปั้น')
    n = re.sub(r'^(นาย|น\.ส\.|นางสาว|นาง|ส\.ต\.|ส\.ต|พลฯ|พล|ด\.ต\.|ร\.ต\.ท\.|ร\.ต\.ต\.)\s*', '', n)
    n = re.sub(r'\s+', '', n)
    return n

def split_name(full):
    if not isinstance(full, str): return '', '', ''
    s = full.strip()
    title = ''
    m = re.match(r'^(นาย|น\.ส\.|นางสาว|นาง|ส\.ต\.|ส\.ต|พลฯ|พล|ด\.ต\.|ร\.ต\.ท\.|ร\.ต\.ต\.)\s*', s)
    if m:
        title = m.group(1).strip()
        s = s[m.end():].strip()
    parts = s.split()
    if len(parts) == 1:
        fname = parts[0]
        lname = ''
    else:
        fname = parts[0]
        lname = ' '.join(parts[1:])
    return title, fname, lname

MANUAL_ALIAS_REV = {
    'สมเกียรติสุขตะพงษ์': 'สมเกียร์ติ์สุขตะพงษ์',
    'อนุชิตศิริมงคล': 'อนุชิดศิริมงคล',
    'ธนวัฒน์ไตรรงค์': 'ธรวัฒน์ไตรรงค์',
    'วัชริตทรงวรรณะ': 'วัชริศทรงวรรณะ',
    'ประสิทธ์หากวี': 'ประสิทธิ์หากวี',
    'สมบัติจิ๋วศรีสวัสดิ': 'สมบัติจิ๋วศรีสวัสดิ์',
    'เฉลาดวงสุวรรณ': 'เฉลาดวงสุวรรณ์',
    'อิศราปราบพาน': 'อิศราปราบพาล',
    'อิทธิ์พงษ์วิลัยทอง': 'อิทธิ์พงศ์วิลัยทอง',
    'พงศ์สรรค์บรรณโต': 'พงศ์สรรค์บรรพโต',
}

health_lookup = {}
for idx, row in df_health.iterrows():
    c = clean_name(row['ชื่อ-สกุล'])
    health_lookup[c] = {
        'health_order': row['ลำดับ'],
        'health_name': row['ชื่อ-สกุล'],
        'age': row.get('อายุ'),
        'sbp': row.get('ความดัน Systolic'),
        'dbp': row.get('ความดัน Diastolic'),
        'fbs': row.get('Diabetes_FBS (mg/dl)'),
        'chol': row.get('Lipid_Total Cholesterol'),
    }

cleaned_rows = []
for idx, row in df_life.iterrows():
    no = int(row[0])
    bv = str(row[1]).strip() if pd.notna(row[1]) else ''
    orig_name = str(row[2]).strip()
    title, fname, lname = split_name(orig_name)
    c_name = clean_name(orig_name)
    
    # smoking
    c_smoke = bool(pd.notna(row[3]) and '/' in str(row[3]))
    v_smoke = bool(pd.notna(row[7]) and '/' in str(row[7]))
    smoking = 1 if (c_smoke or v_smoke) else 0
    smoke_label = 'สูบบุหรี่' if smoking == 1 else 'ไม่สูบ'
    
    # alcohol
    alcohol = 1 if (pd.notna(row[9]) and '/' in str(row[9])) else 0
    alc_label = 'ดื่มสุรา' if alcohol == 1 else 'ไม่ดื่ม'
    
    # match with health
    target_c = MANUAL_ALIAS_REV.get(c_name, c_name)
    h_match = health_lookup.get(target_c, None)
    
    cleaned_rows.append({
        'ลำดับ_สำรวจ': no,
        'จุดประจำการ_BV': bv,
        'คำนำหน้า': title,
        'ชื่อ': fname,
        'นามสกุล': lname,
        'ชื่อ_สกุล_เดิม': orig_name,
        'สูบบุหรี่มวน_ยาเส้น': 'สูบ' if c_smoke else 'ไม่สูบ',
        'สูบบุหรี่ไฟฟ้า': 'สูบ' if v_smoke else 'ไม่สูบ',
        'สถานะการสูบบุหรี่': smoke_label,
        'สถานะการดื่มสุรา': alc_label,
        'พบข้อมูลตรวจสุขภาพ': 'พบ' if h_match else 'ไม่พบ',
        'ลำดับ_ตรวจสุขภาพ': h_match['health_order'] if h_match else None,
        'ชื่อ_ในใบตรวจสุขภาพ': h_match['health_name'] if h_match else None,
        'อายุ': h_match['age'] if h_match else None,
        'SBP': h_match['sbp'] if h_match else None,
        'DBP': h_match['dbp'] if h_match else None,
        'FBS': h_match['fbs'] if h_match else None,
        'Total_Chol': h_match['chol'] if h_match else None,
    })

df_clean = pd.DataFrame(cleaned_rows)
out_excel = 'data/ประวัติดื่มเหล้า_บุหรี่_รปภ_ปี2569_cleaned.xlsx'
df_clean.to_excel(out_excel, index=False)
print(f"Saved cleaned excel with {len(df_clean)} rows to {out_excel}")
