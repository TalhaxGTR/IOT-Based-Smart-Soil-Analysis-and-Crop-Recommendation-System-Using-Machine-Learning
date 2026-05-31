# 🌱 Smart Soil Analysis System

An AI-powered soil analysis system that uses an **ESP32 microcontroller** with real soil sensors to collect data, then runs **Random Forest machine learning models** to recommend the optimal **crop** and **fertilizer** — all displayed on a live **Streamlit dashboard**.

---

## 📌 Project Overview

Traditional soil testing requires expensive lab equipment and days of waiting. This system performs real-time, on-site soil analysis using low-cost sensors and on-device ML inference. A farmer simply inserts the sensor probe into the soil, and within minutes receives actionable AI-driven recommendations.

### What it measures
| Sensor | Parameter | Unit |
|---|---|---|
| NPK RS-485 Modbus | Nitrogen (N) | mg/kg |
| NPK RS-485 Modbus | Phosphorus (P) | mg/kg |
| NPK RS-485 Modbus | Potassium (K) | mg/kg |
| NPK RS-485 Modbus | Soil Moisture | % |
| NPK RS-485 Modbus | Soil pH | 0–14 |
| DHT11 | Air Temperature | °C |
| DHT11 | Air Humidity | % |

### What it predicts
- 🌾 **Recommended Crop** — best crop for current soil conditions (22 classes)
- 🌿 **Recommended Fertilizer** — most suitable fertilizer type

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        HARDWARE LAYER                           │
│                                                                 │
│  ┌──────────────┐   RS-485    ┌────────────┐                   │
│  │ NPK Sensor   │────Modbus──▶│   MAX485   │                   │
│  │ (Moisture,   │             │  RS485↔TTL │                   │
│  │  pH, N, P, K)│             └─────┬──────┘                   │
│  └──────────────┘                   │ UART2                    │
│                                     ▼                           │
│  ┌──────────────┐             ┌────────────┐                   │
│  │    DHT11     │─────GPIO───▶│   ESP32    │                   │
│  │ (Temp, Hum)  │             │ DevKit v1  │                   │
│  └──────────────┘             └─────┬──────┘                   │
│                                     │ USB Serial                │
└─────────────────────────────────────┼───────────────────────────┘
                                      │
                          DATA:<t>,<h>,<ph>,<N>,<P>,<K>,<m>
                                      │
┌─────────────────────────────────────▼───────────────────────────┐
│                        SOFTWARE LAYER (PC)                      │
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                  dashboard.py (Streamlit)                 │  │
│  │  ┌────────────────────┐   ┌────────────────────────────┐  │  │
│  │  │ Serial Reader      │   │  ML Inference              │  │  │
│  │  │ (pyserial thread)  │──▶│  crop_model.pkl  →  Crop   │  │  │
│  │  │                    │   │  fert_model.pkl  →  Fert.  │  │  │
│  │  └────────────────────┘   └────────────────────────────┘  │  │
│  │                                                           │  │
│  │  Live Sensor Metrics │ NPK Bar Chart │ AI Recommendations │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📁 Repository Structure

```
Smart-Soil-Analysis-System/
│
├── dataset/                        # Training datasets
│   ├── Crop_recommendation.csv     # 2,200 samples, 22 crop classes
│   └── fertilizer_recommendation_dataset.csv
│
├── models/                         # Trained ML models (Git LFS or local)
│   ├── crop_model.pkl              # Random Forest crop classifier
│   ├── fert_model.pkl              # Random Forest fertilizer classifier
│   ├── le_fert.pkl                 # Label encoder for fertilizer classes
│   ├── le_crop.pkl                 # Label encoder for crop classes
│   └── le_soil.pkl                 # Label encoder for soil type
│
├── hardware/                       # Embedded firmware & wiring
│   ├── ESP32_code/
│   │   └── main.ino                # Arduino sketch (ESP32 + DHT11 + RS-485)
│   ├── sensor_connections.md       # Full wiring diagram & pin table
│   └── circuit_diagram.png         # Schematic image
│
├── dashboard/                      # Streamlit web dashboard
│   └── app.py                      # Main dashboard (copy of dashboard.py)
│
├── src/                            # Python source modules
│   ├── train_crop_model.py         # Train & evaluate crop RF model
│   ├── train_fertilizer_model.py   # Train & evaluate fertilizer RF model
│   ├── bridge.py                   # CLI serial bridge (no UI)
│   └── test_model.py               # Quick model sanity checks
│
├── notebooks/
│   └── experimentation.ipynb       # EDA, feature analysis, model comparison
│
├── images/
│   ├── architecture.png            # System architecture diagram
│   ├── dashboard.png               # Screenshot of the Streamlit dashboard
│   └── results.png                 # Model accuracy & confusion matrix
│
├── requirements.txt                # Python dependencies
├── README.md                       # This file
├── LICENSE                         # MIT License
└── .gitignore
```

