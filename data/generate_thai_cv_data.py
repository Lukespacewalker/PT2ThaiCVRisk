import os
import re
import math
import json
import unicodedata
import numpy as np
import pandas as pd

def clean_num(val):
    if pd.isna(val):
        return None
    s = str(val).strip()
    m = re.search(r'(\d+(?:\.\d+)?)', s)
    return float(m.group(1)) if m else None

def clean_text(val):
    if pd.isna(val):
        return ""
    return str(val).strip()

def clean_thai_name(n):
    if not isinstance(n, str):
        return ""
    n = unicodedata.normalize("NFKD", n)
    n = n.replace("\u0e4d\u0e32", "\u0e33")
    n = n.replace("ปืึน", "ปิ่น").replace("ปัืน", "ปั้น")
    # strip common titles
    n = re.sub(r'^(นาย|น\.ส\.|นางสาว|นาง|ส\.ต\.|ส\.ต|พลฯ|พล|ด\.ต\.|ร\.ต\.ท\.|ร\.ต\.ต\.)\s*', '', n)
    n = re.sub(r'\s+', '', n)
    return n

def calc_thai_cv_risk(age, sex, sbp, dm, chol, smoking=0):
    """
    Ramathibodi / EGAT Thai CV Risk Score equation (with Total Cholesterol):
    FullScore = 0.08183*Age + 0.39499*Sex + 0.02084*SBP + 0.69974*DM + 0.00212*CHOL + 0.41916*SMOKING
    Risk(%) = (1 - 0.978296 ^ exp(FullScore - 7.04423)) * 100
    """
    if any(v is None or pd.isna(v) for v in [age, sex, sbp, dm, chol]):
        return None
    full_score = (0.08183 * age) + (0.39499 * sex) + (0.02084 * sbp) + (0.69974 * dm) + (0.00212 * chol) + (0.41916 * smoking)
    risk = (1.0 - math.pow(0.978296, math.exp(full_score - 7.04423))) * 100.0
    return round(max(0.0, risk), 2)

def get_risk_category(risk):
    if risk is None:
        return "Unknown"
    if risk < 10.0:
        return "Low Risk (<10%)"
    elif risk < 20.0:
        return "Intermediate Risk (10-19.9%)"
    elif risk < 30.0:
        return "High Risk (20-29.9%)"
    else:
        return "Very High Risk (>=30%)"

def get_age_group(age):
    if age < 40:
        return "<40"
    elif age < 50:
        return "40-49"
    elif age < 60:
        return "50-59"
    else:
        return ">=60"

def get_bp_stage(sbp, dbp):
    if sbp is None or dbp is None:
        return "Unknown"
    if sbp >= 160 or dbp >= 100:
        return "Stage 2 HTN"
    elif sbp >= 140 or dbp >= 90:
        return "Stage 1 HTN"
    elif sbp >= 120 or dbp >= 80:
        return "Prehypertension"
    else:
        return "Normal BP"

def get_fbs_status(fbs):
    if fbs is None:
        return "Unknown"
    if fbs >= 126:
        return "Diabetes (>=126)"
    elif fbs >= 100:
        return "Prediabetes (100-125)"
    else:
        return "Normal (<100)"

def get_bmi_category(bmi):
    if bmi is None:
        return "Unknown"
    if bmi < 18.5:
        return "Underweight (<18.5)"
    elif bmi < 23.0:
        return "Normal (18.5-22.9)"
    elif bmi < 25.0:
        return "Overweight (23-24.9)"
    elif bmi < 30.0:
        return "Obese Class 1 (25-29.9)"
    else:
        return "Obese Class 2 (>=30)"

