"""Shared, testable rules for converting the health-check PDF tables."""

AMPHETAMINE_COLUMNS = [
    "ลำดับ",
    "ชื่อ-สกุล",
    "อายุ",
    "Amphetamine in Urine",
    "แปลผล Amphetamine",
]

CBC_COLUMNS = [
    "ลำดับ",
    "ชื่อ-สกุล",
    "WBC Count",
    "RBC Count",
    "Hb",
    "Hct",
    "MCV",
    "MCH",
    "MCHC",
    "RDW",
    "Platelet Count",
    "PMN/Neu",
    "Lym",
    "Mono",
    "Eos",
    "Baso",
    "RBC Morphology",
    "แปลผล CBC",
    "คำแนะนำ",
]

BLOOD_CHEMISTRY_COLUMNS = [
    "ลำดับ",
    "ชื่อ-สกุล",
    "อายุ",
    "FBS",
    "แปลผล FBS",
    "Cholesterol",
    "Triglyceride",
    "HDL-C",
    "LDL-C",
    "แปลผล Lipid Profile",
    "SGOT (AST)",
    "SGPT (ALT)",
    "แปลผล Liver Function",
    "Uric Acid",
    "แปลผล Uric Acid",
]

HEPATITIS_B_COLUMNS = [
    "ลำดับ",
    "ชื่อ-สกุล",
    "อายุ",
    "HBsAg",
    "แปลผล HBsAg",
    "AntiHBs",
    "แปลผล AntiHBs",
]


def validate_row_width(section_name, row, expected_columns):
    """Fail loudly instead of silently shifting or discarding PDF cells."""
    expected = len(expected_columns)
    actual = len(row)
    if actual != expected:
        raise ValueError(
            f"{section_name}: expected {expected} columns from the PDF schema, "
            f"but extracted {actual}"
        )
    return row