---

## ⚙️ Hardware Requirements

| Component | Qty | Notes |
|---|---|---|
| ESP32 DevKit v1 | 1 | Any 38-pin ESP32 |
| 7-in-1 NPK RS-485 Sensor | 1 | Modbus RTU, slave ID 1 |
| MAX485 TTL↔RS-485 Module | 1 | — |
| DHT11 Temperature/Humidity | 1 | With 10 kΩ pull-up resistor |
| 12V DC Power Adapter | 1 | For NPK sensor |
| USB-A to Micro-USB cable | 1 | ESP32 ↔ PC |
| Jumper wires | — | Male-to-female |

Detailed wiring → [`hardware/sensor_connections.md`](hardware/sensor_connections.md)

---

## 🚀 Quick Start

### 1. Clone the repository

```bash
git clone https://github.com/<your-username>/Smart-Soil-Analysis-System.git
cd Smart-Soil-Analysis-System
```

### 2. Install Python dependencies

```bash
pip install -r requirements.txt
```

### 3. Flash the ESP32

1. Open `hardware/ESP32_code/main.ino` in **Arduino IDE 2.x**
2. Install libraries via Library Manager:
   - `ModbusMaster` by Doc Walker
   - `DHT sensor library` by Adafruit
3. Select your ESP32 board and COM port
4. Upload the sketch

### 4. Train the models (or use pre-trained)

```bash
# From the project root:
python src/train_crop_model.py
python src/train_fertilizer_model.py
```

Pre-trained `.pkl` files are already included in `models/`.

### 5. Run the dashboard

```bash
streamlit run dashboard/app.py
```

Open `http://localhost:8501` in your browser, select the ESP32 COM port in the sidebar, and press **Start Analysis**.

### 6. (Optional) CLI mode — no Streamlit

```bash
# Edit COM_PORT in src/bridge.py first
python src/bridge.py
```

---

## 🤖 Machine Learning Details

### Crop Recommendation Model

| Item | Value |
|---|---|
| Algorithm | Random Forest Classifier |
| Features | N, P, K, Temperature, Humidity, pH |
| Classes | 22 crop types |
| Training samples | 1,760 (80%) |
| Test samples | 440 (20%) |
| Accuracy | ~99% |
| Pipeline | StandardScaler → RandomForest(500 trees, depth 15) |

### Fertilizer Recommendation Model

| Item | Value |
|---|---|
| Algorithm | Random Forest Classifier |
| Features | Temperature, Moisture, pH, N, P, K |
| Classes | Multiple fertilizer types |
| Class balancing | SMOTE (Synthetic Minority Oversampling) |
| Pipeline | StandardScaler → RandomForest(400 trees, depth 12) |

---

## 📊 ESP32 Sampling Strategy

The firmware takes **5 sensor readings** spaced **10 seconds apart** and sends the **averaged values** to the PC. This filters out transient noise and gives a more reliable soil reading.

Serial output format (one line, sent after all 5 samples):
```
DATA:<temp>,<hum>,<ph>,<N>,<P>,<K>,<moist>
```

Example:
```
DATA:28.50,65.30,6.80,62.00,48.00,41.00,55.40
```

---

## 🖥️ Dashboard Features

- **Live progress log** — shows each sample read from the ESP32 in real time
- **Elapsed timer** — tracks how long the reading session is taking
- **Sensor metrics panel** — displays all 7 averaged sensor values
- **NPK bar chart** — visual comparison of nitrogen, phosphorus, and potassium
- **AI recommendations** — prominently displayed crop and fertilizer cards
- **COM port selector** — auto-detects available serial ports in the sidebar
- **Reset button** — clears state for a new analysis without restarting

---

## 🔧 Troubleshooting

| Problem | Solution |
|---|---|
| `Serial port not found` | Check Device Manager; use correct COM port |
| `MODBUS_ERROR` in log | Check RS-485 wiring; verify 12V sensor supply |
| `DHT_ERROR` in log | Check GPIO 15 connection; add/check 10kΩ pull-up |
| Dashboard freezes | Close Arduino IDE Serial Monitor (it blocks the port) |
| Model file not found | Run `train_crop_model.py` and `train_fertilizer_model.py` first |

---

## 📄 License

This project is licensed under the MIT License — see [LICENSE](LICENSE) for details.

---

## 👤 Author

Final Year Project (FYP) — Department of Computer Science / Electrical Engineering  
*Smart Soil Analysis System using IoT & Machine Learning*
