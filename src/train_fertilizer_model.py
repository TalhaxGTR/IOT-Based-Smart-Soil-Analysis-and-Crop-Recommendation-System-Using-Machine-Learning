"""
train_fertilizer_model.py
=========================
Trains a Random Forest classifier to recommend a fertilizer based on
soil temperature, moisture, pH, and NPK levels.

Uses SMOTE to handle class imbalance in the dataset.

Dataset  : dataset/fertilizer_recommendation_dataset.csv
Output   : models/fert_model.pkl, models/le_fert.pkl
"""

import os
import pandas as pd
import joblib

from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    confusion_matrix,
    classification_report,
)
from imblearn.over_sampling import SMOTE

# ─── Paths ─────────────────────────────────────────────────
DATA_PATH       = os.path.join("dataset", "fertilizer_recommendation_dataset.csv")
MODEL_PATH      = os.path.join("models", "fert_model.pkl")
ENCODER_PATH    = os.path.join("models", "le_fert.pkl")

# ─── Load & clean dataset ──────────────────────────────────
df = pd.read_csv(DATA_PATH)
print(f"Dataset loaded: {df.shape[0]} rows, {df.shape[1]} columns")

# Drop columns not used for prediction
DROP_COLS = ["Carbon", "Remark", "Rainfall", "Soil", "Crop"]
df = df.drop(columns=[c for c in DROP_COLS if c in df.columns])

# Fix a common typo in the dataset
df.rename(columns={"Temparature": "Temperature"}, inplace=True)

print(f"Unique fertilizers: {df['Fertilizer'].nunique()}")

# ─── Label encoding ────────────────────────────────────────
le_fert = LabelEncoder()
df["Fertilizer"] = le_fert.fit_transform(df["Fertilizer"])

# ─── Features & target ─────────────────────────────────────
FEATURES = ["Temperature", "Moisture", "PH",
            "Nitrogen", "Phosphorous", "Potassium"]
TARGET   = "Fertilizer"

X = df[FEATURES]
y = df[TARGET]

# ─── Balance dataset with SMOTE ────────────────────────────
print("\nApplying SMOTE …")
smote = SMOTE(random_state=42)
X, y = smote.fit_resample(X, y)
print(f"After SMOTE: {len(X)} samples")

# ─── Train / test split ────────────────────────────────────
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# ─── Model pipeline ────────────────────────────────────────
model = Pipeline([
    ("scaler", StandardScaler()),
    ("rf", RandomForestClassifier(
        n_estimators=400,
        max_depth=12,
        min_samples_split=4,
        random_state=42,
        n_jobs=-1,
    )),
])

# ─── Train ─────────────────────────────────────────────────
print("\nTraining …")
model.fit(X_train, y_train)

# ─── Evaluate ──────────────────────────────────────────────
y_pred = model.predict(X_test)

accuracy  = accuracy_score(y_test, y_pred)
precision = precision_score(y_test, y_pred, average="weighted")
recall    = recall_score(y_test, y_pred, average="weighted")

print("\n========== FERTILIZER MODEL ==========")
print(f"Accuracy  : {accuracy:.4f}")
print(f"Precision : {precision:.4f}")
print(f"Recall    : {recall:.4f}")
print("\nClassification Report:\n")
print(classification_report(y_test, y_pred,
                             target_names=le_fert.classes_))
print("\nConfusion Matrix:\n")
print(confusion_matrix(y_test, y_pred))

# ─── Save ──────────────────────────────────────────────────
os.makedirs("models", exist_ok=True)
joblib.dump(model, MODEL_PATH)
joblib.dump(le_fert, ENCODER_PATH)
print(f"\n✅ Fertilizer model saved → {MODEL_PATH}")
print(f"✅ Label encoder saved   → {ENCODER_PATH}")
