"""
report_generator.py
Generates downloadable, user-friendly, simple medical receipts and clinical summary reports.
Contains patient demographics, simple diagnostic status, lab test results, prescribed medications,
and daily care recommendations (diet, superfoods, yoga, exercise).
"""

import os
import io
from datetime import datetime
from fpdf import FPDF
from fpdf.enums import XPos, YPos

def clean_pdf_text(s):
    if s is None:
        return ""
    s = str(s)
    unicode_replacements = [
        ("\u2013", "-"),  # en dash
        ("\u2014", "--"), # em dash
        ("\u2018", "'"),  # left single quote
        ("\u2019", "'"),  # right single quote
        ("\u201c", '"'),  # left double quote
        ("\u201d", '"'),  # right double quote
        ("\u2022", "*"),  # bullet
        ("\u2265", ">="), # greater than or equal
        ("\u2264", "<="), # less than or equal
        ("\u00b2", "2"),  # superscript 2
        ("\u00b3", "3"),  # superscript 3
        ("\u2192", "->"), # right arrow
        ("\u2794", "->"), # heavy right arrow
        ("\u2026", "..."),# ellipsis
        ("\u00a0", " "),  # non-breaking space
        ("\u00b1", "+/-"),# plus-minus
    ]
    for orig, rep in unicode_replacements:
        s = s.replace(orig, rep)
    return s.encode("latin-1", "replace").decode("latin-1")

class SafePDF(FPDF):
    """
    Subclass of FPDF that transparently sanitizes all text passed to cell()
    and multi_cell() to prevent FPDFUnicodeEncodingException.
    """
    def cell(self, *args, **kwargs):
        if "text" in kwargs:
            kwargs["text"] = clean_pdf_text(kwargs["text"])
        elif len(args) >= 3:
            args = list(args)
            args[2] = clean_pdf_text(args[2])
            args = tuple(args)
        return super().cell(*args, **kwargs)

    def multi_cell(self, *args, **kwargs):
        if "text" in kwargs:
            kwargs["text"] = clean_pdf_text(kwargs["text"])
        elif len(args) >= 3:
            args = list(args)
            args[2] = clean_pdf_text(args[2])
            args = tuple(args)
        return super().multi_cell(*args, **kwargs)

