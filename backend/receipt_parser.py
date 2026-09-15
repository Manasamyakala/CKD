"""
receipt_parser.py
Dynamic medical receipt and lab report parser for clinical biomarkers, patient demographics,
and lifestyle indicators from uploaded PDF, TXT, or image files.
"""

import re
import io
import pypdf

# Common medical regex patterns with optional parenthesized abbreviations and optional colon/dash
SEP = r"(?:\s*\([a-z0-9\s/+-]+\))?\s*[:=–-]*\s+"
VAL = r"([0-9]+\.?[0-9]*)"

PATTERNS = {
    "SerumCreatinine": [
        r"(?:serum\s*creatinine|s\.?\s*creatinine|creatinine|sc)" + SEP + VAL,
    ],
    "BUNLevels": [
        r"(?:blood\s*urea\s*nitrogen|bun\s*levels|bun|blood\s*urea|urea|bu)" + SEP + VAL,
    ],
    "GFR": [
        r"(?:estimated\s*gfr|estimated\s*glomerular\s*filtration\s*rate|egfr|gfr|grf)" + SEP + VAL,
    ],
    "HemoglobinLevels": [
        r"(?:hemoglobin\s*levels|hemoglobin|haemoglobin|hemo|hb|hgb)" + SEP + VAL,
    ],
    "FastingBloodSugar": [
        r"(?:fasting\s*blood\s*sugar|fasting\s*blood\s*glucose|fasting\s*glucose|fbs|blood\s*glucose\s*random|bgr|blood\s*sugar|glucose)" + SEP + VAL,
    ],
    "HbA1c": [
        r"(?:glycated\s*hemoglobin|glycosylated\s*hemoglobin|hba1c|a1c)" + SEP + VAL,
    ],
    "SystolicBP": [
        r"(?:systolic\s*bp|systolic\s*blood\s*pressure|sbp)" + SEP + VAL,
        r"(?:blood\s*pressure|bp)" + SEP + r"([0-9]{2,3})\s*/\s*[0-9]{2,3}",
    ],
    "DiastolicBP": [
        r"(?:diastolic\s*bp|diastolic\s*blood\s*pressure|dbp)" + SEP + VAL,
        r"(?:blood\s*pressure|bp)" + SEP + r"[0-9]{2,3}\s*/\s*([0-9]{2,3})",
    ],
    "ProteinInUrine": [
        r"(?:protein\s*in\s*urine|urine\s*protein|urine\s*albumin|proteinuria|protein)" + SEP + VAL,
    ],
    "ACR": [
        r"(?:albumin[- ]to[- ]creatinine\s*ratio|albumin/creatinine\s*ratio|acr|uacr)" + SEP + VAL,
    ],
    "SerumElectrolytesSodium": [
        r"(?:serum\s*electrolytes\s*sodium|serum\s*sodium|sodium|sod|na)" + SEP + VAL,
    ],
    "SerumElectrolytesPotassium": [
        r"(?:serum\s*electrolytes\s*potassium|serum\s*potassium|potassium|pot|k)" + SEP + VAL,
    ],
    "SerumElectrolytesCalcium": [
        r"(?:serum\s*electrolytes\s*calcium|serum\s*calcium|calcium|ca)" + SEP + VAL,
    ],
    "SerumElectrolytesPhosphorus": [
        r"(?:serum\s*electrolytes\s*phosphorus|serum\s*phosphorus|phosphorus|phosphate|po4)" + SEP + VAL,
    ],
    "CholesterolTotal": [
        r"(?:cholesterol\s*total|total\s*cholesterol|cholesterol)" + SEP + VAL,
    ],
    "CholesterolLDL": [
        r"(?:cholesterol\s*ldl|ldl\s*cholesterol|ldl)" + SEP + VAL,
    ],
    "CholesterolHDL": [
        r"(?:cholesterol\s*hdl|hdl\s*cholesterol|hdl)" + SEP + VAL,
    ],
    "CholesterolTriglycerides": [
        r"(?:cholesterol\s*triglycerides|triglycerides|tg)" + SEP + VAL,
    ],
    "BMI": [
        r"(?:body\s*mass\s*index|bmi)" + SEP + VAL,
    ],
    "Age": [
        r"(?:patient\s*age|age)" + SEP + VAL,
    ]
}

def extract_text_from_file(file_bytes, file_name):
    """
    Extracts text content from uploaded PDF or text file.
    """
    text = ""
    lower_name = file_name.lower()
    
    if lower_name.endswith(".pdf"):
        try:
            reader = pypdf.PdfReader(io.BytesIO(file_bytes))
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        except Exception as e:
            text = f"[PDF Extraction Error: {e}]"
    else:
        try:
            text = file_bytes.decode("utf-8", errors="ignore")
        except Exception:
            text = str(file_bytes)
            
    return text

