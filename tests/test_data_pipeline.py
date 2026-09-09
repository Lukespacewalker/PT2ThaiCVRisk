import importlib
import json
from pathlib import Path
import unittest


class BloodChemistrySchemaTests(unittest.TestCase):
    def test_amphetamine_schema_has_only_the_five_pdf_columns(self):
        pipeline = importlib.import_module("data.extraction_pipeline")
        if not hasattr(pipeline, "AMPHETAMINE_COLUMNS"):
            self.fail("AMPHETAMINE_COLUMNS must match the PDF table")

        self.assertEqual(
            pipeline.AMPHETAMINE_COLUMNS,
            [
                "ลำดับ",
                "ชื่อ-สกุล",
                "อายุ",
                "Amphetamine in Urine",
                "แปลผล Amphetamine",
            ],
        )

    def test_hepatitis_schema_preserves_antigen_and_antibody_results(self):
        pipeline = importlib.import_module("data.extraction_pipeline")
        if not hasattr(pipeline, "HEPATITIS_B_COLUMNS"):
            self.fail("HEPATITIS_B_COLUMNS must preserve HBsAg and AntiHBs")

        self.assertEqual(
            pipeline.HEPATITIS_B_COLUMNS,
            [
                "ลำดับ",
                "ชื่อ-สกุล",
                "อายุ",
                "HBsAg",
                "แปลผล HBsAg",
                "AntiHBs",
                "แปลผล AntiHBs",
            ],
        )

    def test_cbc_schema_matches_the_nineteen_columns_in_the_pdf(self):
        pipeline = importlib.import_module("data.extraction_pipeline")
        if not hasattr(pipeline, "CBC_COLUMNS"):
            self.fail("CBC_COLUMNS must preserve every CBC field in the PDF")

        self.assertEqual(len(pipeline.CBC_COLUMNS), 19)
        self.assertEqual(pipeline.CBC_COLUMNS[2:6], ["WBC Count", "RBC Count", "Hb", "Hct"])
        self.assertEqual(
            pipeline.CBC_COLUMNS[-3:],
            ["RBC Morphology", "แปลผล CBC", "คำแนะนำ"],
        )

    def test_summary_schema_matches_the_fifteen_columns_in_the_pdf(self):
        try:
            pipeline = importlib.import_module("data.extraction_pipeline")
        except ModuleNotFoundError:
            self.fail("data.extraction_pipeline must define the PDF extraction schema")

        self.assertEqual(
            pipeline.BLOOD_CHEMISTRY_COLUMNS,
            [
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
            ],
        )

    def test_rejects_a_data_row_whose_width_does_not_match_the_schema(self):
        pipeline = importlib.import_module("data.extraction_pipeline")
        if not hasattr(pipeline, "validate_row_width"):
            self.fail("validate_row_width must reject shifted PDF table rows")

        with self.assertRaisesRegex(ValueError, "Blood_Chem_Summary.*15.*14"):
            pipeline.validate_row_width(
                "Blood_Chem_Summary",
                [str(value) for value in range(14)],
                pipeline.BLOOD_CHEMISTRY_COLUMNS,
            )


class LifestyleMappingTests(unittest.TestCase):
    def test_missing_survey_is_unknown_not_a_negative_answer(self):
        try:
            mapping = importlib.import_module("data.lifestyle_mapping")
        except ModuleNotFoundError:
            self.fail("data.lifestyle_mapping must represent missing survey data")

        self.assertEqual(
            mapping.unknown_lifestyle(),
            {
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
            },
        )

    def test_maps_the_survey_checkbox_columns_to_smoking_and_alcohol(self):
        mapping = importlib.import_module("data.lifestyle_mapping")
        if not hasattr(mapping, "parse_lifestyle_checks"):
            self.fail("parse_lifestyle_checks must map the source checkbox columns")

        source_row = [1, "BV", "name", "/", None, None, None, None, "/", "/", None]
        self.assertEqual(
            mapping.parse_lifestyle_checks(source_row),
            {
                "smoking_actual": 1,
                "smoking_status": "สูบบุหรี่",
                "alcohol_actual": 1,
                "alcohol_status": "ดื่มแอลกอฮอล์",
                "c_smoke": True,
                "v_smoke": False,
            },
        )

    def test_rejects_contradictory_yes_and_no_checkboxes(self):
        mapping = importlib.import_module("data.lifestyle_mapping")
        contradictory_row = [1, "BV", "name", "/", None, "/", None, None, "/", None, "/"]

        with self.assertRaisesRegex(ValueError, "บุหรี่/ยาเส้น"):
            mapping.parse_lifestyle_checks(contradictory_row)


class ThaiCvRiskTests(unittest.TestCase):
    def test_out_of_model_range_is_calculated_and_tagged_extrapolated(self):
        risk = importlib.import_module("data.thai_cv_risk")
        if not hasattr(risk, "get_extrapolation_reasons"):
            self.fail("get_extrapolation_reasons must tag calculations outside model ranges")

        score = risk.calc_thai_cv_risk(27, 1, 123, 0, 191, smoking=0)
        self.assertEqual(score, 0.5)
        self.assertEqual(risk.get_extrapolation_reasons(27, 123, 191), ["age"])

    def test_generated_records_preserve_unknown_survey_and_extrapolation_status(self):
        records = json.loads(
            Path("src/data/thai_cv_data.json").read_text(encoding="utf-8")
        )
        by_id = {record["id"]: record for record in records}

        self.assertIsNone(by_id[7]["smoking_actual"])
        self.assertIsNone(by_id[7]["alcohol_actual"])
        self.assertIsNone(by_id[7]["thai_cv_risk"])
        self.assertTrue(by_id[34]["risk_is_extrapolated"])
        self.assertIn("age", by_id[34]["risk_extrapolation_reasons"])
        self.assertEqual(
            {record["id"] for record in records if not record["smoking_survey_found"]},
            {7, 10, 17, 24, 70},
        )
        self.assertEqual(sum(record["smoking_actual"] == 1 for record in records), 21)
        self.assertEqual(
            sum(record["smoking_actual"] in (0, 1) for record in records),
            69,
        )
        self.assertEqual(sum(record["alcohol_actual"] == 1 for record in records), 29)
        self.assertEqual(
            sum(record["alcohol_actual"] in (0, 1) for record in records),
            69,
        )
        self.assertEqual(sum(record["risk_is_extrapolated"] for record in records), 16)


if __name__ == "__main__":
    unittest.main()