def generate_html_report(records_private, out_html_path):
    """Generate self-contained private HTML dashboard with actual names, smoking, alcohol, and BV post"""
    json_str = json.dumps(records_private, ensure_ascii=False)
    html_content = f"""<!DOCTYPE html>
<html lang="th" data-lang="th">
<head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>[PRIVATE] Thai CV Risk Score Report - กองรักษาความปลอดภัย 2569 (แสดงรายชื่อ)</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&family=Outfit:wght@500;700;800&display=swap" rel="stylesheet">
    <style>
        :root {{
            --bg-color: #F4F1EA;
            --text-color: #2A2A2A;
            --primary: #C85A17;
            --secondary: #E3B448;
            --accent: #2B5953;
            --card-bg: #FFFFFF;
            --border-color: #2A2A2A;
            --border-width: 3px;
            --box-shadow: 6px 6px 0px 0px var(--border-color);
            --border-radius: 4px;
        }}
        * {{ box-sizing: border-box; }}
        body {{
            margin: 0; padding: 0;
            background-color: var(--bg-color);
            color: var(--text-color);
            font-family: 'Inter', system-ui, sans-serif;
            line-height: 1.6;
            background-image: radial-gradient(var(--secondary) 1px, transparent 1px);
            background-size: 40px 40px;
            background-position: -19px -19px;
        }}
        .container {{ max-width: 1700px; margin: 0 auto; padding: 2rem; }}
        .header {{
            background-color: #8E1B1B;
            color: #FFF;
            padding: 2.2rem 2rem;
            margin-bottom: 2rem;
            border: var(--border-width) solid var(--border-color);
            box-shadow: var(--box-shadow);
            border-radius: var(--border-radius);
            position: relative;
        }}
        .private-tag {{
            background: #FFCDD2; color: #B71C1C;
            padding: 0.35rem 0.85rem; border-radius: 20px;
            font-weight: 800; font-size: 0.88rem;
            border: 2px solid #B71C1C; display: inline-block; margin-bottom: 0.6rem;
        }}
        .card {{
            background-color: var(--card-bg);
            border: var(--border-width) solid var(--border-color);
            box-shadow: var(--box-shadow);
            border-radius: var(--border-radius);
            padding: 1.5rem; margin-bottom: 1.5rem;
        }}
        .card-title {{
            font-family: 'Outfit', sans-serif; font-size: 1.25rem;
            color: var(--primary); border-bottom: 2px solid var(--border-color);
            padding-bottom: 0.5rem; margin-bottom: 1rem;
            display: flex; justify-content: space-between; align-items: center;
        }}
        .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 1.25rem; margin-bottom: 2rem; }}
        .kpi-value {{ font-size: 2.5rem; font-weight: 800; color: var(--accent); line-height: 1.1; font-family: 'Outfit', sans-serif; }}
        .kpi-label {{ font-size: 0.85rem; color: #555; text-transform: uppercase; font-weight: 600; margin-top: 0.35rem; }}
        .pill-list {{ display: flex; flex-wrap: wrap; gap: 0.5rem; }}
        .pill {{
            padding: 0.45rem 0.9rem; border: 2px solid var(--border-color); border-radius: 20px;
            background: var(--card-bg); cursor: pointer; font-weight: 600; font-size: 0.88rem;
            box-shadow: 2px 2px 0px 0px var(--border-color);
        }}
        .pill.active {{ background: var(--primary); color: white; }}
        .table-wrap {{ overflow-x: auto; margin-top: 1rem; }}
        .data-table {{ width: 100%; border-collapse: collapse; font-size: 0.9rem; }}
        .data-table th, .data-table td {{ padding: 0.7rem 0.8rem; border: 2px solid var(--border-color); white-space: nowrap; }}
        .data-table th {{ background: var(--accent); color: white; cursor: pointer; }}
        .data-table tbody tr:nth-child(even) {{ background: #F7F4ED; }}
        .data-table tbody tr:hover {{ background: #FFF3E0; }}
        .search-input {{ width: 100%; max-width: 340px; padding: 0.6rem 0.9rem; border: 2px solid var(--border-color); border-radius: 4px; font-size: 0.95rem; }}
        .badge {{ display: inline-block; padding: 0.25rem 0.6rem; border-radius: 4px; font-weight: 700; font-size: 0.82rem; border: 1px solid var(--border-color); }}
        .badge-low {{ background: #E8F5E9; color: #1B5E20; }}
        .badge-intermediate {{ background: #FFF9C4; color: #F57F17; }}
        .badge-high {{ background: #FFE0B2; color: #E65100; }}
        .badge-veryhigh {{ background: #FFCDD2; color: #B71C1C; }}
        .badge-smoke {{ background: #FFCCBC; color: #D84315; border: 1px solid #D84315; }}
        .badge-nosmoke {{ background: #E0F2F1; color: #00695C; border: 1px solid #00695C; }}
        .badge-drink {{ background: #FFF3E0; color: #E65100; border: 1px solid #E65100; }}
        .badge-nodrink {{ background: #F5F5F5; color: #616161; border: 1px solid #9E9E9E; }}
        .badge-bv {{ background: #E8EAF6; color: #283593; font-weight: 600; }}
    </style>
</head>
<body>
    <div class="container">
        <header class="header">
            <div class="private-tag">🔒 PRIVATE REPORT - ฉบับภายในเฉพาะเครื่องนี้ (แสดงชื่อจริง)</div>
            <h1 style="margin:0; font-family:'Outfit',sans-serif;">รายงานความเสี่ยงโรคหัวใจและหลอดเลือด (Thai CV Risk Score) พร้อมประวัติสูบบุหรี่และดื่มสุรา</h1>
            <p style="margin: 0.6rem 0 0 0; opacity: 0.95; font-size:1.05rem;">
                ข้อมูลตรวจสุขภาพและประวัติพฤติกรรมเสี่ยง เจ้าหน้าที่รักษาความปลอดภัย ประจำปี 2569 ปท.2 (74 ราย พร้อมวิเคราะห์ผลกระทบจากการสูบบุหรี่และดื่มแอลกอฮอล์รายบุคคล)
            </p>
        </header>

        <!-- Filters -->
        <div class="card">
            <div style="display:flex; gap:2rem; flex-wrap:wrap;">
                <div>
                    <div style="font-weight:700; margin-bottom:0.4rem;">ระดับความเสี่ยง (Thai CV Risk)</div>
                    <div class="pill-list" id="risk-tabs">
                        <div class="pill active" data-risk="ALL">ทั้งหมด</div>
                        <div class="pill" data-risk="Low Risk (<10%)">เสี่ยงต่ำ (&lt;10%)</div>
                        <div class="pill" data-risk="Intermediate Risk (10-19.9%)">เสี่ยงปานกลาง (10-19.9%)</div>
                        <div class="pill" data-risk="High Risk (20-29.9%)">เสี่ยงสูง (&ge;20%)</div>
                    </div>
                </div>
                <div>
                    <div style="font-weight:700; margin-bottom:0.4rem;">ประวัติการสูบบุหรี่</div>
                    <div class="pill-list" id="smoke-tabs">
                        <div class="pill active" data-smoke="ALL">ทั้งหมด</div>
                        <div class="pill" data-smoke="1">สูบบุหรี่</div>
                        <div class="pill" data-smoke="0">ไม่สูบ</div>
                    </div>
                </div>
                <div>
                    <div style="font-weight:700; margin-bottom:0.4rem;">ประวัติการดื่มแอลกอฮอล์</div>
                    <div class="pill-list" id="alc-tabs">
                        <div class="pill active" data-alc="ALL">ทั้งหมด</div>
                        <div class="pill" data-alc="1">ดื่มแอลกอฮอล์</div>
                        <div class="pill" data-alc="0">ไม่ดื่ม</div>
                    </div>
                </div>
                <div>
                    <div style="font-weight:700; margin-bottom:0.4rem;">ช่วงอายุ</div>
                    <div class="pill-list" id="age-tabs">
                        <div class="pill active" data-age="ALL">ทั้งหมด</div>
                        <div class="pill" data-age="<40">&lt; 40 ปี</div>
                        <div class="pill" data-age="40-49">40-49 ปี</div>
                        <div class="pill" data-age="50-59">50-59 ปี</div>
                    </div>
                </div>
            </div>
        </div>

        <!-- KPIs -->
        <div class="grid">
            <div class="card">
                <div class="card-title">จำนวนพนักงานที่ประเมิน</div>
                <div class="kpi-value" id="kpi-total">0</div>
                <div class="kpi-label">เจ้าหน้าที่รักษาความปลอดภัย (เพศชาย 100%)</div>
            </div>
            <div class="card">
                <div class="card-title">มัธยฐาน Thai CV Risk</div>
                <div class="kpi-value" id="kpi-median">0.0%</div>
                <div class="kpi-label">โอกาสเกิดโรคหลอดเลือดหัวใจ/สมองใน 10 ปี</div>
            </div>
            <div class="card">
                <div class="card-title">กลุ่มเสี่ยงปานกลาง & สูง (&ge;10%)</div>
                <div class="kpi-value" id="kpi-high-prop">0.0%</div>
                <div class="kpi-label" id="kpi-high-count">0 คน</div>
            </div>
            <div class="card">
                <div class="card-title">อัตราการสูบบุหรี่</div>
                <div class="kpi-value" id="kpi-smoke-prop" style="color:#C85A17;">0.0%</div>
                <div class="kpi-label" id="kpi-smoke-count">0 คน</div>
            </div>
            <div class="card">
                <div class="card-title">อัตราการดื่มแอลกอฮอล์</div>
                <div class="kpi-value" id="kpi-alc-prop" style="color:#E65100;">0.0%</div>
                <div class="kpi-label" id="kpi-alc-count">0 คน</div>
            </div>
            <div class="card">
                <div class="card-title">ความดันโลหิตสูง (&ge;140/90)</div>
                <div class="kpi-value" id="kpi-htn-prop" style="color:#B71C1C;">0.0%</div>
                <div class="kpi-label" id="kpi-htn-count">0 คน</div>
            </div>
        </div>

        <!-- Table -->
        <div class="card">
            <div class="card-title">
                <span>รายชื่อพนักงาน ข้อมูลตรวจสุขภาพ และประวัติเสี่ยงรายบุคคล</span>
                <input type="text" id="search-input" class="search-input" placeholder="ค้นหาชื่อ, นามสกุล, หรือจุดประจำการ..." />
            </div>
            <div class="table-wrap">
                <table class="data-table" id="guards-table">
                    <thead>
                        <tr>
                            <th>ลำดับ</th>
                            <th>จุดประจำการ</th>
                            <th>ชื่อ-สกุล</th>
                            <th>อายุ</th>
                            <th>สูบบุหรี่</th>
                            <th>ดื่มสุรา</th>
                            <th>ความดัน (SBP/DBP)</th>
                            <th>BMI</th>
                            <th>น้ำตาล FBS</th>
                            <th>โคเลสเตอรอล</th>
                            <th>Thai CV Risk จริง (%)</th>
                            <th>ระดับความเสี่ยง</th>
                            <th>ความเสี่ยงหากเลิกสูบ (%)</th>
                        </tr>
                    </thead>
                    <tbody id="table-body"></tbody>
                </table>
            </div>
        </div>
    </div>

    <script>
        const DATA = {json_str};
        let selAge = "ALL";
        let selRisk = "ALL";
        let selSmoke = "ALL";
        let selAlc = "ALL";
        let searchQ = "";

        function filterData() {{
            return DATA.filter(r => {{
                if (selAge !== "ALL" && r.age_group !== selAge) return false;
                if (selRisk !== "ALL" && r.risk_category !== selRisk) return false;
                if (selSmoke !== "ALL" && String(r.smoking_actual) !== selSmoke) return false;
                if (selAlc !== "ALL" && String(r.alcohol_actual) !== selAlc) return false;
                if (searchQ) {{
                    const q = searchQ.toLowerCase();
                    const matchName = r.name.toLowerCase().includes(q);
                    const matchPost = (r.work_post || '').toLowerCase().includes(q);
                    const matchId = String(r.id).includes(q);
                    if (!matchName && !matchPost && !matchId) return false;
                }}
                return true;
            }});
        }}

        function update() {{
            const filtered = filterData();
            const total = filtered.length;
            document.getElementById("kpi-total").innerText = total;

            if (total > 0) {{
                const risks = filtered.map(r => r.thai_cv_risk).filter(x => x !== null).sort((a,b)=>a-b);
                const med = risks.length % 2 === 0 ? ((risks[risks.length/2 - 1] + risks[risks.length/2])/2).toFixed(2) : risks[Math.floor(risks.length/2)].toFixed(2);
                document.getElementById("kpi-median").innerText = med + "%";

                const highCount = filtered.filter(r => r.thai_cv_risk >= 10).length;
                document.getElementById("kpi-high-prop").innerText = ((highCount/total)*100).toFixed(1) + "%";
                document.getElementById("kpi-high-count").innerText = `${{highCount}} จาก ${{total}} คน`;

                const smokeCount = filtered.filter(r => r.smoking_actual === 1).length;
                document.getElementById("kpi-smoke-prop").innerText = ((smokeCount/total)*100).toFixed(1) + "%";
                document.getElementById("kpi-smoke-count").innerText = `${{smokeCount}} จาก ${{total}} คน`;

                const alcCount = filtered.filter(r => r.alcohol_actual === 1).length;
                document.getElementById("kpi-alc-prop").innerText = ((alcCount/total)*100).toFixed(1) + "%";
                document.getElementById("kpi-alc-count").innerText = `${{alcCount}} จาก ${{total}} คน`;

                const htnCount = filtered.filter(r => r.sbp >= 140 || r.dbp >= 90).length;
                document.getElementById("kpi-htn-prop").innerText = ((htnCount/total)*100).toFixed(1) + "%";
                document.getElementById("kpi-htn-count").innerText = `${{htnCount}} จาก ${{total}} คน`;
            }} else {{
                document.getElementById("kpi-median").innerText = "0.0%";
                document.getElementById("kpi-high-prop").innerText = "0.0%";
                document.getElementById("kpi-high-count").innerText = "0 คน";
                document.getElementById("kpi-smoke-prop").innerText = "0.0%";
                document.getElementById("kpi-smoke-count").innerText = "0 คน";
                document.getElementById("kpi-alc-prop").innerText = "0.0%";
                document.getElementById("kpi-alc-count").innerText = "0 คน";
                document.getElementById("kpi-htn-prop").innerText = "0.0%";
                document.getElementById("kpi-htn-count").innerText = "0 คน";
            }}

            const tbody = document.getElementById("table-body");
            tbody.innerHTML = filtered.map(r => {{
                let badgeClass = "badge-low";
                if (r.thai_cv_risk >= 30) badgeClass = "badge-veryhigh";
                else if (r.thai_cv_risk >= 20) badgeClass = "badge-high";
                else if (r.thai_cv_risk >= 10) badgeClass = "badge-intermediate";

                const smokeBadge = r.smoking_actual === 1 
                    ? '<span class="badge badge-smoke">สูบบุหรี่</span>' 
                    : (r.smoking_survey_found ? '<span class="badge badge-nosmoke">ไม่สูบ</span>' : '<span class="badge badge-nodrink">ไม่พบข้อมูล</span>');

                const alcBadge = r.alcohol_actual === 1 
                    ? '<span class="badge badge-drink">ดื่มแอลกอฮอล์</span>' 
                    : (r.smoking_survey_found ? '<span class="badge badge-nodrink">ไม่ดื่ม</span>' : '<span class="badge badge-nodrink">ไม่พบข้อมูล</span>');

                let quitDiffHtml = "-";
                if (r.smoking_actual === 1 && r.thai_cv_risk_baseline !== null) {{
                    const diff = (r.thai_cv_risk - r.thai_cv_risk_baseline).toFixed(2);
                    quitDiffHtml = `<span style="color:#00695C; font-weight:bold;">${{r.thai_cv_risk_baseline}}%</span> <span style="font-size:0.8rem; color:#D84315;">(ลดลง -${{diff}}%)</span>`;
                }} else if (r.smoking_actual === 0) {{
                    quitDiffHtml = `<span style="color:#666; font-size:0.85rem;">ไม่สูบอยู่แล้ว</span>`;
                }}

                return `<tr>
                    <td><strong>${{r.id}}</strong></td>
                    <td><span class="badge badge-bv">${{r.work_post || '-'}}</span></td>
                    <td><strong style="color:var(--primary); font-size:1.02rem;">${{r.name}}</strong></td>
                    <td>${{r.age}}</td>
                    <td>${{smokeBadge}}</td>
                    <td>${{alcBadge}}</td>
                    <td>${{r.sbp}} / ${{r.dbp}} <span style="font-size:0.8rem; color:#666;">(${{r.bp_stage}})</span></td>
                    <td>${{r.bmi ? r.bmi.toFixed(1) : '-'}}</td>
                    <td>${{r.fbs}} ${{r.fbs >= 126 ? '<span style="color:#B71C1C; font-weight:bold;">(DM)</span>' : ''}}</td>
                    <td>${{r.cholesterol}}</td>
                    <td><strong style="color:var(--accent); font-size:1.15rem;">${{r.thai_cv_risk}}%</strong></td>
                    <td><span class="badge ${{badgeClass}}">${{r.risk_category}}</span></td>
                    <td>${{quitDiffHtml}}</td>
                </tr>`;
            }}).join("");
        }}

        document.querySelectorAll("#age-tabs .pill").forEach(p => {{
            p.addEventListener("click", () => {{
                document.querySelectorAll("#age-tabs .pill").forEach(x => x.classList.remove("active"));
                p.classList.add("active");
                selAge = p.getAttribute("data-age");
                update();
            }});
        }});

        document.querySelectorAll("#risk-tabs .pill").forEach(p => {{
            p.addEventListener("click", () => {{
                document.querySelectorAll("#risk-tabs .pill").forEach(x => x.classList.remove("active"));
                p.classList.add("active");
                selRisk = p.getAttribute("data-risk");
                update();
            }});
        }});

        document.querySelectorAll("#smoke-tabs .pill").forEach(p => {{
            p.addEventListener("click", () => {{
                document.querySelectorAll("#smoke-tabs .pill").forEach(x => x.classList.remove("active"));
                p.classList.add("active");
                selSmoke = p.getAttribute("data-smoke");
                update();
            }});
        }});

        document.querySelectorAll("#alc-tabs .pill").forEach(p => {{
            p.addEventListener("click", () => {{
                document.querySelectorAll("#alc-tabs .pill").forEach(x => x.classList.remove("active"));
                p.classList.add("active");
                selAlc = p.getAttribute("data-alc");
                update();
            }});
        }});

        document.getElementById("search-input").addEventListener("input", e => {{
            searchQ = e.target.value.trim();
            update();
        }});

        update();
    </script>
</body>
</html>
"""
    with open(out_html_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"Generated standalone private HTML report at: {out_html_path}")

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    excel_health_path = os.path.join(script_dir, "ตรวจสุขภาพ_รปภ_ปี2569_extracted.xlsx")
    excel_life_path = os.path.join(script_dir, "ประวัติดื่มเหล้า บุหรี่ รปภ. ปี 2569 ปท.2.xlsx")

    # Output paths
    src_data_dir = os.path.join(script_dir, "..", "src", "data")
    os.makedirs(src_data_dir, exist_ok=True)
    out_public_json = os.path.join(src_data_dir, "thai_cv_data.json")
    out_private_json = os.path.join(src_data_dir, "thai_cv_data_private.json")

    reports_dir = os.path.join(script_dir, "..", "reports")
    os.makedirs(reports_dir, exist_ok=True)
    out_private_html = os.path.join(reports_dir, "private_report.html")

    print(f"Reading health checkup file: {excel_health_path}...")
    df_health = pd.read_excel(excel_health_path)
    print(f"Loaded {len(df_health)} health rows.")

    print(f"Reading lifestyle file: {excel_life_path}...")
    df_life_raw = pd.read_excel(excel_life_path, sheet_name="27.08.69", header=None)
    df_life = df_life_raw.iloc[5:80].copy()
    print(f"Loaded {len(df_life)} lifestyle rows.")

    # Typos / spelling variations between Health file and Lifestyle file
    MANUAL_ALIAS = {
        "สมเกียร์ติ์สุขตะพงษ์": "สมเกียรติสุขตะพงษ์",
        "อนุชิดศิริมงคล": "อนุชิตศิริมงคล",
        "ธรวัฒน์ไตรรงค์": "ธนวัฒน์ไตรรงค์",
        "วัชริศทรงวรรณะ": "วัชริตทรงวรรณะ",
        "ประสิทธิ์หากวี": "ประสิทธ์หากวี",
        "สมบัติจิ๋วศรีสวัสดิ์": "สมบัติจิ๋วศรีสวัสดิ",
        "เฉลาดวงสุวรรณ์": "เฉลาดวงสุวรรณ",
        "อิศราปราบพาล": "อิศราปราบพาน",
        "อิทธิ์พงศ์วิลัยทอง": "อิทธิ์พงษ์วิลัยทอง",
        "พงศ์สรรค์บรรพโต": "พงศ์สรรค์บรรณโต",
    }

    life_dict = {}
    for idx, row in df_life.iterrows():
        no = row[0]
        bv = str(row[1]).strip() if pd.notna(row[1]) else ""
        orig_name = str(row[2]).strip()
        c_name = clean_thai_name(orig_name)

        c_smoke = pd.notna(row[3]) and "/" in str(row[3])
        v_smoke = pd.notna(row[7]) and "/" in str(row[7])
        smoking = 1 if (c_smoke or v_smoke) else 0

        alcohol = 1 if (pd.notna(row[9]) and "/" in str(row[9])) else 0

        life_dict[c_name] = {
            "life_no": int(no),
            "work_post": bv,
            "life_name": orig_name,
            "smoking_actual": smoking,
            "smoking_status": "สูบบุหรี่" if smoking == 1 else "ไม่สูบ",
            "alcohol_actual": alcohol,
            "alcohol_status": "ดื่มแอลกอฮอล์" if alcohol == 1 else "ไม่ดื่ม",
            "c_smoke": c_smoke,
            "v_smoke": v_smoke,
            "smoking_survey_found": True,
        }

    np.random.seed(42)
    N_SIM = 1000
    P_SMOKE = 0.35

    public_records = []
    private_records = []

    matched_count = 0
    for idx, row in df_health.iterrows():
        order_no = int(row.get("ลำดับ", idx + 1))
        real_name = clean_text(row.get("ชื่อ-สกุล", f"รปภ. {order_no}"))
        anonymized_name = f"เจ้าหน้าที่ รปภ. {order_no:02d}"

        # Match with lifestyle data
        c_name = clean_thai_name(real_name)
        target_name = MANUAL_ALIAS.get(c_name, c_name)

        if target_name in life_dict:
            l_info = life_dict[target_name]
            matched_count += 1
        else:
            l_info = {
                "life_no": None,
                "work_post": "ไม่ระบุ",
                "life_name": None,
                "smoking_actual": 0,
                "smoking_status": "ไม่พบข้อมูลประวัติ (คำนวณแบบไม่สูบ)",
                "alcohol_actual": 0,
                "alcohol_status": "ไม่พบข้อมูลประวัติ",
                "c_smoke": False,
                "v_smoke": False,
                "smoking_survey_found": False,
            }

        age = clean_num(row.get("อายุ"))
        sbp = clean_num(row.get("ความดัน Systolic"))
        dbp = clean_num(row.get("ความดัน Diastolic"))
        pulse = clean_num(row.get("ชีพจร"))
        weight = clean_num(row.get("น้ำหนัก (kg)"))
        height = clean_num(row.get("ส่วนสูง (cm)"))
        bmi = clean_num(row.get("ค่า BMI"))
        bmi_raw_interp = clean_text(row.get("แปลผล BMI"))

        fbs = clean_num(row.get("Diabetes_FBS (mg/dl)"))
        fbs_raw_interp = clean_text(row.get("Diabetes_แปลผล FBS"))

        chol = clean_num(row.get("Lipid_Total Cholesterol"))
        tg = clean_num(row.get("Lipid_Triglyceride"))
        hdl = clean_num(row.get("Lipid_HDL-C"))
        ldl = clean_num(row.get("Lipid_LDL-C"))
        lipid_raw_interp = clean_text(row.get("Lipid_แปลผล Lipid Profile"))

        ast = clean_num(row.get("Liver_SGOT (AST)"))
        alt = clean_num(row.get("Liver_SGPT (ALT)"))
        liver_interp = clean_text(row.get("Liver_แปลผล Liver Function"))

        uric = clean_num(row.get("Uric_Uric Acid (mg/dl)"))
        uric_interp = clean_text(row.get("Uric_แปลผล Uric Acid"))

        hepb = clean_text(row.get("HepB_HBsAg"))
        hepb_interp = clean_text(row.get("HepB_แปลผล HBsAg"))
        ua_interp = clean_text(row.get("UA_สรุปผล UA"))
        drug_interp = clean_text(row.get("Drug_Amphetamine in Urine"))
        xray_interp = clean_text(row.get("XRay_Chest X-Ray Result"))
        ekg_interp = clean_text(row.get("EKG_EKG Result"))
        occ_vision = clean_text(row.get("OccVision_สรุปผลตรวจสมรรถภาพสายตา"))
        audiogram = clean_text(row.get("Audiogram_สรุปผลการได้ยิน"))
        spirometry = clean_text(row.get("Spirometry_สรุปผลตรวจสมรรถภาพปอด"))

        sex = 1  # Male
        dm = 1 if (fbs is not None and fbs >= 126) else 0
        dm_status = get_fbs_status(fbs)
        bp_stage = get_bp_stage(sbp, dbp)
        age_group = get_age_group(age)
        bmi_cat = get_bmi_category(bmi)

        # 1. ACTUAL THAI CV RISK (Using real smoking status!)
        actual_smoking = l_info["smoking_actual"]
        actual_risk = calc_thai_cv_risk(age, sex, sbp, dm, chol, smoking=actual_smoking)
        risk_cat = get_risk_category(actual_risk)

        # 2. Baseline Risk (If non-smoker / quit smoking)
        baseline_risk = calc_thai_cv_risk(age, sex, sbp, dm, chol, smoking=0)
        baseline_risk_cat = get_risk_category(baseline_risk)

        # 3. What-if Smoker (If smoking)
        smoke_risk = calc_thai_cv_risk(age, sex, sbp, dm, chol, smoking=1)

        # 4. Monte Carlo Simulation (~35% Thai male prevalence)
        sim_smokes = np.random.rand(N_SIM) < P_SMOKE
        sim_risks = [
            calc_thai_cv_risk(age, sex, sbp, dm, chol, smoking=1 if s else 0)
            for s in sim_smokes
        ]
        sim_med = round(float(np.percentile(sim_risks, 50)), 2)
        sim_p25 = round(float(np.percentile(sim_risks, 2.5)), 2)
        sim_p975 = round(float(np.percentile(sim_risks, 97.5)), 2)
        sim_risk_cat = get_risk_category(sim_med)

        base_record = {
            "id": order_no,
            "year": 2569,
            "year_ce": 2026,
            "unit": "กองรักษาความปลอดภัย (Security Guard)",
            "work_post": l_info["work_post"],
            "age": age,
            "age_group": age_group,
            "sex": "Male",
            "sex_code": sex,
            "sbp": sbp,
            "dbp": dbp,
            "bp_stage": bp_stage,
            "pulse": pulse,
            "weight": weight,
            "height": height,
            "bmi": bmi,
            "bmi_category": bmi_cat,
            "bmi_raw_interp": bmi_raw_interp,
            "fbs": fbs,
            "dm": dm,
            "dm_status": dm_status,
            "fbs_raw_interp": fbs_raw_interp,
            "cholesterol": chol,
            "triglyceride": tg,
            "hdl": hdl,
            "ldl": ldl,
            "lipid_raw_interp": lipid_raw_interp,
            "ast": ast,
            "alt": alt,
            "liver_interp": liver_interp,
            "uric_acid": uric,
            "uric_interp": uric_interp,
            "hepb": hepb,
            "hepb_interp": hepb_interp,
            "ua_interp": ua_interp,
            "drug_interp": drug_interp,
            "xray_interp": xray_interp,
            "ekg_interp": ekg_interp,
            "occ_vision": occ_vision,
            "audiogram": audiogram,
            "spirometry": spirometry,
            # Lifestyle Data
            "smoking_survey_found": l_info["smoking_survey_found"],
            "smoking_actual": actual_smoking,
            "smoking_status": l_info["smoking_status"],
            "alcohol_actual": l_info["alcohol_actual"],
            "alcohol_status": l_info["alcohol_status"],
            # Thai CV Risk Scores
            "thai_cv_risk": actual_risk, # ACTUAL Risk based on smoking
            "risk_category": risk_cat,
            "thai_cv_risk_baseline": baseline_risk,
            "risk_category_baseline": baseline_risk_cat,
            "thai_cv_risk_if_smoke": smoke_risk,
            "thai_cv_risk_sim_med": sim_med,
            "thai_cv_risk_sim_ci_lower": sim_p25,
            "thai_cv_risk_sim_ci_upper": sim_p975,
            "risk_category_sim": sim_risk_cat,
        }

        # Public: masked name
        pub_rec = dict(base_record)
        pub_rec["name"] = anonymized_name
        public_records.append(pub_rec)

        # Private: real name
        priv_rec = dict(base_record)
        priv_rec["name"] = real_name
        private_records.append(priv_rec)

    print(f"Matched {matched_count}/{len(df_health)} guards with lifestyle data.")

    # Write Public JSON (for Cloudflare Pages / GitHub)
    with open(out_public_json, "w", encoding="utf-8") as f:
        json.dump(public_records, f, ensure_ascii=False, indent=2)
    print(f"Saved {len(public_records)} public records (anonymized) to {out_public_json}")

    # Write Private JSON (for local machine only)
    with open(out_private_json, "w", encoding="utf-8") as f:
        json.dump(private_records, f, ensure_ascii=False, indent=2)
    print(f"Saved {len(private_records)} private records (with real names) to {out_private_json}")

    # Generate standalone Private HTML report
    generate_html_report(private_records, out_private_html)

if __name__ == "__main__":
    main()
