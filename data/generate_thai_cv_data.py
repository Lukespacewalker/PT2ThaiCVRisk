import os
import re
import math
import json
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
    """Generate self-contained private HTML dashboard with actual names"""
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
    <script src="https://cdn.plot.ly/plotly-2.32.0.min.js"></script>
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
        .container {{ max-width: 1600px; margin: 0 auto; padding: 2rem; }}
        .header {{
            background-color: #8E1B1B;
            color: #FFF;
            padding: 2.5rem 2rem 2rem 2rem;
            margin-bottom: 2rem;
            border: var(--border-width) solid var(--border-color);
            box-shadow: var(--box-shadow);
            border-radius: var(--border-radius);
            position: relative;
        }}
        .private-tag {{
            background: #FFCDD2; color: #B71C1C;
            padding: 0.3rem 0.8rem; border-radius: 20px;
            font-weight: 800; font-size: 0.85rem;
            border: 2px solid #B71C1C; display: inline-block; margin-bottom: 0.5rem;
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
        .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 1.5rem; margin-bottom: 2rem; }}
        .kpi-value {{ font-size: 2.75rem; font-weight: 800; color: var(--accent); line-height: 1.1; font-family: 'Outfit', sans-serif; }}
        .kpi-label {{ font-size: 0.85rem; color: #666; text-transform: uppercase; font-weight: 600; margin-top: 0.35rem; }}
        .pill-list {{ display: flex; flex-wrap: wrap; gap: 0.5rem; }}
        .pill {{
            padding: 0.45rem 0.9rem; border: 2px solid var(--border-color); border-radius: 20px;
            background: var(--card-bg); cursor: pointer; font-weight: 600; font-size: 0.9rem;
            box-shadow: 2px 2px 0px 0px var(--border-color);
        }}
        .pill.active {{ background: var(--primary); color: white; }}
        .table-wrap {{ overflow-x: auto; margin-top: 1rem; }}
        .data-table {{ width: 100%; border-collapse: collapse; font-size: 0.92rem; }}
        .data-table th, .data-table td {{ padding: 0.75rem 0.85rem; border: 2px solid var(--border-color); white-space: nowrap; }}
        .data-table th {{ background: var(--accent); color: white; cursor: pointer; }}
        .data-table tbody tr:nth-child(even) {{ background: #F7F4ED; }}
        .data-table tbody tr:hover {{ background: #FFF3E0; }}
        .search-input {{ width: 100%; max-width: 320px; padding: 0.6rem 0.9rem; border: 2px solid var(--border-color); border-radius: 4px; font-size: 0.95rem; }}
        .badge {{ display: inline-block; padding: 0.25rem 0.6rem; border-radius: 4px; font-weight: 700; font-size: 0.82rem; border: 1px solid var(--border-color); }}
        .badge-low {{ background: #E8F5E9; color: #1B5E20; }}
        .badge-intermediate {{ background: #FFF9C4; color: #F57F17; }}
        .badge-high {{ background: #FFE0B2; color: #E65100; }}
        .badge-veryhigh {{ background: #FFCDD2; color: #B71C1C; }}
    </style>
</head>
<body>
    <div class="container">
        <header class="header">
            <div class="private-tag">🔒 PRIVATE REPORT - ฉบับภายในเฉพาะเครื่องนี้ (แสดงชื่อจริง)</div>
            <h1 style="margin:0; font-family:'Outfit',sans-serif;">รายงานความเสี่ยงโรคหัวใจและหลอดเลือด (Thai CV Risk Score)</h1>
            <p style="margin: 0.5rem 0 0 0; opacity: 0.95;">ข้อมูลตรวจสุขภาพเจ้าหน้าที่รักษาความปลอดภัย ประจำปี 2569 (แสดงรายชื่อพนักงาน 74 ราย สำหรับการติดตามสุขภาพรายบุคคล)</p>
        </header>

        <!-- Filters -->
        <div class="card">
            <div style="display:flex; gap:2rem; flex-wrap:wrap;">
                <div>
                    <div style="font-weight:700; margin-bottom:0.4rem;">ช่วงอายุ</div>
                    <div class="pill-list" id="age-tabs">
                        <div class="pill active" data-age="ALL">ทั้งหมด</div>
                        <div class="pill" data-age="<40">&lt; 40 ปี</div>
                        <div class="pill" data-age="40-49">40-49 ปี</div>
                        <div class="pill" data-age="50-59">50-59 ปี</div>
                    </div>
                </div>
                <div>
                    <div style="font-weight:700; margin-bottom:0.4rem;">ระดับความเสี่ยง</div>
                    <div class="pill-list" id="risk-tabs">
                        <div class="pill active" data-risk="ALL">ทั้งหมด</div>
                        <div class="pill" data-risk="Low Risk (<10%)">เสี่ยงต่ำ (&lt;10%)</div>
                        <div class="pill" data-risk="Intermediate Risk (10-19.9%)">เสี่ยงปานกลาง (10-19.9%)</div>
                        <div class="pill" data-risk="High Risk (20-29.9%)">เสี่ยงสูง (&ge;20%)</div>
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
                <div class="card-title">มัธยฐานความเสี่ยง (Thai CV Risk)</div>
                <div class="kpi-value" id="kpi-median">0.0%</div>
                <div class="kpi-label">โอกาสเกิดโรคหัวใจ/สมองใน 10 ปี</div>
            </div>
            <div class="card">
                <div class="card-title">กลุ่มเสี่ยงปานกลางและสูง</div>
                <div class="kpi-value" id="kpi-high-prop">0.0%</div>
                <div class="kpi-label" id="kpi-high-count">0 คน</div>
            </div>
            <div class="card">
                <div class="card-title">ความดันโลหิตสูง (&ge;140/90)</div>
                <div class="kpi-value" id="kpi-htn-prop">0.0%</div>
                <div class="kpi-label" id="kpi-htn-count">0 คน</div>
            </div>
        </div>

        <!-- Table -->
        <div class="card">
            <div class="card-title">
                <span>รายชื่อพนักงานและผลตรวจรายบุคคล</span>
                <input type="text" id="search-input" class="search-input" placeholder="ค้นหาชื่อหรือลำดับ..." />
            </div>
            <div class="table-wrap">
                <table class="data-table" id="guards-table">
                    <thead>
                        <tr>
                            <th>ลำดับ</th>
                            <th>ชื่อ-สกุล</th>
                            <th>อายุ</th>
                            <th>ความดัน (SBP/DBP)</th>
                            <th>BMI</th>
                            <th>น้ำตาล FBS</th>
                            <th>โคเลสเตอรอล</th>
                            <th>HDL</th>
                            <th>LDL</th>
                            <th>Thai CV Risk (%)</th>
                            <th>ระดับความเสี่ยง</th>
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
        let searchQ = "";

        function filterData() {{
            return DATA.filter(r => {{
                if (selAge !== "ALL" && r.age_group !== selAge) return false;
                if (selRisk !== "ALL" && r.risk_category !== selRisk) return false;
                if (searchQ) {{
                    const q = searchQ.toLowerCase();
                    if (!r.name.toLowerCase().includes(q) && !String(r.id).includes(q)) return false;
                }}
                return true;
            }});
        }}

        function update() {{
            const filtered = filterData();
            const total = filtered.length;
            document.getElementById("kpi-total").innerText = total;

            if (total > 0) {{
                const risks = filtered.map(r => r.thai_cv_risk).sort((a,b)=>a-b);
                const med = risks.length % 2 === 0 ? ((risks[risks.length/2 - 1] + risks[risks.length/2])/2).toFixed(2) : risks[Math.floor(risks.length/2)].toFixed(2);
                document.getElementById("kpi-median").innerText = med + "%";
                const highCount = filtered.filter(r => r.thai_cv_risk >= 10).length;
                document.getElementById("kpi-high-prop").innerText = ((highCount/total)*100).toFixed(1) + "%";
                document.getElementById("kpi-high-count").innerText = `${{highCount}} จาก ${{total}} คน`;

                const htnCount = filtered.filter(r => r.sbp >= 140 || r.dbp >= 90).length;
                document.getElementById("kpi-htn-prop").innerText = ((htnCount/total)*100).toFixed(1) + "%";
                document.getElementById("kpi-htn-count").innerText = `${{htnCount}} จาก ${{total}} คน`;
            }} else {{
                document.getElementById("kpi-median").innerText = "0.0%";
                document.getElementById("kpi-high-prop").innerText = "0.0%";
                document.getElementById("kpi-high-count").innerText = "0 คน";
                document.getElementById("kpi-htn-prop").innerText = "0.0%";
                document.getElementById("kpi-htn-count").innerText = "0 คน";
            }}

            const tbody = document.getElementById("table-body");
            tbody.innerHTML = filtered.map(r => {{
                let badgeClass = "badge-low";
                if (r.thai_cv_risk >= 30) badgeClass = "badge-veryhigh";
                else if (r.thai_cv_risk >= 20) badgeClass = "badge-high";
                else if (r.thai_cv_risk >= 10) badgeClass = "badge-intermediate";

                return `<tr>
                    <td><strong>${{r.id}}</strong></td>
                    <td><strong style="color:var(--primary); font-size:1.02rem;">${{r.name}}</strong></td>
                    <td>${{r.age}}</td>
                    <td>${{r.sbp}} / ${{r.dbp}} <span style="font-size:0.8rem; color:#666;">(${{r.bp_stage}})</span></td>
                    <td>${{r.bmi ? r.bmi.toFixed(1) : '-'}}</td>
                    <td>${{r.fbs}} ${{r.fbs >= 126 ? '<span style="color:#B71C1C; font-weight:bold;">(DM)</span>' : ''}}</td>
                    <td>${{r.cholesterol}}</td>
                    <td>${{r.hdl}}</td>
                    <td>${{r.ldl}}</td>
                    <td><strong style="color:var(--accent); font-size:1.1rem;">${{r.thai_cv_risk}}%</strong></td>
                    <td><span class="badge ${{badgeClass}}">${{r.risk_category}}</span></td>
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
    print(f"Generated private standalone HTML report at: {out_html_path}")

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    excel_path = os.path.join(script_dir, "ตรวจสุขภาพ_รปภ_ปี2569_extracted.xlsx")
    out_dir = os.path.join(script_dir, "..", "src", "data")
    os.makedirs(out_dir, exist_ok=True)
    out_public_json = os.path.join(out_dir, "thai_cv_data.json")
    out_private_json = os.path.join(out_dir, "thai_cv_data_private.json")

    reports_dir = os.path.join(script_dir, "..", "reports")
    os.makedirs(reports_dir, exist_ok=True)
    out_private_html = os.path.join(reports_dir, "private_report.html")

    print(f"Reading {excel_path}...")
    df = pd.read_excel(excel_path)
    print(f"Loaded {len(df)} rows.")

    np.random.seed(42)
    N_SIM = 1000
    P_SMOKE = 0.35  # Thai male national smoking prevalence ~35%

    public_records = []
    private_records = []

    for idx, row in df.iterrows():
        order_no = int(row.get("ลำดับ", idx + 1))
        real_name = clean_text(row.get("ชื่อ-สกุล", f"รปภ. {order_no}"))
        anonymized_name = f"เจ้าหน้าที่ รปภ. {order_no:02d}"

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

        # Baseline: Smoking = 0
        baseline_risk = calc_thai_cv_risk(age, sex, sbp, dm, chol, smoking=0)
        risk_cat = get_risk_category(baseline_risk)

        # What-if Smoker:
        smoke_risk = calc_thai_cv_risk(age, sex, sbp, dm, chol, smoking=1)

        # Monte Carlo Simulation
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
            "smoking_baseline": 0,
            "thai_cv_risk": baseline_risk,
            "risk_category": risk_cat,
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