def parse_medical_receipt(file_bytes, file_name):
    """
    Dynamically parses an uploaded medical lab report / receipt and extracts:
    - Patient Name
    - Age & Gender
    - All clinical lab values (Creatinine, BUN, GFR, Protein, BP, etc.)
    - Lifestyle indicators (BMI, Edema, Fatigue, Diet, Activity)
    """
    raw_text = extract_text_from_file(file_bytes, file_name)
    extracted = {}
    text_clean = raw_text.lower()
    
    # 1. Extract Patient Name
    name_match = re.search(r"(?:patient\s*name|name\s*of\s*patient|patient)[\s:=]+([a-zA-Z\s\.\,\'\-]+?)(?:\s+age|\s+gender|\s+date|\s+ref|\s+test|\s*\n)", raw_text, re.IGNORECASE)
    if name_match:
        p_name = name_match.group(1).strip()
        # Clean up any trailing labels
        p_name = re.sub(r"\s+(?:age|gender|sex|date|dr|mr|mrs|ms).*", "", p_name, flags=re.IGNORECASE).strip()
        if len(p_name) > 2:
            extracted["PatientName"] = p_name.title()
    else:
        extracted["PatientName"] = "Patient"

    # 2. Extract Gender
    gender_match = re.search(r"(?:gender|sex)[\s:=]+(male|female|m|f)\b", text_clean, re.IGNORECASE)
    if gender_match:
        g = gender_match.group(1).lower()
        extracted["Gender"] = "Female" if g in ["female", "f"] else "Male"
    else:
        extracted["Gender"] = "Male"

    # 3. Extract Numerical Biomarkers
    for feature, pattern_list in PATTERNS.items():
        for pattern in pattern_list:
            match = re.search(pattern, text_clean, re.IGNORECASE)
            if match:
                try:
                    val_str = match.group(1).strip()
                    val = float(val_str)
                    extracted[feature] = val
                    break
                except ValueError:
                    continue

    # Derive eGFR if GFR missing but Serum Creatinine present
    if "GFR" not in extracted and "SerumCreatinine" in extracted:
        sc = extracted["SerumCreatinine"]
        age = extracted.get("Age", 55)
        extracted["GFR"] = round(142 * (max(sc / 0.9, 1) ** -1.200) * (0.9938 ** age), 1)

    # 4. Extract Symptoms & Lifestyle Indicators Dynamically
    # Edema (Swelling)
    if any(term in text_clean for term in ["edema", "swelling", "pedal edema", "fluid overload"]):
        if any(neg in text_clean for neg in ["no edema", "edema: nil", "edema: no", "edema: negative", "swelling: no"]):
            extracted["Edema"] = 0
        else:
            extracted["Edema"] = 1
    else:
        # Default based on proteinuria or normal state
        extracted["Edema"] = 1 if extracted.get("ProteinInUrine", 0) >= 1.5 else 0

    # Fatigue, Cramps, Itching
    if any(t in text_clean for t in ["fatigue", "tiredness", "weakness"]):
        extracted["FatigueLevels"] = 6
    else:
        extracted["FatigueLevels"] = 2

    if "cramp" in text_clean:
        extracted["MuscleCramps"] = 3
    else:
        extracted["MuscleCramps"] = 0

    if any(t in text_clean for t in ["itching", "pruritus"]):
        extracted["Itching"] = 4
    else:
        extracted["Itching"] = 0

    # Dynamic Diet & Physical Activity inference from clinical impression
    is_severe = (
        extracted.get("GFR", 90) < 60 or
        extracted.get("SerumCreatinine", 1.0) > 1.4 or
        extracted.get("ProteinInUrine", 0) > 0.5 or
        "stage g3" in text_clean or "stage g4" in text_clean or "stage g5" in text_clean or "ckd" in text_clean
    )

    if is_severe:
        extracted["DietQuality"] = 4.0
        extracted["PhysicalActivity"] = 1.5
        extracted["SleepQuality"] = 5.5
    else:
        extracted["DietQuality"] = 7.5
        extracted["PhysicalActivity"] = 4.0
        extracted["SleepQuality"] = 8.0

    return {
        "extracted_values": extracted,
        "matched_count": len(extracted),
        "patient_name": extracted.get("PatientName", "Patient"),
        "raw_text_snippet": raw_text[:600] + ("..." if len(raw_text) > 600 else "")
    }

if __name__ == "__main__":
    import os
    pdf_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "sample_receipt.pdf")
    if os.path.exists(pdf_path):
        with open(pdf_path, "rb") as f:
            res = parse_medical_receipt(f.read(), "sample_receipt.pdf")
            print("Extracted from sample_receipt.pdf:")
            print("  Patient Name:", res["patient_name"])
            print("  Total Fields Matched:", res["matched_count"])
            for k, v in res["extracted_values"].items():
                print(f"    {k}: {v}")