def generate_pdf_report(record_data):
    """
    Builds a simple, elegant, patient-friendly medical receipt & summary report.
    """
    pdf = SafePDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    
    # Theme Palette
    NAVY = (26, 82, 118)      # Deep navy #1A5276
    DARK = (30, 41, 59)       # Dark charcoal
    GRAY = (100, 116, 139)     # Soft slate gray
    LIGHT_BG = (248, 250, 252) # Off-white background
    BORDER_COL = (203, 213, 225)
    
    # -------------------------------------------------------------
    # 1. HEADER BANNER
    # -------------------------------------------------------------
    pdf.set_fill_color(*NAVY)
    pdf.rect(10, 10, 190, 20, "F")
    
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 15)
    pdf.set_y(13)
    pdf.cell(0, 6, "NEFRO-AI HEALTHCARE RECEIPT & MEDICAL SUMMARY", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
    pdf.set_font("Helvetica", "", 8.5)
    pdf.cell(0, 4, "AI-Powered Kidney Risk Assessment & Personalized Care Plan", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
    
    pdf.set_y(34)
    pdf.set_text_color(*GRAY)
    pdf.set_font("Helvetica", "I", 8)
    pdf.cell(0, 4, f"Date: {datetime.now().strftime('%B %d, %Y at %H:%M')}", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="R")
    pdf.ln(2)

    # -------------------------------------------------------------
    # 2. PATIENT DETAILS CARD
    # -------------------------------------------------------------
    patient_name = record_data.get("patient_name", "Patient")
    age = record_data.get("age", "N/A")
    gender = record_data.get("gender", "N/A")
    record_id = record_data.get("record_id", "REC-01")
    username = record_data.get("username", "Clinician")

    pdf.set_fill_color(240, 247, 255)
    pdf.set_draw_color(189, 215, 238)
    pdf.set_line_width(0.4)
    pdf.rect(10, pdf.get_y(), 190, 18, "FD")
    
    pdf.set_text_color(*DARK)
    pdf.set_font("Helvetica", "B", 9.5)
    pdf.cell(95, 5, f" Patient Name: {patient_name}", new_x=XPos.RIGHT, new_y=YPos.TOP)
    pdf.cell(95, 5, f" Receipt ID: {record_id}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("Helvetica", "", 9)
    pdf.cell(95, 5, f" Age / Gender: {age} Yrs | {gender}", new_x=XPos.RIGHT, new_y=YPos.TOP)
    pdf.cell(95, 5, f" Doctor / User: {username}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(5)

    # -------------------------------------------------------------
    # 3. SIMPLE HEALTH STATUS BANNER
    # -------------------------------------------------------------
    pred = record_data.get("prediction", {})
    is_ckd = pred.get("is_ckd", False)
    risk_pct = pred.get("risk_percentage", 0.0)
    kdigo = pred.get("kdigo_stage", {})
    stage_name = kdigo.get("stage", "Stage G0 / Normal")
    stage_label = kdigo.get("label", "Optimal Health")

    if not is_ckd or risk_pct < 50.0:
        bg_color = (212, 237, 218)   # Soft green
        border_col = (40, 167, 69)    # Green
        text_col = (21, 87, 36)
        status_heading = "HEALTHY KIDNEYS - NO KIDNEY DISEASE DETECTED"
        status_advice = "Your kidney tests (Creatinine, eGFR, Blood Pressure) are in healthy normal ranges. Continue good hydration!"
    elif risk_pct >= 80.0:
        bg_color = (248, 215, 218)   # Soft red
        border_col = (220, 53, 69)    # Red
        text_col = (114, 28, 36)
        status_heading = f"CRITICAL KIDNEY CARE REQUIRED: {stage_name}"
        status_advice = "Significant kidney reduction detected. Please consult a Nephrologist immediately for medication and diet management."
    elif risk_pct >= 65.0:
        bg_color = (255, 243, 205)   # Soft orange
        border_col = (253, 126, 20)   # Orange
        text_col = (133, 100, 4)
        status_heading = f"MODERATE KIDNEY ATTENTION NEEDED: {stage_name}"
        status_advice = "Moderate kidney change detected. Follow the prescribed medications and diet plan below."
    else:
        bg_color = (255, 243, 205)   # Soft yellow
        border_col = (255, 193, 7)
        text_col = (133, 100, 4)
        status_heading = f"MILD KIDNEY CHANGE: {stage_name}"
        status_advice = "Early kidney changes identified. Keep blood pressure controlled and monitor diet yearly."

    pdf.set_fill_color(*bg_color)
    pdf.set_draw_color(*border_col)
    pdf.set_line_width(0.6)
    pdf.rect(10, pdf.get_y(), 190, 20, "FD")
    
    pdf.set_text_color(*text_col)
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 5.5, f" {status_heading}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("Helvetica", "B", 8.5)
    pdf.cell(95, 4.5, f" Risk Probability Score: {risk_pct}%", new_x=XPos.RIGHT, new_y=YPos.TOP)
    pdf.cell(95, 4.5, f" Kidney Stage: {stage_name} ({stage_label})", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("Helvetica", "", 8)
    pdf.cell(0, 4.5, f" Summary Advice: {status_advice}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(5)

    # -------------------------------------------------------------
    # 4. SIMPLE LAB TEST RESULTS TABLE
    # -------------------------------------------------------------
    pdf.set_text_color(*NAVY)
    pdf.set_font("Helvetica", "B", 10.5)
    pdf.cell(0, 6, "1. YOUR LAB TEST RESULTS & VITALS", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    
    inputs = record_data.get("input_parameters", {})
    sc_val = inputs.get("SerumCreatinine", inputs.get("sc", 0.90))
    gfr_val = inputs.get("GFR", inputs.get("grf", 100.0))
    bun_val = inputs.get("BUNLevels", inputs.get("bu", 14.0))
    prot_val = inputs.get("ProteinInUrine", inputs.get("al", 0.0))
    acr_val = inputs.get("ACR", 10.0)
    hemo_val = inputs.get("HemoglobinLevels", inputs.get("hemo", 14.5))
    sbp_val = inputs.get("SystolicBP", inputs.get("bp", 120))
    dbp_val = inputs.get("DiastolicBP", 80)

    lab_items = [
        ("Serum Creatinine (Waste Clearance)", f"{sc_val} mg/dL", "0.60 - 1.20 mg/dL", "High" if float(sc_val) > 1.3 else "Normal"),
        ("eGFR (Kidney Filtration Rate)", f"{gfr_val} mL/min", ">= 90 mL/min", "Low" if float(gfr_val) < 60 else "Normal"),
        ("Blood Urea Nitrogen (BUN)", f"{bun_val} mg/dL", "7.0 - 20.0 mg/dL", "High" if float(bun_val) > 20 else "Normal"),
        ("Protein in Urine", f"{prot_val} g/day", "< 0.15 g/day", "High" if float(prot_val) > 0.3 else "Normal"),
        ("Albumin-Creatinine Ratio (ACR)", f"{acr_val} mg/g", "< 30 mg/g", "High" if float(acr_val) > 30 else "Normal"),
        ("Hemoglobin (Blood Count)", f"{hemo_val} g/dL", "13.5 - 17.5 g/dL", "Low" if float(hemo_val) < 12.0 else "Normal"),
        ("Blood Pressure", f"{sbp_val} / {dbp_val} mmHg", "< 120/80 mmHg", "High" if float(sbp_val) >= 130 else "Normal"),
    ]
    
    # Table Header
    pdf.set_fill_color(220, 230, 242)
    pdf.set_draw_color(*BORDER_COL)
    pdf.set_font("Helvetica", "B", 8)
    pdf.set_text_color(*DARK)
    pdf.cell(75, 5, "Lab Test Name", border=1, fill=True)
    pdf.cell(40, 5, "Your Result", border=1, fill=True)
    pdf.cell(45, 5, "Normal Range", border=1, fill=True)
    pdf.cell(30, 5, "Status", border=1, fill=True, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    
    pdf.set_font("Helvetica", "", 8)
    fill_row = False
    for name, val, ref, status in lab_items:
        fill_row = not fill_row
        pdf.set_fill_color(248, 250, 252) if fill_row else pdf.set_fill_color(255, 255, 255)
            
        pdf.cell(75, 4.5, name, border=1, fill=True)
        pdf.cell(40, 4.5, str(val), border=1, fill=True)
        pdf.cell(45, 4.5, ref, border=1, fill=True)
        
        if status == "Normal":
            pdf.set_text_color(40, 167, 69)
            pdf.cell(30, 4.5, "Normal", border=1, fill=True, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        else:
            pdf.set_text_color(220, 53, 69)
            pdf.cell(30, 4.5, f"Attention ({status})", border=1, fill=True, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.set_text_color(*DARK)
    pdf.ln(3)

    # -------------------------------------------------------------
    # 5. PRESCRIBED MEDICATIONS & TABLETS
    # -------------------------------------------------------------
    tablets = record_data.get("prescribed_tablets", [])
    if tablets:
        pdf.set_text_color(*NAVY)
        pdf.set_font("Helvetica", "B", 10.5)
        pdf.cell(0, 6, "2. PRESCRIBED MEDICATIONS & TABLETS", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.set_text_color(*DARK)
        
        for med in tablets[:4]:
            pdf.set_font("Helvetica", "B", 8.5)
            pdf.cell(0, 4.5, f"* {med['drug_name']} ({med['class']})", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            pdf.set_font("Helvetica", "", 8)
            pdf.cell(0, 4, f"   Dose: {med['standard_dose']} | Purpose: {med['indication']}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            pdf.ln(1)
        pdf.ln(2)

    # -------------------------------------------------------------
    # 6. SIMPLE DIET & SUPERFOODS
    # -------------------------------------------------------------
    diet = record_data.get("diet_plan", {})
    if diet:
        pdf.set_text_color(*NAVY)
        pdf.set_font("Helvetica", "B", 10.5)
        pdf.cell(0, 6, "3. DAILY DIET & FOOD RECOMMENDATIONS", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.set_text_color(*DARK)
        
        pdf.set_font("Helvetica", "B", 8)
        pdf.cell(0, 4, f"Daily Salt Limit: {diet.get('daily_sodium_target', '< 2,000 mg/day')} | Water Limit: {diet.get('daily_fluid_target', '2.0 L/day')}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.ln(1)
        
        pdf.set_font("Helvetica", "B", 8)
        pdf.cell(95, 4.5, "Recommended Kidney Foods (Superfoods):", new_x=XPos.RIGHT, new_y=YPos.TOP)
        pdf.cell(95, 4.5, "Foods to Restrict / Avoid:", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        
        pdf.set_font("Helvetica", "", 7.5)
        recs = diet.get("recommended_foods", [])[:4]
        avoids = diet.get("foods_to_avoid", [])[:4]
        max_rows = max(len(recs), len(avoids))
        for r_i in range(max_rows):
            left = f"* {recs[r_i]['food']}" if r_i < len(recs) else ""
            right = f"* {avoids[r_i]['food']}" if r_i < len(avoids) else ""
            pdf.cell(95, 4, left[:55], new_x=XPos.RIGHT, new_y=YPos.TOP)
            pdf.cell(95, 4, right[:55], new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.ln(3)

    # -------------------------------------------------------------
    # 7. SIMPLE YOGA & EXERCISE PLAN
    # -------------------------------------------------------------
    yogas = record_data.get("yoga_program", [])
    if yogas:
        pdf.set_text_color(*NAVY)
        pdf.set_font("Helvetica", "B", 10.5)
        pdf.cell(0, 6, "4. DAILY YOGA & EXERCISE PLAN", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.set_text_color(*DARK)
        
        pdf.set_font("Helvetica", "", 7.5)
        for y_item in yogas[:3]:
            pdf.cell(0, 3.8, f"* {y_item['name']}: {y_item['duration']} - Benefit: {y_item['renal_benefit']}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.ln(3)

    # -------------------------------------------------------------
    # 8. PATIENT RECEIPT DISCLAIMER & SIGNATURE
    # -------------------------------------------------------------
    pdf.set_font("Helvetica", "I", 7.5)
    pdf.set_text_color(*GRAY)
    pdf.multi_cell(0, 3.5, "DISCLAIMER: This document is a computer-generated medical summary receipt based on your lab parameters. It provides evidence-based guidance for educational purposes. Please consult your physician for formal diagnosis and prescription adjustments.")
    
    return pdf.output()
