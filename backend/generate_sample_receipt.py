"""
generate_sample_receipt.py
Generates sample medical receipt files (PDF and TXT) in data/ directory
so users can easily test the upload functionality in the Streamlit application.
"""

import os
from fpdf import FPDF

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")

def create_sample_files():
    os.makedirs(DATA_DIR, exist_ok=True)
    
    txt_path = os.path.join(DATA_DIR, "sample_receipt.txt")
    pdf_path = os.path.join(DATA_DIR, "sample_receipt.pdf")
    
    content = """CENTRAL DIAGNOSTIC PATHOLOGY LABORATORY
Accredited Clinical Reference Lab | Reg: LAB-CKD-2026-9912
----------------------------------------------------------------------
PATIENT REPORT & MEDICAL RECEIPT
Patient Name: Alex Carter               Age: 56 Years
Gender: Male                            Date: 14-Sep-2026
Referring Physician: Dr. Sarah Jenkins   Test Panel: Comprehensive Renal Panel
----------------------------------------------------------------------
LABORATORY INVESTIGATION FINDINGS:

1. RENAL FUNCTION TESTS (RFT / KFT):
   - Serum Creatinine (SC)            : 1.85 mg/dL     (Ref: 0.60 - 1.20)  [HIGH]
   - Blood Urea Nitrogen (BUN)        : 31.5 mg/dL     (Ref: 7.0 - 20.0)   [HIGH]
   - Estimated GFR (eGFR)             : 44.2 mL/min    (Ref: >= 90)        [LOW]
   - Serum Electrolytes Sodium (Na)   : 137.0 mEq/L    (Ref: 135 - 145)    [NORMAL]
   - Serum Electrolytes Potassium (K) : 4.80 mEq/L     (Ref: 3.5 - 5.0)    [NORMAL]
   - Serum Electrolytes Calcium (Ca)  : 8.90 mg/dL     (Ref: 8.5 - 10.5)   [NORMAL]
   - Serum Electrolytes Phosphorus (P): 4.20 mg/dL     (Ref: 2.5 - 4.5)    [NORMAL]

2. URINALYSIS & PROTEINURIA:
   - Protein In Urine                 : 1.60 g/day     (Ref: < 0.15)       [HIGH]
   - Albumin-to-Creatinine Ratio (ACR): 145.0 mg/g     (Ref: < 30)         [HIGH]

3. HEMATOLOGY & METABOLIC:
   - Hemoglobin Levels (Hb)           : 11.4 g/dL      (Ref: 13.5 - 17.5)  [MILD ANEMIA]
   - Fasting Blood Sugar (FBS)        : 132.0 mg/dL    (Ref: 70 - 100)     [ELEVATED]
   - HbA1c                            : 6.7 %          (Ref: < 5.7%)       [DIABETIC RANGE]

4. VITALS & CARDIOVASCULAR:
   - Blood Pressure (BP)              : 142/88 mmHg    (Ref: < 120/80)     [HYPERTENSIVE]
   - Body Mass Index (BMI)            : 28.8           (Ref: 18.5 - 24.9)  [OVERWEIGHT]
----------------------------------------------------------------------
CLINICAL IMPRESSION:
Laboratory findings demonstrate moderately reduced Glomerular Filtration Rate
with significant macroalbuminuria and elevated serum creatinine.
KDIGO Category corresponds to Stage G3b. RAAS blockade and renal diet modification advised.
======================================================================
"""

    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(content)
        
    # Generate PDF using fpdf2
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 10, "CENTRAL DIAGNOSTIC PATHOLOGY LABORATORY", ln=True, align="C")
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 6, "Accredited Clinical Reference Lab | Reg: LAB-CKD-2026-9912", ln=True, align="C")
    pdf.line(10, 28, 200, 28)
    pdf.ln(5)
    
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 7, "PATIENT REPORT & MEDICAL RECEIPT", ln=True)
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(95, 6, "Patient Name: Alex Carter", ln=False)
    pdf.cell(95, 6, "Age: 56 Years | Gender: Male", ln=True)
    pdf.cell(95, 6, "Date: 14-Sep-2026", ln=False)
    pdf.cell(95, 6, "Test: Comprehensive Renal Panel (KFT)", ln=True)
    pdf.line(10, 48, 200, 48)
    pdf.ln(5)
    
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 7, "LABORATORY INVESTIGATION FINDINGS:", ln=True)
    pdf.set_font("Helvetica", "", 9)
    
    lines = [
        ("Serum Creatinine (SC)", "1.85 mg/dL", "0.60 - 1.20", "HIGH"),
        ("Blood Urea Nitrogen (BUN)", "31.5 mg/dL", "7.0 - 20.0", "HIGH"),
        ("Estimated GFR (eGFR)", "44.2 mL/min", ">= 90", "LOW"),
        ("Protein In Urine", "1.60 g/day", "< 0.15", "HIGH"),
        ("Albumin-to-Creatinine Ratio (ACR)", "145.0 mg/g", "< 30", "HIGH"),
        ("Hemoglobin Levels (Hb)", "11.4 g/dL", "13.5 - 17.5", "MILD ANEMIA"),
        ("Fasting Blood Sugar (FBS)", "132.0 mg/dL", "70 - 100", "ELEVATED"),
        ("HbA1c", "6.7 %", "< 5.7%", "HIGH"),
        ("Serum Sodium (Na)", "137.0 mEq/L", "135 - 145", "NORMAL"),
        ("Serum Potassium (K)", "4.80 mEq/L", "3.5 - 5.0", "NORMAL"),
        ("Serum Calcium (Ca)", "8.90 mg/dL", "8.5 - 10.5", "NORMAL"),
        ("Serum Phosphorus (P)", "4.20 mg/dL", "2.5 - 4.5", "NORMAL"),
        ("Blood Pressure (BP)", "142/88 mmHg", "< 120/80", "HYPERTENSIVE"),
        ("Body Mass Index (BMI)", "28.8", "18.5 - 24.9", "OVERWEIGHT")
    ]
    
    # Table header
    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(75, 6, "Test Parameter", border=1)
    pdf.cell(35, 6, "Result", border=1)
    pdf.cell(40, 6, "Reference Range", border=1)
    pdf.cell(40, 6, "Status", border=1, ln=True)
    
    pdf.set_font("Helvetica", "", 9)
    for param, res, ref, status in lines:
        pdf.cell(75, 5, param, border=1)
        pdf.cell(35, 5, res, border=1)
        pdf.cell(40, 5, ref, border=1)
        pdf.cell(40, 5, status, border=1, ln=True)
        
    pdf.ln(5)
    pdf.set_font("Helvetica", "I", 9)
    pdf.multi_cell(0, 5, "Clinical Impression: Stage G3b Moderate-to-Severe CKD with Proteinuria. KDIGO guidelines advise RAAS blockade, moderate dietary protein restriction (0.6-0.75 g/kg/day), sodium limitation (<2000mg/day), and personalized lifestyle interventions.")
    
    pdf.output(pdf_path)
    print(f"Sample files generated:\n  - {txt_path}\n  - {pdf_path}")

if __name__ == "__main__":
    create_sample_files()
