"""
test_backend.py
Automated verification tests for the NefroAI application:
1. Dataset verification (A, B, C)
2. ML Pipeline & SVM Predictor
3. Medical Receipt & PDF Parser
4. KDIGO Recommendation & Personalization Engine
5. MongoDB Database Operations
6. PDF Clinical Report Generation
"""

import os
import sys
import unittest

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

import pandas as pd

from backend.dataset_manager import get_dataset_a_path, get_dataset_b_path, get_dataset_c_path
from backend.predictor import NefroPredictor
from backend.receipt_parser import parse_medical_receipt
from backend.recommendation_engine import generate_recommendations
from backend.database import db_manager
from frontend.report_generator import generate_pdf_report

class TestNefroAIBackend(unittest.TestCase):

    def test_01_datasets_exist_and_valid(self):
        """Verifies Datasets A, B, and C as described in the paper."""
        path_a = get_dataset_a_path()
        path_b = get_dataset_b_path()
        path_c = get_dataset_c_path()

        self.assertTrue(os.path.exists(path_a), f"Dataset A not found at {path_a}")
        self.assertTrue(os.path.exists(path_b), f"Dataset B not found at {path_b}")
        self.assertTrue(os.path.exists(path_c), f"Dataset C not found at {path_c}")

        df_a = pd.read_csv(path_a)
        df_b = pd.read_csv(path_b)
        df_c = pd.read_csv(path_c)

        self.assertEqual(df_a.shape[0], 400, "Dataset A should have 400 instances")
        self.assertEqual(df_b.shape[0], 1659, "Dataset B should have 1,659 instances")
        self.assertEqual(df_c.shape[0], 200, "Dataset C should have 200 instances")

        # Verify key parameters in Dataset B
        self.assertIn("Diagnosis", df_b.columns)
        self.assertIn("SerumCreatinine", df_b.columns)
        self.assertIn("GFR", df_b.columns)
        self.assertIn("PhysicalActivity", df_b.columns)
        self.assertIn("DietQuality", df_b.columns)
        self.assertIn("SleepQuality", df_b.columns)

    def test_02_ml_predictor(self):
        """Verifies SVM inference, probability output, KDIGO staging, and telemetry."""
        predictor = NefroPredictor(model_type="dataset_b")
        patient_data = {
            "Age": 56, "BMI": 28.8, "PhysicalActivity": 1.5, "DietQuality": 4.0,
            "SystolicBP": 142, "DiastolicBP": 88, "FastingBloodSugar": 132,
            "SerumCreatinine": 1.85, "BUNLevels": 31.5, "GFR": 44.2,
            "ProteinInUrine": 1.6, "ACR": 145.0, "SerumElectrolytesPotassium": 4.8,
            "Edema": 1, "FatigueLevels": 6
        }
        res = predictor.predict(patient_data)
        
        self.assertIn("is_ckd", res)
        self.assertIn("risk_percentage", res)
        self.assertIn("kdigo_stage", res)
        self.assertIn("telemetry", res)
        self.assertGreaterEqual(res["risk_percentage"], 0.0)
        self.assertLessEqual(res["risk_percentage"], 100.0)
        self.assertEqual(res["kdigo_stage"]["stage"], "Stage G3b")
        self.assertGreater(res["telemetry"]["latency_ms"], 0.0)

    def test_03_receipt_parser(self):
        """Verifies parsing of medical lab receipts from both PDF and text."""
        data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
        pdf_path = os.path.join(data_dir, "sample_receipt.pdf")
        
        self.assertTrue(os.path.exists(pdf_path), "Sample receipt PDF must exist")
        with open(pdf_path, "rb") as f:
            res = parse_medical_receipt(f.read(), "sample_receipt.pdf")

        extracted = res["extracted_values"]
        self.assertGreaterEqual(res["matched_count"], 10)
        self.assertAlmostEqual(extracted["SerumCreatinine"], 1.85, places=1)
        self.assertAlmostEqual(extracted["BUNLevels"], 31.5, places=1)
        self.assertAlmostEqual(extracted["GFR"], 44.2, places=1)
        self.assertAlmostEqual(extracted["SystolicBP"], 142.0, places=1)
        self.assertAlmostEqual(extracted["DiastolicBP"], 88.0, places=1)

    def test_04_recommendation_engine(self):
        """Verifies KDIGO tablets, diet targets, yoga asanas, and exercise routines."""
        patient_data = {
            "Age": 56, "BMI": 28.8, "PhysicalActivity": 1.5, "DietQuality": 4.0,
            "SystolicBP": 142, "DiastolicBP": 88, "SerumCreatinine": 1.85,
            "GFR": 44.2, "ProteinInUrine": 1.6, "ACR": 145.0,
            "SerumElectrolytesPotassium": 4.8, "SerumElectrolytesPhosphorus": 4.2,
            "HemoglobinLevels": 11.4, "Edema": 1, "FatigueLevels": 6
        }
        pred_res = {
            "is_ckd": True,
            "risk_percentage": 78.4,
            "kdigo_stage": {"stage": "Stage G3b", "label": "Moderately to Severely Decreased GFR"}
        }

        recs = generate_recommendations(patient_data, pred_res)
        
        # Verify Tablets
        tablets = recs["prescribed_tablets"]
        self.assertGreaterEqual(len(tablets), 2)
        drug_names = [t["drug_name"] for t in tablets]
        self.assertTrue(any("Enalapril" in d or "Losartan" in d for d in drug_names), "Should include RAAS inhibitor for proteinuria")
        self.assertTrue(any("Furosemide" in d or "Torsemide" in d for d in drug_names), "Should include diuretic for edema")

        # Verify Diet
        diet = recs["diet_plan"]
        self.assertIn("daily_protein_target", diet)
        self.assertIn("daily_sodium_target", diet)
        self.assertIn("recommended_foods", diet)
        self.assertIn("foods_to_avoid", diet)
        self.assertIn("1.0", diet["daily_fluid_target"], "Should restrict fluid when edema is present")

        # Verify Yoga
        yogas = recs["yoga_program"]
        self.assertGreaterEqual(len(yogas), 4)
        yoga_names = [y["name"] for y in yogas]
        self.assertTrue(any("Bhujangasana" in y for y in yoga_names))
        self.assertTrue(any("Anulom Vilom" in y for y in yoga_names))

        # Verify Exercise
        exercise = recs["exercise_plan"]
        self.assertIn("aerobic_routine", exercise)
        self.assertIn("weekly_schedule", exercise)

    def test_05_mongodb_integration(self):
        """Verifies connection to local mongodb://localhost:27017, user registration, auth, and record saving."""
        if not db_manager.is_connected():
            self.skipTest("MongoDB not running locally at mongodb://localhost:27017")

        # Verification of validation rules:
        bad_num_user, _ = db_manager.register_user("user123", "pass123", "u@gmail.com", "Test User")
        self.assertFalse(bad_num_user, "Numeric username must be rejected")

        bad_email, _ = db_manager.register_user("validuser", "pass123", "u@yahoo.com", "Test User")
        self.assertFalse(bad_email, "Non-gmail/gamil email must be rejected")

        bad_num_name, _ = db_manager.register_user("validuser", "pass123", "u@gmail.com", "User 007")
        self.assertFalse(bad_num_name, "Numeric in full name must be rejected")

        test_user = "evaluser"
        test_pass = "evalpass"
        
        # Register (or verify existing)
        db_manager.register_user(test_user, test_pass, "evaluser@gmail.com", "Eval Clinician", "clinician")
        ok, auth_data = db_manager.authenticate_user(test_user, test_pass)
        self.assertTrue(ok, "Authentication must succeed for valid credentials")
        self.assertEqual(auth_data["username"], test_user)

        # Save test patient record
        sample_record = {
            "username": test_user,
            "patient_name": "Test Alex",
            "age": 56,
            "gender": "Male",
            "input_parameters": {"SerumCreatinine": 1.85, "GFR": 44.2},
            "prediction": {"is_ckd": True, "risk_percentage": 78.4, "prediction_label": "CKD Detected"},
            "prescribed_tablets": [{"drug_name": "Enalapril"}],
            "diet_plan": {"protein": "0.6g/kg"},
            "yoga_program": [],
            "exercise_plan": {},
            "telemetry": {"latency_ms": 32.1}
        }
        rec_id, msg = db_manager.save_patient_record(sample_record)
        self.assertIsNotNone(rec_id, "Record ID should be generated")

        # Fetch records
        history = db_manager.get_patient_records(username=test_user, limit=5)
        self.assertGreaterEqual(len(history), 1)
        self.assertEqual(history[0]["patient_name"], "Test Alex")

    def test_06_pdf_report_generation(self):
        """Verifies clinical summary PDF report generation."""
        report_data = {
            "patient_name": "Alex Carter",
            "record_id": "REC-TEST-99",
            "username": "demo_doctor",
            "age": 56,
            "gender": "Male",
            "input_parameters": {"SerumCreatinine": 1.85, "GFR": 44.2, "SystolicBP": 142},
            "prediction": {
                "prediction_label": "CKD Detected",
                "risk_percentage": 78.4,
                "risk_level": "High Risk (Early/Moderate CKD)",
                "kdigo_stage": {"stage": "Stage G3b", "label": "Moderately Decreased GFR", "description": "Kidney damage"}
            },
            "prescribed_tablets": [
                {"drug_name": "Enalapril", "class": "ACE Inhibitor", "standard_dose": "10 mg daily", "indication": "Proteinuria control", "caution": "Check potassium"}
            ],
            "diet_plan": {
                "daily_protein_target": "0.65 g/kg/day",
                "daily_sodium_target": "< 2000 mg/day",
                "daily_fluid_target": "1.2 L/day",
                "recommended_foods": [{"food": "Blueberries", "benefit": "Antioxidant"}],
                "foods_to_avoid": [{"food": "Dark Colas", "reason": "High phosphate"}]
            },
            "yoga_program": [{"name": "Bhujangasana", "duration": "30s", "renal_benefit": "Adrenal stimulation"}],
            "exercise_plan": {"aerobic_routine": "Brisk walk 25min", "frequency": "4 days/week", "intensity": "Moderate"}
        }
        pdf_bytes = generate_pdf_report(report_data)
        self.assertIsNotNone(pdf_bytes)
        self.assertGreater(len(pdf_bytes), 1000, "PDF bytes should be substantial")

if __name__ == "__main__":
    unittest.main()
