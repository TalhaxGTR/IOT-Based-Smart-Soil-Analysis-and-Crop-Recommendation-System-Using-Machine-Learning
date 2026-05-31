"""
test_model.py — Quick Model Sanity Check
=========================================
Tests the saved crop and fertilizer models with hard-coded sensor
values. Useful for verifying models are working before connecting
the ESP32 hardware.

Usage:
    python src/test_model.py
"""

import joblib
import pandas as pd

# ─── Load models ───────────────────────────────────────────
crop_model = joblib.load("models/crop_model.pkl")
fert_model = joblib.load("models/fert_model.pkl")
le_fert    = joblib.load("models/le_fert.pkl")

print("✅ Models loaded\n")


def predict(temp: float, hum: float, ph: float,
            N: float, P: float, K: float, moist: float,
            label: str = "") -> None:
    """Run both models and print top-3 predictions."""

    print(f"{'─'*52}")
    if label:
        print(f"  Scenario: {label}")
    print(f"  Inputs  → T={temp}°C  H={hum}%  pH={ph}"
          f"  N={N}  P={P}  K={K}  M={moist}%")

    # ── Crop ──
    crop_df = pd.DataFrame(
        [[N, P, K, temp, hum, ph, moist]],
        columns=["N", "P", "K", "temperature",
                 "humidity", "ph", "moisture"],
    )
    crop_probs = crop_model.predict_proba(crop_df)[0]
    crop_classes = crop_model.classes_
    top_crops = sorted(
        zip(crop_classes, crop_probs),
        key=lambda x: x[1], reverse=True
    )[:3]

    print("  🌾 Top Crops:")
    for c, p in top_crops:
        print(f"       {c:<20} {p*100:.1f}%")

    # ── Fertilizer ──
    fert_df = pd.DataFrame(
        [[temp, moist, ph, N, P, K]],
        columns=["Temperature", "Moisture", "PH",
                 "Nitrogen", "Phosphorous", "Potassium"],
    )
    fert_probs = fert_model.predict_proba(fert_df)[0]
    fert_classes = le_fert.classes_
    top_ferts = sorted(
        zip(fert_classes, fert_probs),
        key=lambda x: x[1], reverse=True
    )[:3]

    print("  🌿 Top Fertilizers:")
    for f, p in top_ferts:
        print(f"       {f:<20} {p*100:.1f}%")


# ─── Test cases ────────────────────────────────────────────
predict(28, 70, 6.8, 60, 50, 40, 60,  label="Balanced — high NPK")
predict(32, 50, 5.5, 20, 20, 20, 30,  label="Dry — low NPK")
predict(30, 85, 6.5, 90, 60, 60, 80,  label="Humid — very high NPK")
predict(36, 30, 7.5, 20, 70, 55, 35,  label="Hot & dry — high P/K")

print(f"{'─'*52}")
