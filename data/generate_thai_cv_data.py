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

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    excel_path = os.path.join(script_dir, "ตรวจสุขภาพ_รปภ_ปี2569_extracted.xlsx")
    out_dir = os.path.join(script_dir, "..", "src", "data")
    os.makedirs(out_dir, exist_ok=True)
    out_json_path = os.path.join(out_dir, "thai_cv_data.json")

    print(f"Reading {excel_path}...")
    df = pd.read_excel(excel_path)
    print(f"Loaded {len(df)} rows.")

    np.random.seed(42)
    N_SIM = 1000
    P_SMOKE = 0.35  # Thai male national smoking prevalence ~35%

    records = []
    for idx, row in df.iterrows():
        order_no = int(row.get("ลำดับ", idx + 1))
        name = clean_text(row.get("ชื่อ-สกุล", f"รปภ. {order_no}"))
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

        # Sex: all are "นาย" in this dataset
        sex = 1  # 1 = Male

        # Clinical status
        dm = 1 if (fbs is not None and fbs >= 126) else 0
        dm_status = get_fbs_status(fbs)
        bp_stage = get_bp_stage(sbp, dbp)
        age_group = get_age_group(age)
        bmi_cat = get_bmi_category(bmi)

        # Baseline: Smoking = 0 (per user instruction)
        baseline_risk = calc_thai_cv_risk(age, sex, sbp, dm, chol, smoking=0)
        risk_cat = get_risk_category(baseline_risk)

        # What-if Smoker:
        smoke_risk = calc_thai_cv_risk(age, sex, sbp, dm, chol, smoking=1)

        # Monte Carlo Simulation (35% probability of smoking)
        sim_smokes = np.random.rand(N_SIM) < P_SMOKE
        sim_risks = [
            calc_thai_cv_risk(age, sex, sbp, dm, chol, smoking=1 if s else 0)
            for s in sim_smokes
        ]
        sim_med = round(float(np.percentile(sim_risks, 50)), 2)
        sim_p25 = round(float(np.percentile(sim_risks, 2.5)), 2)
        sim_p975 = round(float(np.percentile(sim_risks, 97.5)), 2)
        sim_risk_cat = get_risk_category(sim_med)

        rec = {
            "id": order_no,
            "name": name,
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
            # Primary Outcome: Thai CV Risk Score
            "smoking_baseline": 0,
            "thai_cv_risk": baseline_risk,
            "risk_category": risk_cat,
            # Simulated Outcomes
            "thai_cv_risk_if_smoke": smoke_risk,
            "thai_cv_risk_sim_med": sim_med,
            "thai_cv_risk_sim_ci_lower": sim_p25,
            "thai_cv_risk_sim_ci_upper": sim_p975,
            "risk_category_sim": sim_risk_cat,
        }
        records.append(rec)

    with open(out_json_path, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)

    print(f"Saved {len(records)} records to {out_json_path}")

    # Summary
    df_res = pd.DataFrame(records)
    print("\n--- Summary Statistics ---")
    print(f"Total Subjects: {len(df_res)}")
    print(f"Median Baseline Thai CV Risk: {df_res['thai_cv_risk'].median():.2f}%")
    print(f"Mean Baseline Thai CV Risk: {df_res['thai_cv_risk'].mean():.2f}%")
    print(f"Median Simulated Thai CV Risk: {df_res['thai_cv_risk_sim_med'].median():.2f}%")
    print("\nBaseline Risk Categories:")
    print(df_res['risk_category'].value_counts())
    print("\nSimulated Risk Categories:")
    print(df_res['risk_category_sim'].value_counts())

if __name__ == "__main__":
    main()
