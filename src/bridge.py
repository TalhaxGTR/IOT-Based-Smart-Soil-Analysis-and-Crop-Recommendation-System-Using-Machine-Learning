"""
bridge.py — Serial Bridge
=========================
Reads sensor data from ESP32 over USB serial, runs crop and fertilizer
ML models, and prints the recommendations to the terminal.

Run this script instead of dashboard.py when you only need a quick
CLI-based result (no Streamlit UI required).

Usage:
    python bridge.py

The ESP32 must be connected and running main.ino.
Adjust COM_PORT below to match your system (e.g. /dev/ttyUSB0 on Linux).
"""

import serial
import joblib
import pandas as pd
import time

# ─── Config ────────────────────────────────────────────────
COM_PORT   = "COM4"    # ← Change to your ESP32 port
BAUD_RATE  = 115200

# ─── Load models ───────────────────────────────────────────
crop_model = joblib.load("models/crop_model.pkl")
fert_model = joblib.load("models/fert_model.pkl")
le_fert    = joblib.load("models/le_fert.pkl")

print("✅ Models Loaded")

# ─── Serial connection with auto-retry ─────────────────────
def connect():
    while True:
        try:
            s = serial.Serial(COM_PORT, BAUD_RATE, timeout=1)
            time.sleep(2)
            print("✅ Serial Connected on", COM_PORT)
            return s
        except Exception as e:
            print(f"⚠️  Could not open {COM_PORT}: {e}  — retrying in 2 s …")
            time.sleep(2)


ser = connect()

# ─── Main loop ─────────────────────────────────────────────
print("\n⏳  Waiting for ESP32 to send sensor data …\n")

while True:
    try:
        if ser.in_waiting:
            line = ser.readline().decode(errors="ignore").strip()

            # Status messages — just forward to console
            if not line.startswith("DATA:"):
                print(f"[ESP32] {line}")
                continue

            # Parse CSV payload
            parts = line.replace("DATA:", "").split(",")
            if len(parts) != 7:
                print(f"[WARN] Unexpected DATA format: {line}")
                continue

            temp, hum, ph, N, P, K, moist = map(float, parts)

            print("\n─── Sensor Averages ───────────────────────────────")
            print(f"  Temperature : {temp:.1f} °C")
            print(f"  Humidity    : {hum:.1f} %")
            print(f"  Moisture    : {moist:.1f} %")
            print(f"  pH          : {ph:.2f}")
            print(f"  Nitrogen    : {N:.0f} mg/kg")
            print(f"  Phosphorus  : {P:.0f} mg/kg")
            print(f"  Potassium   : {K:.0f} mg/kg")

            # ── Crop prediction ─────────────────────────────
            crop_df = pd.DataFrame(
                [[N, P, K, temp, hum, ph, moist]],
                columns=["N", "P", "K", "temperature",
                         "humidity", "ph", "moisture"],
            )
            crop = crop_model.predict(crop_df)[0]

            # ── Fertilizer prediction ────────────────────────
            fert_df = pd.DataFrame(
                [[temp, moist, ph, N, P, K]],
                columns=["Temperature", "Moisture", "PH",
                         "Nitrogen", "Phosphorous", "Potassium"],
            )
            fert = le_fert.inverse_transform(fert_model.predict(fert_df))[0]

            print("\n════════════════════════════════════════════════════")
            print(f"  🌾  Recommended Crop       : {crop}")
            print(f"  🌿  Recommended Fertilizer : {fert}")
            print("════════════════════════════════════════════════════\n")

    except KeyboardInterrupt:
        print("\n👋  Stopped by user.")
        ser.close()
        break
    except Exception as e:
        print(f"[ERROR] {e}")
        ser.close()
        ser = connect()
