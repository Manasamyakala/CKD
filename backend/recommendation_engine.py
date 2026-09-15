"""
recommendation_engine.py
Generates personalized, clinical-grade medical and lifestyle recommendations
based on KDIGO 2024 guidelines (Table 13 of NefroAI paper) and patient's
individual clinical + lifestyle parameters.

Provides:
1. CKD-Related Prescribed Tablets & Medications (with dosages, indications, and cautions)
2. Personalized Daily Diet & Food Intake (Protein, Sodium, K/P rules, Superfoods vs Forbidden foods)
3. Kidney-Strengthening Yoga Program (Asanas, benefits, step-by-step guides, repetitions)
4. Tailored Exercise Routine (Aerobic, resistance, hydration adjusted for edema)
"""

def generate_recommendations(patient_data, prediction_result):
    """
    Generates a personalized prescription, diet, yoga, and exercise plan.
    """
    is_ckd = prediction_result.get("is_ckd", False)
    risk_pct = prediction_result.get("risk_percentage", 0.0)
    kdigo_stage = prediction_result.get("kdigo_stage", {}).get("stage", "Stage G0 / Normal")
    
    # Extract clinical markers
    gfr = float(patient_data.get("GFR", 90.0))
    creatinine = float(patient_data.get("SerumCreatinine", 1.0))
    bun = float(patient_data.get("BUNLevels", 15.0))
    sbp = float(patient_data.get("SystolicBP", 120.0))
    dbp = float(patient_data.get("DiastolicBP", 80.0))
    fbs = float(patient_data.get("FastingBloodSugar", 90.0))
    hba1c = float(patient_data.get("HbA1c", 5.4))
    protein = float(patient_data.get("ProteinInUrine", 0.0))
    acr = float(patient_data.get("ACR", 10.0))
    potassium = float(patient_data.get("SerumElectrolytesPotassium", 4.2))
    phosphorus = float(patient_data.get("SerumElectrolytesPhosphorus", 3.2))
    hemo = float(patient_data.get("HemoglobinLevels", 14.0))
    edema = int(patient_data.get("Edema", 0))
    fatigue = int(patient_data.get("FatigueLevels", 2))
    bmi = float(patient_data.get("BMI", 24.5))
    diet_quality = float(patient_data.get("DietQuality", 6.0))
    activity_hrs = float(patient_data.get("PhysicalActivity", 3.0))

    # ==========================================
    # 1. CKD-RELATED TABLETS & MEDICATIONS (KDIGO Table 13)
    # ==========================================
    tablets = []
    
    # RAAS Blockers (ACEi / ARBs) for Proteinuria and BP control
    if sbp >= 130 or dbp >= 80 or protein > 0.5 or acr > 30:
        tablets.append({
            "drug_name": "Enalapril (or Losartan)",
            "class": "ACE Inhibitor / ARB (RAAS Blocker)",
            "standard_dose": "5 mg to 10 mg once daily (Losartan: 25-50 mg daily)",
            "indication": "Reduces intraglomerular pressure, controls blood pressure, and significantly reduces proteinuria (kidney protein leakage).",
            "caution": "Monitor serum potassium and creatinine within 2-4 weeks after starting."
        })
        
    # SGLT2 Inhibitor for Renal Protection
    if is_ckd or gfr < 60 or hba1c >= 6.5 or protein > 0.5:
        tablets.append({
            "drug_name": "Dapagliflozin (Farxiga) or Empagliflozin",
            "class": "SGLT2 Inhibitor",
            "standard_dose": "10 mg once daily",
            "indication": "Proven by KDIGO guidelines to slow CKD progression and reduce cardiovascular events in patients with or without diabetes.",
            "caution": "Ensure proper hydration; hold medication temporarily during acute illness or severe dehydration."
        })

    # Diuretics for Fluid Overload / Edema
    if edema == 1 or sbp >= 150:
        tablets.append({
            "drug_name": "Furosemide (Lasix) or Torsemide",
            "class": "Loop Diuretic",
            "standard_dose": "20 mg to 40 mg once daily in the morning",
            "indication": "Relieves peripheral edema, reduces fluid overload, and aids in blood pressure control.",
            "caution": "Do not take late in evening; monitor electrolytes for hypokalemia or dehydration."
        })

    # Phosphate Binder for High Phosphorus
    if phosphorus > 4.5 or "G4" in kdigo_stage or "G5" in kdigo_stage:
        tablets.append({
            "drug_name": "Calcium Acetate (PhosLo) or Sevelamer",
            "class": "Phosphate Binder",
            "standard_dose": "667 mg (1-2 tablets with meals)",
            "indication": "Binds dietary phosphorus in the gut to prevent hyperphosphatemia and CKD-mineral bone disorder.",
            "caution": "Must be taken with food/meals to be effective."
        })

    # Potassium Binder if Hyperkalemia
    if potassium >= 5.1:
        tablets.append({
            "drug_name": "Patiromer (Veltassa) or Sodium Zirconium Cyclosilicate (Lokelma)",
            "class": "Potassium Binder",
            "standard_dose": "8.4 g once daily with food",
            "indication": "Lowers serum potassium levels to safe range without requiring discontinuation of kidney-protective RAAS inhibitors.",
            "caution": "Take at least 3 hours apart from other oral medications."
        })

    # Anemia Management
    if hemo < 11.0:
        tablets.append({
            "drug_name": "Ferrous Ascorbate + Folic Acid / Erythropoietin (EPO)",
            "class": "Hematinic / ESA (Erythropoiesis-Stimulating Agent)",
            "standard_dose": "100 mg elemental iron daily; Nephrologist may prescribe Darbepoetin if persistent",
            "indication": "Treats CKD-associated anemia caused by reduced renal erythropoietin production.",
            "caution": "Take iron on an empty stomach or with Vitamin C; avoid taking with calcium supplements."
        })

    # Statin for Cardiovascular Protection
    if "G3" in kdigo_stage or "G4" in kdigo_stage or "G5" in kdigo_stage or sbp >= 140:
        tablets.append({
            "drug_name": "Atorvastatin (Lipitor)",
            "class": "HMG-CoA Reductase Inhibitor (Statin)",
            "standard_dose": "10 mg to 20 mg once daily at bedtime",
            "indication": "Cardiovascular risk reduction in CKD patients as per KDIGO lipid management recommendations.",
            "caution": "Report any unexplained muscle aches or weakness to your physician."
        })

    # Metabolic Acidosis Therapy
    if is_ckd and bun > 30.0:
        tablets.append({
            "drug_name": "Sodium Bicarbonate",
            "class": "Alkalinizing Agent",
            "standard_dose": "650 mg two times daily",
            "indication": "Corrects metabolic acidosis, slowing the rate of renal function decline and preserving muscle mass.",
            "caution": "Ensure sodium load does not worsen edema or hypertension."
        })

    # If low risk / healthy, give preventative supplement advice
    if not tablets:
        tablets.append({
            "drug_name": "Vitamin D3 (Cholecalciferol) + CoQ10",
            "class": "Preventative Renal Nutrient Support",
            "standard_dose": "1000-2000 IU daily",
            "indication": "Supports endothelial health, normal glomerular filtration, and immune-metabolic stability.",
            "caution": "Check 25-OH Vitamin D levels periodically."
        })

    # ==========================================
    # 2. PERSONALIZED DIET & FOOD INTAKE PLAN
    # ==========================================
    # Determine protein target based on stage
    if "G4" in kdigo_stage or "G5" in kdigo_stage:
        protein_target = "0.55 - 0.60 g per kg body weight/day (Strict Low-Protein with Keto-analogues)"
        protein_explanation = "Lowers nitrogenous waste (blood urea) buildup and delays requirement for dialysis."
    elif "G3" in kdigo_stage:
        protein_target = "0.60 - 0.75 g per kg body weight/day (Moderate Protein Restriction)"
        protein_explanation = "Reduces glomerular hyperfiltration while preserving lean body mass."
    else:
        protein_target = "0.80 g per kg body weight/day (Standard Recommended Dietary Allowance)"
        protein_explanation = "Maintains optimal muscle mass without putting excess strain on renal glomeruli."

    # Sodium target
    sodium_target = "< 2,000 mg/day (less than 1 level teaspoon of salt across all meals)"
    
    # Fluid recommendation
    if edema == 1:
        fluid_target = "Strict Fluid Limitation: 1.0 to 1.2 Liters/day (including tea, soups, and water)"
        fluid_note = "Due to fluid retention/edema, excess fluid increases cardiac strain and peripheral swelling."
    else:
        fluid_target = "Adequate Hydration: 2.0 to 2.5 Liters/day (consistent intake throughout waking hours)"
        fluid_note = "Adequate fluid prevents renal hypoperfusion and reduces crystallization risk."

    # Superfoods to eat
    foods_to_eat = [
        {"food": "Blueberries, Strawberries & Cranberries", "benefit": "Rich in anthocyanins and antioxidants, low in potassium and phosphorus."},
        {"food": "Cauliflower & Cabbage", "benefit": "High in Vitamin C, folate, and fiber with minimal potassium burden."},
        {"food": "Red Bell Peppers", "benefit": "Extremely low in potassium while providing 150% daily Vitamin C and Vitamin A."},
        {"food": "Garlic & Onions", "benefit": "Natural anti-inflammatory and anti-microbial agents that enhance food flavor without adding sodium."},
        {"food": "Egg Whites", "benefit": "Pure high-biological-value protein with virtually zero phosphorus (unlike whole egg yolk)."},
        {"food": "Extra Virgin Olive Oil", "benefit": "Polyphenol-rich healthy fat that reduces inflammatory cytokines and lipid peroxidation."},
        {"food": "Apples & Pineapples", "benefit": "Low potassium fruit options rich in pectin fiber and digestive enzymes."}
    ]

    # Foods to strictly avoid
    foods_to_avoid = [
        {"food": "Dark Colas & Canned Sodas", "reason": "Packed with inorganic phosphate additives which are rapidly absorbed and damage blood vessels."},
        {"food": "Processed Meats (Sausages, Bacon, Cured meats)", "reason": "Excessive sodium, nitrates, and high protein catabolite burden."},
        {"food": "Canned Soups & Packaged Instant Meals", "reason": "Hidden sodium often exceeding 1,000 mg per serving."},
        {"food": "Over-the-Counter NSAIDs (Ibuprofen, Naproxen)", "reason": "Directly constricts afferent renal arterioles, causing acute drops in GFR."}
    ]

    # High potassium foods restriction if K > 4.8
    if potassium >= 4.8:
        foods_to_avoid.extend([
            {"food": "Bananas, Oranges & Cantaloupe", "reason": "High potassium content can trigger cardiac dysrhythmias in impaired kidney function."},
            {"food": "Potatoes & Tomatoes (unless boiled and drained/leached)", "reason": "High potassium concentration per serving."},
            {"food": "Avocados & Spinach", "reason": "Extremely dense in potassium; replace with cucumbers, lettuce, and cabbage."}
        ])

    # High phosphorus foods restriction if P > 4.3 or advanced stage
    if phosphorus >= 4.3 or "G3" in kdigo_stage or "G4" in kdigo_stage or "G5" in kdigo_stage:
        foods_to_avoid.extend([
            {"food": "Processed Cheese & Excess Dairy", "reason": "Dense in bioavailable phosphorus, accelerating arterial calcification."},
            {"food": "Nuts, Seeds & Whole Bran in large amounts", "reason": "High organic phosphorus; limit portion size to 1 ounce."}
        ])

    diet_plan = {
        "daily_protein_target": protein_target,
        "protein_rationale": protein_explanation,
        "daily_sodium_target": sodium_target,
        "daily_fluid_target": fluid_target,
        "fluid_rationale": fluid_note,
        "recommended_foods": foods_to_eat,
        "foods_to_avoid": foods_to_avoid,
        "meal_framework": {
            "breakfast": "Egg white scramble with red bell peppers, steamed apples, and herbal ginger tea (no added salt).",
            "lunch": "White basmati rice or sourdough bread, grilled cauliflower steaks, olive oil seasoned cucumber salad, and low-sodium vegetable soup.",
            "snack": "A cup of fresh blueberries or strawberries, or 1 small apple.",
            "dinner": "Steamed white fish or silken tofu, cabbage sauteed with garlic and cumin, with a modest portion of steamed white rice."
        }
    }

    # ==========================================
    # 3. KIDNEY-BENEFICIAL YOGA PROGRAM
    # ==========================================
    yoga_asanas = [
        {
            "name": "Bhujangasana (Cobra Pose)",
            "sanskrit": "भुजङ्गासन",
            "duration": "3 rounds, hold for 20-30 seconds each",
            "instructions": "Lie prone on your stomach, palms beside your shoulders. Inhale and gently lift your chest while keeping your hips grounded. Keep shoulders relaxed and elbows slightly bent.",
            "renal_benefit": "Gently stimulates and massages the adrenal glands and renal tissue, encouraging local blood perfusion and reducing abdominal stagnation."
        },
        {
            "name": "Ardha Matsyendrasana (Half Lord of the Fishes Pose)",
            "sanskrit": "अर्धमत्स्येन्द्रासन",
            "duration": "2 rounds each side, hold for 30 seconds",
            "instructions": "Sit tall with legs straight. Bend right knee and place right foot outside left thigh. Twist torso to the right, placing left elbow on outside of right knee. Breathe deeply.",
            "renal_benefit": "Axial spinal twisting creates intra-abdominal pressure changes that help drain congested blood from the kidneys, liver, and spleen."
        },
        {
            "name": "Setu Bandhasana (Bridge Pose)",
            "sanskrit": "सेतुबन्धासन",
            "duration": "3 rounds, hold for 30-45 seconds each",
            "instructions": "Lie supine with knees bent and feet hip-width apart. Press into your feet and lift your pelvis toward the ceiling. Interlace fingers under your back.",
            "renal_benefit": "Inversion effect reduces peripheral venous pooling in the legs (reducing edema) and regulates autonomic blood pressure control."
        },
        {
            "name": "Paschimottanasana (Seated Forward Bend)",
            "sanskrit": "पश्चिमोत्तानासन",
            "duration": "3 rounds, hold for 30-45 seconds each",
            "instructions": "Sit with legs extended straight. Inhale arms overhead, exhale and hinge forward from the hips, reaching for your shins or toes without rounding shoulders aggressively.",
            "renal_benefit": "Stimulates the posterior renal meridians, stretches the lower back muscles, and promotes calm parasympathetic activity."
        },
        {
            "name": "Anulom Vilom (Alternate Nostril Pranayama)",
            "sanskrit": "अनुलोम विलोम प्राणायाम",
            "duration": "10 minutes daily in the morning and evening",
            "instructions": "Sit in a comfortable upright posture. Close right nostril with thumb, inhale slowly through left nostril (4 counts). Close left nostril with ring finger, release thumb and exhale through right (4 counts). Repeat opposite.",
            "renal_benefit": "Proven to lower sympathetic overactivity, reduce systemic arterial blood pressure, and mitigate renal oxidative stress."
        }
    ]

    # ==========================================
    # 4. TAILORED EXERCISE REGIMEN
    # ==========================================
    # Personalize exercise intensity based on fatigue and current activity
    if fatigue >= 7 or "G4" in kdigo_stage or "G5" in kdigo_stage:
        aerobic_desc = "Gentle pacing: 15-20 minutes of leisurely walking or recumbent stationary cycling at low resistance, broken into two 10-minute intervals."
        exercise_freq = "3 to 4 days per week"
        intensity = "Low Intensity (RPE 3-4 out of 10)"
    elif fatigue >= 4 or "G3" in kdigo_stage:
        aerobic_desc = "Moderate walking or stationary cycling: 25-30 minutes per session at a conversational pace."
        exercise_freq = "4 to 5 days per week"
        intensity = "Moderate Intensity (RPE 5-6 out of 10)"
    else:
        aerobic_desc = "Brisk walking, outdoor cycling, or low-impact swimming: 30-40 minutes continuously."
        exercise_freq = "5 days per week (150 minutes/week total)"
        intensity = "Moderate to Vigorous (RPE 6-7 out of 10)"

    resistance_desc = "Light resistance band exercises (seated rows, chest presses, leg press extensions) 2 days/week. Prevents uremic sarcopenia (muscle loss) common in chronic kidney conditions."
    cautions = "Avoid extreme dehydration; drink water in measured sips during exercise; avoid heavy isometric straining (Valsalva maneuver) which spikes blood pressure."

    exercise_plan = {
        "intensity": intensity,
        "frequency": exercise_freq,
        "aerobic_routine": aerobic_desc,
        "resistance_routine": resistance_desc,
        "safety_guidelines": cautions,
        "weekly_schedule": [
            {"day": "Monday", "activity": "30 min Brisk Walk + 10 min Anulom Vilom Pranayama"},
            {"day": "Tuesday", "activity": "20 min Kidney Yoga Session (Bhujangasana, Setu Bandhasana)"},
            {"day": "Wednesday", "activity": "30 min Low-Impact Stationary Cycling + Light Stretch"},
            {"day": "Thursday", "activity": "Rest & Gentle Walking + Breathing Exercises"},
            {"day": "Friday", "activity": "20 min Resistance Band Conditioning + Full Body Yoga"},
            {"day": "Saturday", "activity": "30 min Outdoor Nature Walk + Relaxation"},
            {"day": "Sunday", "activity": "Restoration Day: Meditation, Gentle Pranayama, Family Time"}
        ]
    }

    return {
        "prescribed_tablets": tablets,
        "diet_plan": diet_plan,
        "yoga_program": yoga_asanas,
        "exercise_plan": exercise_plan,
        "patient_summary": {
            "is_ckd": is_ckd,
            "risk_percentage": risk_pct,
            "stage": kdigo_stage,
            "proteinuria_level": "Elevated" if protein > 0.5 or acr > 30 else "Normal",
            "hypertension_status": "Hypertensive" if sbp >= 130 or dbp >= 80 else "Normal BP",
            "edema_present": bool(edema == 1)
        }
    }

if __name__ == "__main__":
    dummy_patient = {
        "Age": 55, "BMI": 28.0, "GFR": 48.0, "SerumCreatinine": 1.7,
        "BUNLevels": 28.0, "SystolicBP": 140, "DiastolicBP": 90,
        "ProteinInUrine": 1.2, "SerumElectrolytesPotassium": 4.7,
        "Edema": 1, "FatigueLevels": 5, "DietQuality": 4.0
    }
    dummy_pred = {
        "is_ckd": True,
        "risk_percentage": 76.5,
        "kdigo_stage": {"stage": "Stage G3a", "label": "G3a: Mild to Moderately Decreased GFR"}
    }
    recs = generate_recommendations(dummy_patient, dummy_pred)
    print("=== Table & Prescription Test ===")
    for t in recs["prescribed_tablets"]:
        print(f"- {t['drug_name']} ({t['class']}) -> {t['standard_dose']}")
    print("\n=== Yoga Plan Count ===")
    print(f"Generated {len(recs['yoga_program'])} yoga asanas.")
    print("\n=== Diet Target ===")
    print(f"Protein: {recs['diet_plan']['daily_protein_target']}")
    print(f"Fluid: {recs['diet_plan']['daily_fluid_target']}")
