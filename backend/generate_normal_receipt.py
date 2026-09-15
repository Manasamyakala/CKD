"""
generate_normal_receipt.py
Generates a healthy/normal control lab report receipt in PDF and TXT format.
"""

import os
from fpdf import FPDF
from fpdf.enums import XPos, YPos

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")

def create_normal_receipt():
    os.makedirs(DATA_DIR, exist_ok=True)
    txt_path = os.path.join(DATA_DIR, "sample_receipt_normal.txt")
    pdf_path = os.path.join(DATA_DIR, "sample_receipt_normal.pdf")
    
    content = """METROPOLITAN HEALTH & CLINICAL DIAGNOSTICS
Accredited Reference Laboratory | License: LAB-METRO-2026-4401
----------------------------------------------------------------------
ROUTINE PREVENTATIVE MEDICAL REPORT & RECEIPT
Patient Name: Emily Watson              Age: 38 Years
Gender: Female                          Date: 15-Sep-2026
Ordering Physician: Dr. Michael Thorne  Test: Comprehensive Health & Kidney Screen
----------------------------------------------------------------------
LABORATORY INVESTIGATION FINDINGS:

1. RENAL FUNCTION TESTS (RFT / KFT):
   - Serum Creatinine (SC)            : 0.82 mg/dL     (Ref: 0.50 - 1.10)  [NORMAL]
   - Blood Urea Nitrogen (BUN)        : 13.4 mg/dL     (Ref: 7.0 - 20.0)   [NORMAL]
   - Estimated GFR (eGFR)             : 104.5 mL/min   (Ref: >= 90)        [OPTIMAL]
   - Serum Electrolytes Sodium (Na)   : 140.0 mEq/L    (Ref: 135 - 145)    [NORMAL]
   - Serum Electrolytes Potassium (K) : 4.10 mEq/L     (Ref: 3.5 - 5.0)    [NORMAL]
   - Serum Electrolytes Calcium (Ca)  : 9.40 mg/dL     (Ref: 8.5 - 10.5)   [NORMAL]
   - Serum Electrolytes Phosphorus (P): 3.30 mg/dL     (Ref: 2.5 - 4.5)    [NORMAL]

2. URINALYSIS & PROTEIN:
   - Protein In Urine                 : 0.04 g/day     (Ref: < 0.15)       [NEGATIVE]
   - Albumin-to-Creatinine Ratio (ACR): 8.5 mg/g       (Ref: < 30)         [NORMAL]

3. HEMATOLOGY & METABOLIC:
   - Hemoglobin Levels (Hb)           : 14.2 g/dL      (Ref: 12.0 - 16.0)  [NORMAL]
   - Fasting Blood Sugar (FBS)        : 88.0 mg/dL     (Ref: 70 - 100)     [OPTIMAL]
   - HbA1c                            : 5.2 %          (Ref: < 5.7%)       [NORMAL]

4. VITALS & PHYSIOLOGY:
   - Blood Pressure (BP)              : 116/74 mmHg    (Ref: < 120/80)     [OPTIMAL]
   - Body Mass Index (BMI)            : 22.4           (Ref: 18.5 - 24.9)  [NORMAL WEIGHT]
----------------------------------------------------------------------
CLINICAL IMPRESSION:
All evaluated renal and metabolic parameters are strictly within normal reference limits.
Glomerular filtration rate is optimal with no evidence of pathological proteinuria.
Routine annual preventative follow-up recommended.
======================================================================
"""

    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(content)
        
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 10, "METROPOLITAN HEALTH & CLINICAL DIAGNOSTICS", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 6, "Accredited Reference Laboratory | License: LAB-METRO-2026-4401", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
    pdf.line(10, 28, 200, 28)
    pdf.ln(5)
    
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 7, "ROUTINE PREVENTATIVE MEDICAL REPORT & RECEIPT", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(95, 6, "Patient Name: Emily Watson", new_x=XPos.RIGHT, new_y=YPos.TOP)
    pdf.cell(95, 6, "Age: 38 Years | Gender: Female", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.cell(95, 6, "Date: 15-Sep-2026", new_x=XPos.RIGHT, new_y=YPos.TOP)
    pdf.cell(95, 6, "Test: Comprehensive Health & Kidney Screen", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.line(10, 48, 200, 48)
    pdf.ln(5)
    
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 7, "LABORATORY INVESTIGATION FINDINGS:", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    
    lines = [
        ("Serum Creatinine (SC)", "0.82 mg/dL", "0.50 - 1.10", "NORMAL"),
        ("Blood Urea Nitrogen (BUN)", "13.4 mg/dL", "7.0 - 20.0", "NORMAL"),
        ("Estimated GFR (eGFR)", "104.5 mL/min", ">= 90", "OPTIMAL"),
        ("Protein In Urine", "0.04 g/day", "< 0.15", "NEGATIVE"),
        ("Albumin-to-Creatinine Ratio (ACR)", "8.5 mg/g", "< 30", "NORMAL"),
        ("Hemoglobin Levels (Hb)", "14.2 g/dL", "12.0 - 16.0", "NORMAL"),
        ("Fasting Blood Sugar (FBS)", "88.0 mg/dL", "70 - 100", "OPTIMAL"),
        ("HbA1c", "5.2 %", "< 5.7%", "NORMAL"),
        ("Serum Sodium (Na)", "140.0 mEq/L", "135 - 145", "NORMAL"),
        ("Serum Potassium (K)", "4.10 mEq/L", "3.5 - 5.0", "NORMAL"),
        ("Serum Calcium (Ca)", "9.40 mg/dL", "8.5 - 10.5", "NORMAL"),
        ("Serum Phosphorus (P)", "3.30 mg/dL", "2.5 - 4.5", "NORMAL"),
        ("Blood Pressure (BP)", "116/74 mmHg", "< 120/80", "OPTIMAL"),
        ("Body Mass Index (BMI)", "22.4", "18.5 - 24.9", "NORMAL WEIGHT")
    ]
    
    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(75, 6, "Test Parameter", border=1)
    pdf.cell(35, 6, "Result", border=1)
    pdf.cell(40, 6, "Reference Range", border=1)
    pdf.cell(40, 6, "Status", border=1, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    
    pdf.set_font("Helvetica", "", 9)
    for param, res, ref, status in lines:
        pdf.cell(75, 5, param, border=1)
        pdf.cell(35, 5, res, border=1)
        pdf.cell(40, 5, ref, border=1)
        pdf.cell(40, 5, status, border=1, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        
    pdf.ln(5)
    pdf.set_font("Helvetica", "I", 9)
    pdf.multi_cell(0, 5, "Clinical Impression: Optimal renal health and metabolic function. No evidence of renal insufficiency or proteinuria.")
    pdf.output(pdf_path)
    print(f"Normal receipt generated:\n  - {txt_path}\n  - {pdf_path}")

if __name__ == "__main__":
    create_normal_receipt()
