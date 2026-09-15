"""
ml_pipeline.py
Implements the end-to-end Machine Learning pipeline from the NefroAI research paper:
1. Missing value handling (Mean/Median/Mode Simple Imputation)
2. Class balancing using SMOTE (k_neighbors=5)
3. Feature scaling using StandardScaler
4. Hybrid Feature Selection (Algorithm 1: Redundancy filter |r| > 0.85 + Information Gain & Gain Ratio)
5. Model Training & Evaluation: Support Vector Machine (SVM, RBF kernel, probability=True)
   with 5-fold Stratified Cross-Validation
6. Serialization to models/
"""

import os
import joblib
import numpy as np
import pandas as pd
from sklearn.model_selection import StratifiedKFold, cross_validate
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.svm import SVC
from sklearn.feature_selection import mutual_info_classif
from imblearn.over_sampling import SMOTE

MODELS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "models")
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")

def ensure_models_dir():
    os.makedirs(MODELS_DIR, exist_ok=True)

# Top 30 features for Dataset B from Table/Section III of the paper
PAPER_DATASET_B_FEATURES = [
    "SerumCreatinine", "GFR", "Itching", "FastingBloodSugar", "MuscleCramps",
    "BUNLevels", "ProteinInUrine", "BMI", "HbA1c", "CholesterolTotal",
    "CholesterolHDL", "HemoglobinLevels", "Edema", "QualityOfLifeScore",
    "SerumElectrolytesPotassium", "DietQuality", "SerumElectrolytesSodium",
    "FamilyHistoryKidneyDisease", "Diuretics", "PhysicalActivity",
    "SleepQuality", "SerumElectrolytesCalcium", "MedicationAdherence",
    "NSAIDsUse", "NauseaVomiting", "CholesterolTriglycerides",
    "CholesterolLDL", "ACR", "HealthLiteracy", "SerumElectrolytesPhosphorus"
]

# Top 10 features for Dataset A from the paper (Figure 20 & Section III)
PAPER_DATASET_A_FEATURES = [
    "hemo", "pcv", "rc", "sc", "sg", "bgr", "al", "sod", "pot", "bu"
]

def hybrid_feature_selection(X, y, k=30, correlation_threshold=0.85):
    """
    Algorithm 1: Hybrid Feature Selection (HFS) from the NefroAI Paper.
    1. Redundancy Removal: Remove pairwise correlations |r| > threshold.
    2. Relevance Scoring: Information Gain and Gain Ratio proxy.
    3. Select top k features.
    """
    feature_names = list(X.columns)
    
    # Step 1: Redundancy Removal via Pearson Correlation
    corr_matrix = X.corr().abs()
    redundant = set()
    for i in range(len(feature_names)):
        col_i = feature_names[i]
        if col_i in redundant:
            continue
        for j in range(i + 1, len(feature_names)):
            col_j = feature_names[j]
            if col_j in redundant:
                continue
            if corr_matrix.loc[col_i, col_j] > correlation_threshold:
                redundant.add(col_j)
                
    non_redundant = [f for f in feature_names if f not in redundant]
    X_filtered = X[non_redundant]
    
    # Step 2: Information Gain (Mutual Information)
    ig_scores = mutual_info_classif(X_filtered, y, random_state=42)
    ig_series = pd.Series(ig_scores, index=non_redundant)
    
    # Step 3: Gain Ratio approximation (IG normalized by entropy of the feature)
    gr_series = ig_series.copy()
    for col in non_redundant:
        val_counts = pd.qcut(X_filtered[col], q=5, duplicates='drop').value_counts(normalize=True)
        split_info = -np.sum(val_counts * np.log2(val_counts + 1e-9))
        gr_series[col] = ig_series[col] / (split_info + 1e-9)
        
    # Hybrid Score: 0.5 * IG + 0.5 * GR (normalized)
    ig_norm = (ig_series - ig_series.min()) / (ig_series.max() - ig_series.min() + 1e-9)
    gr_norm = (gr_series - gr_series.min()) / (gr_series.max() - gr_series.min() + 1e-9)
    hybrid_score = 0.5 * ig_norm + 0.5 * gr_norm
    
    top_features = hybrid_score.sort_values(ascending=False).head(k).index.tolist()
    return top_features

