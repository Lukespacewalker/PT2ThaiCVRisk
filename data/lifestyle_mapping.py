"""Rules for mapping the smoking and alcohol survey into health records."""


def _checked(value):
    return value is not None and "/" in str(value)


def _choice(yes_value, no_value, label):
    yes = _checked(yes_value)
    no = _checked(no_value)
    if yes and no:
        raise ValueError(f"เลือกทั้งใช่และไม่ใช่สำหรับ {label}")
    if not yes and not no:
        return None
    return yes


def parse_lifestyle_checks(row):
    """Map the source sheet's yes-checkbox columns to model inputs."""
    c_smoke = _choice(row[3], row[5], "บุหรี่/ยาเส้น")
    v_smoke = _choice(row[7], row[8], "บุหรี่ไฟฟ้า")
    alcohol_checked = _choice(row[9], row[10], "การดื่มแอลกอฮอล์")

    smoking = None if c_smoke is None or v_smoke is None else int(c_smoke or v_smoke)
    alcohol = None if alcohol_checked is None else int(alcohol_checked)
    return {
        "smoking_actual": smoking,
        "smoking_status": (
            "ไม่พบข้อมูลประวัติ" if smoking is None else "สูบบุหรี่" if smoking else "ไม่สูบ"
        ),
        "alcohol_actual": alcohol,
        "alcohol_status": (
            "ไม่พบข้อมูลประวัติ" if alcohol is None else "ดื่มแอลกอฮอล์" if alcohol else "ไม่ดื่ม"
        ),
        "c_smoke": c_smoke,
        "v_smoke": v_smoke,
    }


def unknown_lifestyle():
    """Represent an absent survey response without inventing negative answers."""
    return {
        "life_no": None,
        "work_post": "ไม่ระบุ",
        "life_name": None,
        "smoking_actual": None,
        "smoking_status": "ไม่พบข้อมูลประวัติ",
        "alcohol_actual": None,
        "alcohol_status": "ไม่พบข้อมูลประวัติ",
        "c_smoke": None,
        "v_smoke": None,
        "smoking_survey_found": False,
    }
