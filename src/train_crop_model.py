"""
train_crop_model.py
===================
Trains a Random Forest classifier to recommend a crop based on
soil NPK values, temperature, humidity, pH, and moisture.

Dataset  : dataset/Crop_recommendation.csv
Output   : models/crop_model.pkl
"""

import os
import pandas as pd
import joblib

from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    confusion_matrix,
    classification_report,
)

# ─── Paths ─────────────────────────────────────────────────
DATA_PATH  = os.path.join("dataset", "Crop_recommendation.csv")
MODEL_PATH = os.path.join("models", "crop_model.pkl")

# ─── Load dataset ──────────────────────────────────────────
df = pd.read_csv(DATA_PATH)
print(f"Dataset loaded: {df.shape[0]} rows, {df.shape[1]} columns")
print(f"Unique crops  : {df['label'].nunique()}")

# ─── Features & target ─────────────────────────────────────
FEATURES = ["N", "P", "K", "temperature", "humidity", "ph"]
TARGET   = "label"

X = df[FEATURES]
y = df[TARGET]

# ─── Train / test split ────────────────────────────────────
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

# ─── Model pipeline ────────────────────────────────────────
model = Pipeline([
    ("scaler", StandardScaler()),
    ("rf", RandomForestClassifier(
        n_estimators=500,
        max_depth=15,
        min_samples_split=3,
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

print("\n========== CROP MODEL ==========")
print(f"Accuracy  : {accuracy:.4f}")
print(f"Precision : {precision:.4f}")
print(f"Recall    : {recall:.4f}")
print("\nClassification Report:\n")
print(classification_report(y_test, y_pred))
print("\nConfusion Matrix:\n")
print(confusion_matrix(y_test, y_pred))

# ─── Save ──────────────────────────────────────────────────
os.makedirs("models", exist_ok=True)
joblib.dump(model, MODEL_PATH)
print(f"\n✅ Crop model saved → {MODEL_PATH}")