def train_dataset_b_model():
    """
    Trains the primary NefroAI Support Vector Machine (SVM) model on Dataset B.
    Provides 52 parameters total, evaluates on selected 30 features, and saves model.
    """
    ensure_models_dir()
    data_path = os.path.join(DATA_DIR, "dataset_B_kaggle_1659.csv")
    if not os.path.exists(data_path):
        from backend.dataset_manager import prepare_dataset_b
        prepare_dataset_b()
        
    df = pd.read_csv(data_path)
    
    # Exclude identifiers and non-predictive columns as documented in paper
    drop_cols = ["PatientID", "DoctorInCharge"]
    cols_to_drop = [c for c in drop_cols if c in df.columns]
    df_clean = df.drop(columns=cols_to_drop)
    
    X = df_clean.drop(columns=["Diagnosis"])
    y = df_clean["Diagnosis"]
    
    # 1. Missing Value Imputation
    imputer = SimpleImputer(strategy="median")
    X_imputed = pd.DataFrame(imputer.fit_transform(X), columns=X.columns)
    
    # 2. Select Features (Combine Algorithm 1 with paper's validated 30 features)
    selected_features = [f for f in PAPER_DATASET_B_FEATURES if f in X_imputed.columns]
    if len(selected_features) < 15:
        selected_features = hybrid_feature_selection(X_imputed, y, k=30)
        
    X_sel = X_imputed[selected_features]
    
    # 3. SMOTE Balancing (k_neighbors=5)
    smote = SMOTE(k_neighbors=5, random_state=42)
    X_res, y_res = smote.fit_resample(X_sel, y)
    
    # 4. Normalization using StandardScaler
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X_res)
    
    # 5. SVM Classifier (RBF Kernel, C=10, gamma=0.1, probability=True for risk scores)
    svm_clf = SVC(C=10.0, kernel='rbf', gamma=0.1, probability=True, random_state=42)
    
    # 5-fold Stratified Cross-Validation
    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    scoring = ['accuracy', 'precision', 'recall', 'f1']
    cv_results = cross_validate(svm_clf, X_scaled, y_res, cv=skf, scoring=scoring)
    
    metrics = {
        "accuracy": float(np.mean(cv_results['test_accuracy'])),
        "precision": float(np.mean(cv_results['test_precision'])),
        "recall": float(np.mean(cv_results['test_recall'])),
        "f1_score": float(np.mean(cv_results['test_f1'])),
        "dataset": "Dataset B (1,659 records)",
        "model": "Support Vector Machine (SVM)",
        "features_count": len(selected_features)
    }
    
    # Train final model on all balanced data
    svm_clf.fit(X_scaled, y_res)
    
    artifact = {
        "model": svm_clf,
        "scaler": scaler,
        "selected_features": selected_features,
        "all_feature_medians": X_imputed.median().to_dict(),
        "metrics": metrics
    }
    
    save_path = os.path.join(MODELS_DIR, "nefroai_svm_model.joblib")
    joblib.dump(artifact, save_path)
    print(f"Dataset B Model trained & saved to {save_path}")
    print(f"Metrics: Accuracy={metrics['accuracy']:.4f}, Precision={metrics['precision']:.4f}, Recall={metrics['recall']:.4f}, F1={metrics['f1_score']:.4f}")
    return artifact

