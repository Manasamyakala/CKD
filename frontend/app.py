"""
app.py
CKD Risk Assessment & Personalized Healthcare
Dynamic clinical diagnostic framework with:
- Automated PDF/receipt parsing (Name, Gender, Age, Biomarkers, Lifestyle)
- Real-time CKD Stage identification & risk probability
- Prescribed tablets & medications (KDIGO Table 13)
- Personalized lifestyle care (Diet, Superfoods, Yoga, Exercise)
- MongoDB Compass storage at mongodb://localhost:27017
- Model performance metrics
"""

import os
import re
import sys
import time
import pandas as pd
import numpy as np
import streamlit as st

# Add project root to sys.path
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from backend.database import db_manager
from backend.predictor import NefroPredictor
from backend.recommendation_engine import generate_recommendations
from backend.receipt_parser import parse_medical_receipt
from frontend.report_generator import generate_pdf_report

# ==========================================
# PAGE CONFIGURATION
# ==========================================
st.set_page_config(
    page_title="CKD Risk Assessment & Personalized Healthcare",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Clean, Patient-Friendly Medical Styling
st.markdown("""
<style>
    /* Hide Streamlit top-right 3 dots menu, header toolbar, deploy button, and footer */
    #MainMenu {visibility: hidden !important; display: none !important;}
    header {visibility: hidden !important; display: none !important;}
    footer {visibility: hidden !important; display: none !important;}
    .stDeployButton {display:none !important; visibility: hidden !important;}
    [data-testid="stDecoration"] {display:none !important; visibility: hidden !important;}
    [data-testid="stToolbar"] {display:none !important; visibility: hidden !important;}
    [data-testid="stHeader"] {display:none !important; visibility: hidden !important;}
    [data-testid="stMainMenu"] {display:none !important; visibility: hidden !important;}
    [data-testid="stAppDeployButton"] {display:none !important; visibility: hidden !important;}

    .main-header {
        font-size: 2.1rem;
        font-weight: 700;
        color: #1a5276;
        margin-bottom: 0.5rem;
    }
    .flow-bar {
        background: linear-gradient(90deg, #eef5fc, #f0fdf4);
        border: 1px solid #d0e1fd;
        border-radius: 8px;
        padding: 10px 18px;
        font-size: 0.95rem;
        font-weight: 600;
        color: #2c3e50;
        margin-bottom: 1.2rem;
        display: flex;
        justify-content: space-around;
        align-items: center;
    }
    .level-card-healthy {
        background-color: #eafaf1;
        border: 2px solid #27ae60;
        border-radius: 10px;
        padding: 18px;
        margin-bottom: 15px;
    }
    .level-card-moderate {
        background-color: #fef9e7;
        border: 2px solid #f39c12;
        border-radius: 10px;
        padding: 18px;
        margin-bottom: 15px;
    }
    .level-card-severe {
        background-color: #fdedec;
        border: 2px solid #e74c3c;
        border-radius: 10px;
        padding: 18px;
        margin-bottom: 15px;
    }
    .metric-pill {
        display: inline-block;
        padding: 4px 10px;
        border-radius: 16px;
        font-weight: 600;
        font-size: 0.85rem;
    }
    .pill-green { background-color: #d4edda; color: #155724; }
    .pill-orange { background-color: #ffeeba; color: #856404; }
    .pill-red { background-color: #f8d7da; color: #721c24; }
    .stButton>button {
        background-color: #1a5276;
        color: white;
        border-radius: 6px;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# SESSION STATE INITIALIZATION
# ==========================================
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "user_info" not in st.session_state:
    st.session_state.user_info = None
if "current_prediction" not in st.session_state:
    st.session_state.current_prediction = None
if "current_recommendations" not in st.session_state:
    st.session_state.current_recommendations = None
if "last_inputs" not in st.session_state:
    st.session_state.last_inputs = {}
if "extracted_data" not in st.session_state:
    st.session_state.extracted_data = {}
if "selected_model" not in st.session_state:
    st.session_state.selected_model = "tri_ensemble"

def safe_float(val, default=0.0):
    try:
        if val is None or val == "N/A" or str(val).strip() == "":
            return default
        return float(val)
    except (ValueError, TypeError):
        return default

def safe_int(val, default=0):
    try:
        if val is None or val == "N/A" or str(val).strip() == "":
            return default
        return int(float(val))
    except (ValueError, TypeError):
        return default

@st.cache_resource
def load_predictors():
    return {
        "tri_ensemble": NefroPredictor(model_type="tri_ensemble"),
        "dataset_b": NefroPredictor(model_type="dataset_b"),
        "dataset_a": NefroPredictor(model_type="dataset_a"),
        "dataset_c": NefroPredictor(model_type="dataset_c")
    }

predictors = load_predictors()

# ==========================================
# SIDEBAR: AUTHENTICATION & SETTINGS
# ==========================================
with st.sidebar:
    st.image("https://img.icons8.com/color/96/kidney.png", width=65)
    st.markdown("### NefroAI Care")
    st.caption("AI-Powered Kidney Risk Assessment")
    st.divider()

    # MongoDB Connection Status
    if db_manager.is_connected():
        st.success("Welcome to NefroAI Care")
    else:
        st.warning(" MongoDB: Offline")

    st.divider()

    # Authentication Interface
    if not st.session_state.authenticated:
        st.subheader("Sign In")
        auth_mode = st.radio("Mode:", ["Login", "Register"], horizontal=True)

        if auth_mode == "Login":
            login_user = st.text_input("Username", key="login_user")
            login_pass = st.text_input("Password", type="password", key="login_pass")
            
            if st.button("Log In", use_container_width=True):
                if login_user and login_pass:
                    ok, res = db_manager.authenticate_user(login_user, login_pass)
                    if ok:
                        st.session_state.authenticated = True
                        st.session_state.user_info = res
                        st.rerun()
                    else:
                        st.error(res)
                else:
                    st.warning("Please enter username and password.")

        else:
            reg_user = st.text_input("New Username (alphabets only)", key="reg_user", help="Only letters permitted (no numbers or symbols)")
            reg_name = st.text_input("Full Name (alphabets only)", key="reg_name", help="Only letters permitted (no numbers)")
            reg_email = st.text_input("Email (must end with @gmail.com or @gamil.com)", key="reg_email", placeholder="user@gmail.com")
            reg_pass = st.text_input("New Password", type="password", key="reg_pass")
            
            if st.button("Create Account", use_container_width=True):
                reg_user_clean = reg_user.strip()
                reg_name_clean = reg_name.strip()
                reg_email_clean = reg_email.strip().lower()
                
                if not reg_user_clean or not reg_name_clean or not reg_email_clean or not reg_pass:
                    st.warning("Please fill in all registration fields.")
                elif not re.match(r"^[a-zA-Z]+$", reg_user_clean):
                    st.error("Username must contain only alphabets (no numbers or special characters).")
                elif not re.match(r"^[a-zA-Z\s]+$", reg_name_clean):
                    st.error("Full Name must contain only alphabets (no numbers or symbols).")
                elif not (reg_email_clean.endswith("@gmail.com") or reg_email_clean.endswith("@gamil.com")):
                    st.error("Email must end with @gmail.com (or @gamil.com).")
                elif not re.match(r"^[a-zA-Z0-9._%+-]+@(gmail|gamil)\.com$", reg_email_clean):
                    st.error("Please enter a valid email address ending with @gmail.com (or @gamil.com).")
                elif len(reg_pass) < 4:
                    st.error("Password must be at least 4 characters long.")
                else:
                    ok, msg = db_manager.register_user(reg_user_clean, reg_pass, reg_email_clean, reg_name_clean, "patient")
                    if ok:
                        st.success(f"{msg} You can now switch to 'Login' mode to sign in.")
                    else:
                        st.error(msg)

    else:
        user = st.session_state.user_info
        st.markdown(f"**Patient/Doctor:** `{user.get('username')}`")
        st.markdown(f"**Name:** {user.get('full_name', 'Clinician')}")
        
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.authenticated = False
            st.session_state.user_info = None
            st.session_state.current_prediction = None
            st.session_state.current_recommendations = None
            st.session_state.extracted_data = {}
            st.rerun()

        st.divider()
        st.subheader("Model Engine")
        model_options = [
            "Tri-Dataset Ensemble (Datasets A, B & C - Highest Accuracy)",
            "Dataset B Model (1,659 Patients, Kaggle)",
            "Dataset A Model (400 Patients, UCI Apollo)",
            "Dataset C Model (200 Patients, Enam Medical)"
        ]
        sel_idx = 0
        if st.session_state.selected_model == "dataset_b":
            sel_idx = 1
        elif st.session_state.selected_model == "dataset_a":
            sel_idx = 2
        elif st.session_state.selected_model == "dataset_c":
            sel_idx = 3

        model_choice = st.radio("Prediction Engine:", model_options, index=sel_idx)
        if "Tri-Dataset" in model_choice:
            st.session_state.selected_model = "tri_ensemble"
        elif "Dataset B" in model_choice:
            st.session_state.selected_model = "dataset_b"
        elif "Dataset A" in model_choice:
            st.session_state.selected_model = "dataset_a"
        else:
            st.session_state.selected_model = "dataset_c"

# ==========================================
# MAIN PAGE HEADER & WORKFLOW ARROWS
# ==========================================
st.markdown('<div class="main-header">🩺 CKD Risk Assessment & Personalized Healthcare</div>', unsafe_allow_html=True)

# User-friendly workflow indicator with arrows
st.markdown("""
<div class="flow-bar">
    <span>📄 1. Upload Lab Report / Receipt</span>
    <span>➔</span>
    <span>🔍 2. AI Risk & KDIGO Prediction</span>
    <span>➔</span>
    <span>💊 3. Prescribed Tablets & Personal Care</span>
</div>
""", unsafe_allow_html=True)

if not st.session_state.authenticated:
    st.info(" Please log in with your credentials or create a new account in the sidebar to assess patient kidney health.")
    st.stop()

# ==========================================
# TABS INTERFACE
# ==========================================
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    " 1. Upload Report & Patient Data",
    " 2. CKD Prediction & Tablets",
    " 3. Personalized Diet & Yoga",
    " 4. MongoDB Records",
    " 5. Model Performance"
])

# ----------------------------------------------------
# TAB 1: UPLOAD REPORT & DYNAMIC EXTRACTION
# ----------------------------------------------------
with tab1:
    st.subheader("Medical Report & Receipt Ingestion")
    st.write("Upload a lab report or select a sample patient. If uploading general health/fever reports without renal markers, parameters default to normal healthy baselines.")

    col_up, col_btn1, col_btn2, col_btn3 = st.columns([3, 1.2, 1.2, 1.2])
    with col_up:
        uploaded_doc = st.file_uploader(
            "Upload Patient Medical Report (PDF or TXT)",
            type=["pdf", "txt", "csv"],
            help="Dynamic parser extracts Patient Name, Age, Gender, Serum Creatinine, eGFR, BUN, BP, Albumin, etc."
        )

    with col_btn1:
        st.markdown("**Moderate CKD**")
        if st.button("📄 Sample: CKD (G3b)", use_container_width=True, help="Loads Alex Carter (Stage G3b, Creatinine 1.85, eGFR 44.2)"):
            sample_path = os.path.join(ROOT_DIR, "data", "sample_receipt.pdf")
            if os.path.exists(sample_path):
                with open(sample_path, "rb") as f:
                    res = parse_medical_receipt(f.read(), "sample_receipt.pdf")
                    st.session_state.extracted_data = res["extracted_values"]
                    st.success(f"Dynamically extracted {res['matched_count']} fields for {res['patient_name']}!")
                    st.rerun()

    with col_btn2:
        st.markdown("**Healthy Control**")
        if st.button("🟢 Sample: Normal", use_container_width=True, help="Loads Emily Watson (Stage G0, Optimal GFR 104.5, Creatinine 0.82)"):
            sample_norm_path = os.path.join(ROOT_DIR, "data", "sample_receipt_normal.pdf")
            if os.path.exists(sample_norm_path):
                with open(sample_norm_path, "rb") as f:
                    res = parse_medical_receipt(f.read(), "sample_receipt_normal.pdf")
                    st.session_state.extracted_data = res["extracted_values"]
                    st.success(f"Dynamically extracted {res['matched_count']} fields for {res['patient_name']}!")
                    st.rerun()

    with col_btn3:
        st.markdown("**Reset Baseline**")
        if st.button("🧹 Clear / Reset", use_container_width=True, help="Resets parameters to normal healthy baseline"):
            st.session_state.extracted_data = {}
            st.session_state.current_prediction = None
            st.session_state.current_recommendations = None
            st.success("Reset form to normal healthy baseline!")
            st.rerun()

    # Dynamic extraction on uploaded file
    if uploaded_doc is not None:
        doc_bytes = uploaded_doc.read()
        res = parse_medical_receipt(doc_bytes, uploaded_doc.name)
        st.session_state.extracted_data = res["extracted_values"]
        st.success(f"Dynamically extracted {res['matched_count']} clinical & lifestyle values from '{uploaded_doc.name}'!")

    ext = st.session_state.get("extracted_data", {})
    has_data = bool(ext)
    show_manual = st.session_state.get("show_manual_form", False)

    submit_btn = False

    if not has_data and not show_manual:
        st.markdown("""
        <div style="background-color:#f8fafc; border:2px dashed #cbd5e1; border-radius:10px; padding:35px 20px; text-align:center; margin-top:20px; margin-bottom:25px;">
            <h3 style="color:#1a5276; margin-bottom:8px;">📄 No Patient Lab Report Uploaded Yet</h3>
            <p style="color:#475569; font-size:1.02rem; margin-bottom:18px;">
                Upload a patient medical lab report (PDF or TXT) above, or select a sample report to dynamically parse and extract clinical parameters.
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        c_sp1, c_man_btn, c_sp2 = st.columns([1.5, 2, 1.5])
        with c_man_btn:
            if st.button("✏️ Or Manually Enter Patient Parameters", use_container_width=True):
                st.session_state.show_manual_form = True
                st.rerun()

    else:
        # Show Quick Extracted Summary Badge Card if data exists
        if ext:
            sc_num = safe_float(ext.get("SerumCreatinine"), 0.90)
            gfr_num = safe_float(ext.get("GFR"), 100.0)
            sbp_num = safe_int(ext.get("SystolicBP"), 120)
            dbp_num = safe_int(ext.get("DiastolicBP"), 80)
            prot_num = safe_float(ext.get("ProteinInUrine"), 0.0)
            
            sc_disp = ext.get("SerumCreatinine", "Normal (0.90)")
            gfr_disp = ext.get("GFR", "Optimal (100)")
            bp_disp = f"{sbp_num}/{dbp_num}"
            prot_disp = ext.get("ProteinInUrine", "0.0")
            
            sc_pill = "pill-red" if sc_num > 1.3 else "pill-green"
            gfr_pill = "pill-red" if gfr_num < 60 else "pill-green"
            bp_pill = "pill-orange" if sbp_num >= 130 else "pill-green"
            prot_pill = "pill-orange" if prot_num > 0.3 else "pill-green"
            
            st.markdown(f"""
            <div style="background-color:#f0f7ff; border:1px solid #bdd7ee; border-radius:8px; padding:12px; margin-top:10px; margin-bottom:15px;">
                <b>Patient Profile:</b> {ext.get('PatientName', 'Patient')} ({ext.get('Gender', 'Male')}, {safe_int(ext.get('Age'), 40)} yrs) | 
                <b>Serum Creatinine:</b> <span class="metric-pill {sc_pill}">{sc_disp} mg/dL</span> | 
                <b>eGFR:</b> <span class="metric-pill {gfr_pill}">{gfr_disp} mL/min</span> | 
                <b>Blood Pressure:</b> <span class="metric-pill {bp_pill}">{bp_disp} mmHg</span> | 
                <b>Urine Protein:</b> <span class="metric-pill {prot_pill}">{prot_disp} g/day</span>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("### Patient Parameters (Dynamically Populated)")
        
        patient_form = st.form("patient_clinical_form")
        with patient_form:
            # Section A: Demographics
            c1, c2, c3 = st.columns(3)
            with c1:
                p_name = st.text_input("Patient Name", value=str(ext.get("PatientName", "Patient")))
            with c2:
                p_age = st.number_input("Patient Age", min_value=18, max_value=105, value=safe_int(ext.get("Age"), 40))
            with c3:
                gen_idx = 1 if str(ext.get("Gender", "Male")).lower() == "female" else 0
                p_gender = st.selectbox("Gender", ["Male", "Female"], index=gen_idx)

            # Section B: Renal Function Test (RFT)
            st.markdown("#### 1. Renal Function Biomarkers")
            r1, r2, r3, r4 = st.columns(4)
            with r1:
                sc_val = safe_float(ext.get("SerumCreatinine"), 0.90)
                serum_creatinine = st.number_input("Serum Creatinine (mg/dL)", min_value=0.2, max_value=15.0, value=sc_val, step=0.05, help="Healthy range: 0.6 - 1.2 mg/dL")
            with r2:
                bun_val = safe_float(ext.get("BUNLevels"), 14.0)
                bun_levels = st.number_input("Blood Urea Nitrogen / BUN (mg/dL)", min_value=2.0, max_value=150.0, value=bun_val, step=0.5, help="Healthy range: 7 - 20 mg/dL")
            with r3:
                gfr_val = safe_float(ext.get("GFR"), 100.0)
                gfr = st.number_input("eGFR (mL/min/1.73m²)", min_value=5.0, max_value=160.0, value=gfr_val, step=1.0, help="Healthy range: >= 90 mL/min")
            with r4:
                hemo_val = safe_float(ext.get("HemoglobinLevels"), 14.5)
                hemo = st.number_input("Hemoglobin (g/dL)", min_value=4.0, max_value=20.0, value=hemo_val, step=0.1, help="Healthy range: 13.5 - 17.5 g/dL")

            # Section C: Urinalysis & Proteinuria
            st.markdown("#### 2. Urine Protein & Albumin")
            u1, u2 = st.columns(2)
            with u1:
                prot_val = safe_float(ext.get("ProteinInUrine"), 0.0)
                protein_urine = st.number_input("Protein In Urine (g/day)", min_value=0.0, max_value=10.0, value=prot_val, step=0.1, help="Healthy range: < 0.15 g/day")
            with u2:
                acr_val = safe_float(ext.get("ACR"), 10.0)
                acr = st.number_input("Albumin-to-Creatinine Ratio / ACR (mg/g)", min_value=0.0, max_value=500.0, value=acr_val, step=5.0, help="Healthy range: < 30 mg/g")

            # Section D: Vitals & Metabolic
            st.markdown("#### 3. Blood Pressure & Glucose")
            v1, v2, v3, v4 = st.columns(4)
            with v1:
                sbp_val = safe_int(ext.get("SystolicBP"), 120)
                systolic_bp = st.number_input("Systolic Blood Pressure (mmHg)", min_value=70, max_value=220, value=sbp_val)
            with v2:
                dbp_val = safe_int(ext.get("DiastolicBP"), 80)
                diastolic_bp = st.number_input("Diastolic Blood Pressure (mmHg)", min_value=40, max_value=140, value=dbp_val)
            with v3:
                fbs_val = safe_float(ext.get("FastingBloodSugar"), 90.0)
                fbs = st.number_input("Fasting Glucose (mg/dL)", min_value=50.0, max_value=400.0, value=fbs_val, step=1.0)
            with v4:
                a1c_val = safe_float(ext.get("HbA1c"), 5.4)
                hba1c = st.number_input("HbA1c (%)", min_value=3.5, max_value=16.0, value=a1c_val, step=0.1)

            # Section E: Electrolytes
            st.markdown("#### 4. Serum Electrolytes")
            e1, e2, e3, e4 = st.columns(4)
            with e1:
                na_val = safe_float(ext.get("SerumElectrolytesSodium"), 140.0)
                sodium = st.number_input("Sodium (mEq/L)", min_value=110.0, max_value=165.0, value=na_val, step=0.5)
            with e2:
                k_val = safe_float(ext.get("SerumElectrolytesPotassium"), 4.2)
                potassium = st.number_input("Potassium (mEq/L)", min_value=2.0, max_value=8.5, value=k_val, step=0.1)
            with e3:
                ca_val = safe_float(ext.get("SerumElectrolytesCalcium"), 9.5)
                calcium = st.number_input("Calcium (mg/dL)", min_value=5.0, max_value=15.0, value=ca_val, step=0.1)
            with e4:
                p_val = safe_float(ext.get("SerumElectrolytesPhosphorus"), 3.5)
                phosphorus = st.number_input("Phosphorus (mg/dL)", min_value=1.0, max_value=10.0, value=p_val, step=0.1)

            # Section F: Lifestyle & Symptoms
            st.markdown("#### 5. Lifestyle & Physical Symptoms")
            l1, l2, l3, l4 = st.columns(4)
            with l1:
                bmi_val = safe_float(ext.get("BMI"), 22.5)
                bmi = st.number_input("Body Mass Index (BMI)", min_value=12.0, max_value=55.0, value=bmi_val, step=0.2)
            with l2:
                diet_q = safe_float(ext.get("DietQuality"), 8.0)
                diet_quality = st.slider("Diet Quality Score (0: Poor, 10: Healthy)", 0.0, 10.0, diet_q, step=0.5)
            with l3:
                act_val = safe_float(ext.get("PhysicalActivity"), 4.0)
                activity = st.slider("Weekly Physical Activity (Hours)", 0.0, 15.0, act_val, step=0.5)
            with l4:
                sleep_q = safe_float(ext.get("SleepQuality"), 8.0)
                sleep_quality = st.slider("Sleep Quality Score (4: Poor, 10: Restful)", 4.0, 10.0, sleep_q, step=0.5)

            s1, s2, s3, s4 = st.columns(4)
            with s1:
                ed_idx = 1 if safe_int(ext.get("Edema"), 0) == 1 else 0
                has_edema = st.selectbox("Swelling / Peripheral Edema", ["No", "Yes"], index=ed_idx)
            with s2:
                fat_val = safe_int(ext.get("FatigueLevels"), 1)
                fatigue_lvl = st.slider("Fatigue Level (0-10)", 0, 10, fat_val)
            with s3:
                cramp_val = safe_int(ext.get("MuscleCramps"), 0)
                cramps_lvl = st.slider("Muscle Cramps (per week)", 0, 7, cramp_val)
            with s4:
                itch_val = safe_int(ext.get("Itching"), 0)
                itching_lvl = st.slider("Itching Severity (0-10)", 0, 10, itch_val)

            submit_btn = patient_form.form_submit_button("🔍 Predict CKD Risk & Generate Personalized Care Plan", use_container_width=True)

        if submit_btn:
            patient_dict = {
                "Age": p_age,
                "Gender": 1 if p_gender == "Female" else 0,
                "BMI": bmi,
                "PhysicalActivity": activity,
                "DietQuality": diet_quality,
                "SleepQuality": sleep_quality,
                "SystolicBP": systolic_bp,
                "DiastolicBP": diastolic_bp,
                "FastingBloodSugar": fbs,
                "HbA1c": hba1c,
                "SerumCreatinine": serum_creatinine,
                "BUNLevels": bun_levels,
                "GFR": gfr,
                "ProteinInUrine": protein_urine,
                "ACR": acr,
                "SerumElectrolytesSodium": sodium,
                "SerumElectrolytesPotassium": potassium,
                "SerumElectrolytesCalcium": calcium,
                "SerumElectrolytesPhosphorus": phosphorus,
                "HemoglobinLevels": hemo,
                "Edema": 1 if has_edema == "Yes" else 0,
                "FatigueLevels": fatigue_lvl,
                "MuscleCramps": cramps_lvl,
                "Itching": itching_lvl,
                "QualityOfLifeScore": 55,
                # Aliases for 10-feature model
                "sc": serum_creatinine,
                "bu": bun_levels,
                "bgr": fbs,
                "hemo": hemo,
                "pcv": round(hemo * 3.1, 1),
                "rc": round(hemo / 3.0, 2),
                "sg": 1.010 if protein_urine > 1.0 else 1.020,
                "al": 3 if protein_urine > 1.5 else (2 if protein_urine > 0.5 else 0),
                "sod": sodium,
                "pot": potassium
            }

            # Run Prediction
            active_pred = predictors[st.session_state.selected_model]
            pred_res = active_pred.predict(patient_dict)
            
            # Run Recommendation Engine
            recs = generate_recommendations(patient_dict, pred_res)

            # Update Session State
            st.session_state.current_prediction = pred_res
            st.session_state.current_recommendations = recs
            st.session_state.last_inputs = patient_dict
            st.session_state.last_patient_name = p_name

            # Save to MongoDB
            current_username = (st.session_state.user_info or {}).get("username", "demo_doctor")
            record_payload = {
                "username": current_username,
                "patient_name": p_name,
                "age": p_age,
                "gender": p_gender,
                "input_parameters": patient_dict,
                "prediction": pred_res,
                "prescribed_tablets": recs["prescribed_tablets"],
                "diet_plan": recs["diet_plan"],
                "yoga_program": recs["yoga_program"],
                "exercise_plan": recs["exercise_plan"],
                "telemetry": pred_res["telemetry"]
            }
            rec_id, db_msg = db_manager.save_patient_record(record_payload)
            st.session_state.last_record_id = rec_id

            st.success(f"Assessment complete! Results ready in Tab 2. Stored in MongoDB (`nefroai_ckd.patient_records`).")

# ----------------------------------------------------
# TAB 2: CKD PREDICTION & PRESCRIBED TABLETS
# ----------------------------------------------------
with tab2:
    if st.session_state.current_prediction is None:
        st.info("No active patient assessment found. Please upload a report or submit the form in **Tab 1**.")
    else:
        pred = st.session_state.current_prediction
        recs = st.session_state.current_recommendations
        inputs = st.session_state.last_inputs
        p_name = st.session_state.get("last_patient_name", "Patient")
        k_stage = pred["kdigo_stage"]
        risk_pct = pred["risk_percentage"]

        st.markdown(f"### Diagnostic Report for {p_name}")

        # Patient-Friendly Level Identifier Card based on 4-Stage Classification
        is_ckd = pred.get("is_ckd", False)
        four_stage = pred.get("four_stage_label", "Normal Stage" if not is_ckd else "Critical Stage")
        
        if four_stage == "Normal Stage" or not is_ckd:
            card_style = "level-card-healthy"
            level_text = "Normal Stage: Healthy Kidney Function (No CKD Detected)"
            icon = "🟢"
            advice = "All evaluated renal biomarkers (Serum Creatinine <= 1.0 mg/dL, eGFR >= 90 mL/min, Blood Pressure ~110/70, Proteinuria < 0.15 g/day) are within optimal reference limits. Kidneys are healthy."
        elif four_stage == "Medium Stage":
            card_style = "level-card-moderate"
            level_text = f"Medium Stage: Mild CKD ({k_stage['label']})"
            icon = "🟡"
            advice = "MEDIUM STAGE DETECTED (Mild CKD): Early kidney changes identified. Blood pressure regulation, healthy hydration, and annual renal screening advised."
        elif four_stage == "Critical Stage":
            card_style = "level-card-moderate"
            level_text = f"Critical Stage: Moderate-to-Severe CKD ({k_stage['label']})"
            icon = "🟠"
            advice = "CRITICAL STAGE DETECTED: Substantial reduction in kidney filtration rate. Nephrologist consultation, RAAS blockade, and dietary protein management indicated."
        else: # Advance Stage
            card_style = "level-card-severe"
            level_text = f"Advance Stage: Severe Kidney Failure / ESRD ({k_stage['label']})"
            icon = "🔴"
            advice = "ADVANCE STAGE DETECTED (Severe Risk): Critical loss of kidney filtration. Immediate nephrology referral and active preparation for renal replacement therapy (dialysis or transplant) required."

        st.markdown(f"""
        <div class="{card_style}">
            <h3 style="margin:0;">{icon} {level_text}</h3>
            <p style="font-size:1.1rem; margin:8px 0;"><b>CKD Risk Score:</b> {risk_pct}% | <b>KDIGO Stage:</b> {k_stage['stage']} - {k_stage['label']}</p>
            <p style="margin:0; color:#333;">{advice}</p>
        </div>
        """, unsafe_allow_html=True)

        st.progress(min(int(risk_pct), 100))

        # 4 Key Metrics Overview
        m1, m2, m3, m4 = st.columns(4)
        with m1:
            st.metric("Status", pred["prediction_label"], delta="Abnormal" if pred["is_ckd"] else "Normal", delta_color="inverse" if pred["is_ckd"] else "normal")
        with m2:
            st.metric("Risk Score", f"{risk_pct}%", help="AI Model Risk Probability")
        with m3:
            st.metric("KDIGO Stage", k_stage["stage"], delta=f"eGFR {inputs.get('GFR', 'N/A')}")
        with m4:
            st.metric("AI Inference", f"{pred['telemetry']['latency_ms']} ms", delta=f"{pred['telemetry']['memory_mb']} MB RAM")

        # Patient Explanation of Their Numbers
        st.markdown("---")
        st.markdown("#### 🩺 What Your Lab Numbers Mean:")
        c_exp1, c_exp2 = st.columns(2)
        with c_exp1:
            sc_val = inputs.get("SerumCreatinine", 1.0)
            gfr_val = inputs.get("GFR", 90.0)
            st.markdown(f"""
            - **Serum Creatinine ({sc_val} mg/dL):** {'⚠️ High. Waste products are accumulating due to reduced filtration.' if sc_val > 1.3 else '✅ Normal. Kidneys are clearing metabolic waste properly.'}
            - **eGFR ({gfr_val} mL/min):** {'⚠️ Reduced filtration rate (Below 60 indicates CKD).' if gfr_val < 60 else '✅ Optimal kidney filtration rate.'}
            """)
        with c_exp2:
            bp_val = f"{inputs.get('SystolicBP', 120)}/{inputs.get('DiastolicBP', 80)}"
            prot_val = inputs.get("ProteinInUrine", 0.0)
            st.markdown(f"""
            - **Blood Pressure ({bp_val} mmHg):** {'⚠️ Elevated. High pressure damages tiny kidney blood vessels.' if inputs.get('SystolicBP', 120) >= 130 else '✅ Well-controlled blood pressure.'}
            - **Urine Protein ({prot_val} g/day):** {'⚠️ Protein leak detected (Albuminuria). Indicates glomerular stress.' if prot_val > 0.3 else '✅ No significant protein leakage.'}
            """)

        # Prescribed Tablets Table
        st.markdown("---")
        st.subheader("💊 Prescribed CKD Tablets & Medications (KDIGO Table 13)")
        st.write("Medications matched to the patient's exact blood pressure, proteinuria, and kidney stage:")

        tablets = recs.get("prescribed_tablets", [])
        if tablets:
            tab_df = pd.DataFrame([
                {
                    "Medication": t["drug_name"],
                    "Drug Class": t["class"],
                    "Standard Dosage": t["standard_dose"],
                    "Why It's Prescribed": t["indication"],
                    "Safety & Precautions": t["caution"]
                }
                for t in tablets
            ])
            st.dataframe(tab_df, use_container_width=True, hide_index=True)
        else:
            st.info("No prescription medication required for this patient profile.")

        # PDF Download Button
        st.markdown("---")
        report_data = {
            "patient_name": p_name,
            "record_id": st.session_state.get("last_record_id", "REC-01"),
            "username": (st.session_state.user_info or {}).get("username", "Doctor"),
            "age": inputs.get("Age", 55),
            "gender": "Female" if inputs.get("Gender", 0) == 1 else "Male",
            "input_parameters": inputs,
            "prediction": pred,
            "prescribed_tablets": tablets,
            "diet_plan": recs.get("diet_plan", {}),
            "yoga_program": recs.get("yoga_program", []),
            "exercise_plan": recs.get("exercise_plan", {})
        }
        
        pdf_bytes = generate_pdf_report(report_data)
        st.download_button(
            "📥 Download Official Medical PDF Report",
            data=bytes(pdf_bytes),
            file_name=f"NefroAI_Report_{p_name.replace(' ', '_')}.pdf",
            mime="application/pdf",
            use_container_width=True
        )

# ----------------------------------------------------
# TAB 3: PERSONALIZED DIET, YOGA & EXERCISE
# ----------------------------------------------------
with tab3:
    if st.session_state.current_recommendations is None:
        st.info("Please run an assessment in **Tab 1** to view the personalized lifestyle, diet, and yoga care plan.")
    else:
        recs = st.session_state.current_recommendations
        diet = recs["diet_plan"]
        yogas = recs["yoga_program"]
        exercise = recs["exercise_plan"]

        st.subheader("🥗 Personalized Renal Nutrition & Daily Food Guide")
        
        # Targets Row
        c_p, c_na, c_fl = st.columns(3)
        with c_p:
            st.info(f"**Daily Protein Target**\n\n{diet['daily_protein_target']}\n\n*{diet['protein_rationale']}*")
        with c_na:
            st.warning(f"**Daily Sodium Limit**\n\n{diet['daily_sodium_target']}\n\n*Limit salt, canned snacks, and sodium seasonings.*")
        with c_fl:
            st.success(f"**Daily Fluid Target**\n\n{diet['daily_fluid_target']}\n\n*{diet['fluid_rationale']}*")

        col_good, col_bad = st.columns(2)
        with col_good:
            st.markdown("#### ✅ Recommended Kidney Superfoods")
            for item in diet["recommended_foods"]:
                st.markdown(f"- **{item['food']}**: {item['benefit']}")

        with col_bad:
            st.markdown("#### ❌ Foods to Strictly Avoid")
            for item in diet["foods_to_avoid"]:
                st.markdown(f"- **{item['food']}**: {item['reason']}")

        st.markdown("#### 🍽️ Daily Meal Framework")
        meal = diet["meal_framework"]
        st.markdown(f"""
        - **Breakfast:** {meal['breakfast']}
        - **Lunch:** {meal['lunch']}
        - **Afternoon Snack:** {meal['snack']}
        - **Dinner:** {meal['dinner']}
        """)

        st.markdown("---")
        st.subheader("🧘 Kidney-Beneficial Therapeutic Yoga Program")
        st.write("Specific asanas shown to improve renal blood flow, reduce stress, and stabilize arterial blood pressure:")

        for y in yogas:
            with st.expander(f"🧘 **{y['name']}** ({y['sanskrit']}) — {y['duration']}", expanded=True):
                st.markdown(f"**Instructions:** {y['instructions']}")
                st.markdown(f"**Renal Therapeutic Benefit:** {y['renal_benefit']}")

        st.markdown("---")
        st.subheader("🏃 Tailored Weekly Exercise Schedule")
        col_ex1, col_ex2 = st.columns([1, 2])
        with col_ex1:
            st.markdown(f"**Target Intensity:** {exercise['intensity']}")
            st.markdown(f"**Recommended Frequency:** {exercise['frequency']}")
            st.markdown(f"**Aerobic Modality:** {exercise['aerobic_routine']}")
            st.markdown(f"**Resistance Guidance:** {exercise['resistance_routine']}")
            st.markdown(f"**Safety:** *{exercise['safety_guidelines']}*")

        with col_ex2:
            st.markdown("#### Weekly Plan")
            sched_df = pd.DataFrame(exercise["weekly_schedule"])
            st.table(sched_df)

# ----------------------------------------------------
# TAB 4: MONGODB PATIENT HISTORY
# ----------------------------------------------------
with tab4:
    st.subheader("🗄️ MongoDB Patient History & Audit Trail")
    st.write("All patient assessments are stored locally in MongoDB (`mongodb://localhost:27017` -> database: `nefroai_ckd`, collection: `patient_records`):")

    stats = db_manager.get_database_stats()
    s1, s2, s3, s4 = st.columns(4)
    with s1:
        st.metric("Total Stored Records", stats.get("total_records", 0))
    with s2:
        st.metric("CKD Cases", stats.get("ckd_cases", 0))
    with s3:
        st.metric("Non-CKD Cases", stats.get("non_ckd_cases", 0))
    with s4:
        st.metric("Database", stats.get("database_name", "nefroai_ckd"))

    curr_user = (st.session_state.user_info or {}).get("username")
    records = db_manager.get_patient_records(username=curr_user, limit=50)
    if records:
        table_rows = []
        for r in records:
            pred = r.get("prediction", {})
            k = pred.get("kdigo_stage", {})
            table_rows.append({
                "Date": r.get("formatted_date", "N/A"),
                "Patient Name": r.get("patient_name", "N/A"),
                "Age": r.get("age", "N/A"),
                "Gender": r.get("gender", "N/A"),
                "Diagnosis": pred.get("prediction_label", "N/A"),
                "Risk Score": f"{pred.get('risk_percentage', 0.0)}%",
                "KDIGO Stage": k.get("stage", "N/A"),
                "Tablets Prescribed": len(r.get("prescribed_tablets", [])),
                "Assessed By": r.get("username", "N/A")
            })
        st.dataframe(pd.DataFrame(table_rows), use_container_width=True, hide_index=True)
    else:
        st.info("No records found in MongoDB for this account. Create your first assessment in Tab 1!")

# ----------------------------------------------------
# TAB 5: MODEL PERFORMANCE
# ----------------------------------------------------
with tab5:
    st.subheader(" Machine Learning Model Performance")
    # st.write("Validation results of the Support Vector Machine (SVM) and comparative machine learning models:")

    # Top KPI Metrics for Deployed Model
    p1, p2, p3, p4 = st.columns(4)
    with p1:
        st.metric("SVM Accuracy", "98.7% – 100%", delta="Validated via 5-Fold CV")
    with p2:
        st.metric("Precision", "98.7% – 100%", delta="High Specificity")
    with p3:
        st.metric("F1-Score", "99.2% – 100%", delta="Optimal Balance")
    with p4:
        st.metric("Inference Latency", "25 – 45 ms", delta="Sub-50ms Real-Time")

    st.markdown("---")
    st.markdown("#### Comparative Benchmark Across Models")
    perf_data = [
        {"Model": "Support Vector Machine (SVM) [Deployed]", "Dataset A (UCI 400)": "100.0%", "Dataset B (Kaggle 1,659)": "98.7%", "Dataset C (UCI 200)": "100.0%", "Inference Latency": "25 - 45 ms", "Model Size": "0.01 MB"},
        {"Model": "Random Forest (RF)", "Dataset A (UCI 400)": "100.0%", "Dataset B (Kaggle 1,659)": "96.1%", "Dataset C (UCI 200)": "100.0%", "Inference Latency": "130 ms", "Model Size": "0.23 MB"},
        {"Model": "XGBoost", "Dataset A (UCI 400)": "99.0%", "Dataset B (Kaggle 1,659)": "96.1%", "Dataset C (UCI 200)": "100.0%", "Inference Latency": "70 ms", "Model Size": "0.05 MB"},
        {"Model": "AdaBoost", "Dataset A (UCI 400)": "99.0%", "Dataset B (Kaggle 1,659)": "89.3%", "Dataset C (UCI 200)": "100.0%", "Inference Latency": "270 ms", "Model Size": "0.019 MB"},
        {"Model": "K-Nearest Neighbors (KNN)", "Dataset A (UCI 400)": "100.0%", "Dataset B (Kaggle 1,659)": "77.5%", "Dataset C (UCI 200)": "100.0%", "Inference Latency": "340 ms", "Model Size": "0.07 MB"},
        {"Model": "Logistic Regression (LR)", "Dataset A (UCI 400)": "97.0%", "Dataset B (Kaggle 1,659)": "83.1%", "Dataset C (UCI 200)": "100.0%", "Inference Latency": "10 ms", "Model Size": "0.0001 MB"},
        {"Model": "Artificial Neural Network (ANN)", "Dataset A (UCI 400)": "99.0%", "Dataset B (Kaggle 1,659)": "96.9%", "Dataset C (UCI 200)": "100.0%", "Inference Latency": "20 ms", "Model Size": "0.013 MB"},
        {"Model": "LSTM Deep Learning", "Dataset A (UCI 400)": "99.0%", "Dataset B (Kaggle 1,659)": "98.0%", "Dataset C (UCI 200)": "100.0%", "Inference Latency": "327 ms", "Model Size": "0.49 MB"}
    ]
    st.dataframe(pd.DataFrame(perf_data), use_container_width=True, hide_index=True)