def train_dataset_a_model():
    """
    Trains the lightweight 10-feature NefroAI model on Dataset A (UCI 400 instances).
    Matching Figure 20 & Figure 41 from the paper.
    """
    ensure_models_dir()
    data_path = os.path.join(DATA_DIR, "dataset_A_uci_400.csv")
    if not os.path.exists(data_path):
        from backend.dataset_manager import prepare_dataset_a
        prepare_dataset_a()
        
    df = pd.read_csv(data_path)
    
    # Target mapping
    y = df["classification"].astype(str).str.strip().apply(lambda x: 1 if "ckd" in x.lower() and "not" not in x.lower() else 0)
    
    # Selected 10 features from the paper
    top_10 = PAPER_DATASET_A_FEATURES
    existing_features = [f for f in top_10 if f in df.columns]
    
    X = df[existing_features].copy()
    for col in X.columns:
        X[col] = pd.to_numeric(X[col], errors='coerce')
        
    imputer = SimpleImputer(strategy="median")
    X_imputed = pd.DataFrame(imputer.fit_transform(X), columns=X.columns)
    
    smote = SMOTE(k_neighbors=5, random_state=42)
    X_res, y_res = smote.fit_resample(X_imputed, y)
    
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X_res)
    
    svm_clf = SVC(C=10.0, kernel='rbf', gamma=0.1, probability=True, random_state=42)
    
    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    scoring = ['accuracy', 'precision', 'recall', 'f1']
    cv_results = cross_validate(svm_clf, X_scaled, y_res, cv=skf, scoring=scoring)
    
    metrics = {
        "accuracy": float(np.mean(cv_results['test_accuracy'])),
        "precision": float(np.mean(cv_results['test_precision'])),
        "recall": float(np.mean(cv_results['test_recall'])),
        "f1_score": float(np.mean(cv_results['test_f1'])),
        "dataset": "Dataset A (400 records)",
        "model": "Support Vector Machine (SVM)",
        "features_count": len(existing_features)
    }
    
    svm_clf.fit(X_scaled, y_res)
    
    artifact = {
        "model": svm_clf,
        "scaler": scaler,
        "selected_features": existing_features,
        "feature_medians": X_imputed.median().to_dict(),
        "metrics": metrics
    }
    
    save_path = os.path.join(MODELS_DIR, "nefroai_datasetA_svm_model.joblib")
    joblib.dump(artifact, save_path)
    print(f"Dataset A Model trained & saved to {save_path}")
    print(f"Metrics: Accuracy={metrics['accuracy']:.4f}, Precision={metrics['precision']:.4f}, F1={metrics['f1_score']:.4f}")
    return artifact

def train_dataset_c_model():
    """
    Trains the clinical 15-feature NefroAI model on Dataset C (Enam Medical College - 200 instances).
    """
    ensure_models_dir()
    data_path = os.path.join(DATA_DIR, "dataset_C_enam_200.csv")
    if not os.path.exists(data_path):
        from backend.dataset_manager import prepare_dataset_c
        prepare_dataset_c()
        
    df = pd.read_csv(data_path)
    
    y = df["Class"].astype(int)
    
    selected_features = [
        "SerumCreatinine", "BloodUrea", "GFR", "Hemoglobin", "BloodGlucoseRandom",
        "Albumin", "Sodium", "Potassium", "Age", "BloodPressureDiastolic",
        "SpecificGravity", "Hypertension", "DiabetesMellitus", "PedalEdema", "Anemia"
    ]
    existing_features = [f for f in selected_features if f in df.columns]
    
    X = df[existing_features].copy()
    for col in X.columns:
        X[col] = pd.to_numeric(X[col], errors='coerce')
        
    imputer = SimpleImputer(strategy="median")
    X_imputed = pd.DataFrame(imputer.fit_transform(X), columns=X.columns)
    
    smote = SMOTE(k_neighbors=5, random_state=42)
    X_res, y_res = smote.fit_resample(X_imputed, y)
    
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X_res)
    
    svm_clf = SVC(C=10.0, kernel='rbf', gamma=0.1, probability=True, random_state=42)
    
    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    scoring = ['accuracy', 'precision', 'recall', 'f1']
    cv_results = cross_validate(svm_clf, X_scaled, y_res, cv=skf, scoring=scoring)
    
    metrics = {
        "accuracy": float(np.mean(cv_results['test_accuracy'])),
        "precision": float(np.mean(cv_results['test_precision'])),
        "recall": float(np.mean(cv_results['test_recall'])),
        "f1_score": float(np.mean(cv_results['test_f1'])),
        "dataset": "Dataset C (200 records)",
        "model": "Support Vector Machine (SVM)",
        "features_count": len(existing_features)
    }
    
    svm_clf.fit(X_scaled, y_res)
    
    artifact = {
        "model": svm_clf,
        "scaler": scaler,
        "selected_features": existing_features,
        "feature_medians": X_imputed.median().to_dict(),
        "metrics": metrics
    }
    
    save_path = os.path.join(MODELS_DIR, "nefroai_datasetC_svm_model.joblib")
    joblib.dump(artifact, save_path)
    print(f"Dataset C Model trained & saved to {save_path}")
    print(f"Metrics: Accuracy={metrics['accuracy']:.4f}, Precision={metrics['precision']:.4f}, F1={metrics['f1_score']:.4f}")
    return artifact

def train_all_models():
    print("=== Training NefroAI Models (All 3 Datasets) ===")
    train_dataset_b_model()
    train_dataset_a_model()
    train_dataset_c_model()
    print("All 3 models successfully trained and serialized.")

if __name__ == "__main__":
    train_all_models()
