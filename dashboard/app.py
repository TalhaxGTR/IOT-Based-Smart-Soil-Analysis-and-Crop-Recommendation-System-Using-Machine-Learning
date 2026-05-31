import streamlit as st
import serial
import serial.tools.list_ports
import joblib
import time
import threading
import pandas as pd

# ════════════════════════════════════════════════════════════
# PAGE CONFIG
# ════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="AI Smart Soil Analysis",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ════════════════════════════════════════════════════════════
# SHARED STATE
# ════════════════════════════════════════════════════════════
if "_shared" not in st.__dict__:
    st._shared = {
        "status":      "idle",   # idle | reading | done | error
        "avg_data":    None,
        "crop_result": None,
        "fert_result": None,
        "log":         [],
        "error_msg":   "",
        "stop_event":  None,
        "start_time":  None,
        # BUG 6 FIX: removed unused "sample_no" key
    }

shared = st._shared

# ════════════════════════════════════════════════════════════
# CSS
# ════════════════════════════════════════════════════════════
st.markdown("""
<style>

#MainMenu, footer, header { visibility: hidden; }

[data-testid="stAppViewContainer"]{
    background: linear-gradient(135deg,#f4f7fb,#eef3f9,#ffffff);
    color:#111827;
}

[data-testid="stSidebar"]{
    background: linear-gradient(180deg,#ffffff,#f3f6fb);
    border-right:1px solid #dbe4ee;
}

.title{
    font-size:3.2rem;
    font-weight:900;
    text-align:center;
    background: linear-gradient(90deg,#00a86b,#0077ff,#7c3aed);
    -webkit-background-clip:text;
    -webkit-text-fill-color:transparent;
}

.subtitle{
    text-align:center;
    color:#4b5563;
    font-size:1rem;
    margin-top:-12px;
    margin-bottom:15px;
}

.stButton > button{
    width:100%;
    border:none !important;
    border-radius:14px !important;
    padding:14px !important;
    font-size:1.05rem !important;
    font-weight:700 !important;
    color:white !important;
    background: linear-gradient(90deg,#00b894,#0984e3) !important;
    transition:0.3s;
}

.stButton > button:hover{
    transform: translateY(-2px);
    box-shadow:0 0 20px rgba(9,132,227,0.25);
}

.hero{
    background: linear-gradient(135deg,#ffffff,#f7fbff);
    border:1px solid #d9e4f2;
    padding:45px;
    border-radius:28px;
    text-align:center;
    box-shadow:0 10px 40px rgba(0,0,0,0.06);
}

.hero h2 { color:#111827; font-size:2rem; font-weight:800; }
.hero p  { color:#4b5563; max-width:700px; margin:auto; line-height:1.7; }

.result-card{
    border-radius:24px;
    padding:35px;
    text-align:center;
    color:white;
    box-shadow:0 10px 35px rgba(0,0,0,0.12);
}

.crop-card{ background: linear-gradient(135deg,#00b894,#009688); }
.fert-card{ background: linear-gradient(135deg,#0984e3,#3f51b5); }

.result-icon  { font-size:60px; }
.result-title { font-size:1rem; color:#dfe6e9; margin-top:10px;
                text-transform:uppercase; letter-spacing:2px; }
.result-value { font-size:2.5rem; font-weight:900; margin-top:10px; }

.metric-card{
    background:#ffffff;
    border:1px solid #dfe7f0;
    border-radius:20px;
    padding:22px 15px;
    text-align:center;
    transition:0.3s;
    box-shadow:0 4px 20px rgba(0,0,0,0.05);
}

.metric-card:hover{ transform: translateY(-4px); box-shadow:0 8px 25px rgba(0,0,0,0.08); }
.metric-icon  { font-size:32px; }
.metric-label { color:#6b7280; margin-top:10px; font-size:0.85rem; font-weight:600; }
.metric-value { color:#111827; font-size:1.8rem; font-weight:800; margin-top:5px; }

.step{
    background:#ffffff;
    border:1px solid #dfe7f0;
    border-radius:22px;
    padding:25px;
    text-align:center;
    height:320px;
    box-shadow:0 5px 20px rgba(0,0,0,0.05);
}

.step h4 { color:#111827; margin-top:10px; }
.step p  { color:#6b7280; font-size:0.92rem; }

/* BUG 2 FIX: reading box for single-sample — no sample counter UI */
.read-box{
    background: linear-gradient(135deg,#ffffff,#eef8ff);
    border:2px solid #00bcd4;
    border-radius:25px;
    padding:50px;
    text-align:center;
    box-shadow:0 10px 40px rgba(0,188,212,0.12);
    animation:pulse 2s infinite;
}

@keyframes pulse{
    0%  { box-shadow:0 0 10px rgba(0,188,212,0.15); }
    50% { box-shadow:0 0 35px rgba(0,188,212,0.35); }
    100%{ box-shadow:0 0 10px rgba(0,188,212,0.15); }
}

h1,h2,h3,h4,h5,h6,p,span,div,label { color:#111827; }

</style>
""", unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════
# LOAD MODELS
# ════════════════════════════════════════════════════════════
@st.cache_resource
def load_models():
    try:
        return dict(
            crop    = joblib.load("crop_model.pkl"),
            fert    = joblib.load("fert_model.pkl"),
            le_fert = joblib.load("le_fert.pkl"),
        ), None
    except Exception as e:
        return None, str(e)

models, model_err = load_models()

# ════════════════════════════════════════════════════════════
# CLEAN SENSOR DATA
# ════════════════════════════════════════════════════════════
def clean_data(temp, hum, ph, N, P, K, moist):
    temp  = max(15.0, min(temp,  45.0))
    hum   = max(20.0, min(hum,  100.0))
    ph    = max(3.5,  min(ph,    9.0))
    N     = max(0.0,  min(N,   140.0))
    P     = max(5.0,  min(P,   145.0))
    K     = max(5.0,  min(K,   205.0))
    moist = max(0.0,  min(moist,100.0))
    return temp, hum, ph, N, P, K, moist

# ════════════════════════════════════════════════════════════
# AI PREDICTION
# BUG 1 FIX: added models is None guard
# ════════════════════════════════════════════════════════════
def run_prediction(temp, hum, ph, N, P, K, moist):
    # BUG 1 FIX: guard against models not loaded
    if models is None:
        return "Model Error", "Model Error"

    crop_df = pd.DataFrame(
        [[N, P, K, temp, hum, ph]],
        columns=['N', 'P', 'K', 'temperature', 'humidity', 'ph']
    )
    crop = str(models['crop'].predict(crop_df)[0]).capitalize()

    fert_df = pd.DataFrame(
        [[temp, moist, ph, N, P, K]],
        columns=['Temperature', 'Moisture', 'PH', 'Nitrogen', 'Phosphorous', 'Potassium']
    )
    fert_enc = models['fert'].predict(fert_df)
    fert = str(models['le_fert'].inverse_transform(fert_enc)[0])

    return crop, fert

# ════════════════════════════════════════════════════════════
# SERIAL READER
# BUG 3 FIX: removed double logging
# BUG 4 FIX: added time.sleep in exception handler
# ════════════════════════════════════════════════════════════
def serial_reader(port, baud, stop_event):
    try:
        ser = serial.Serial(port, baud, timeout=1)
        time.sleep(2)
        shared["log"].append(f"✅ Connected to {port}")
    except Exception as e:
        shared["status"]    = "error"
        shared["error_msg"] = str(e)
        return

    while not stop_event.is_set():
        try:
            line = ser.readline().decode(errors="ignore").strip()

            if not line:
                continue

            # BUG 3 FIX: log the line ONCE only, with friendly prefix
            if line.startswith("READING_SENSOR"):
                shared["log"].append("📡 Reading sensor...")
            elif line.startswith("DHT_ERROR"):
                shared["log"].append("⚠️ DHT sensor error — retrying...")
            elif line.startswith("MODBUS_ERROR"):
                shared["log"].append("⚠️ Modbus error — retrying...")
            elif line.startswith("SYSTEM_READY"):
                shared["log"].append("✅ ESP32 system ready")
            elif line.startswith("DATA:"):
                shared["log"].append("📊 Data received — running AI prediction...")

                parts = line[5:].split(",")
                if len(parts) == 7:
                    try:
                        temp, hum, ph, N, P, K, moist = [float(x) for x in parts]
                        temp, hum, ph, N, P, K, moist = clean_data(
                            temp, hum, ph, N, P, K, moist
                        )
                        shared["avg_data"] = dict(
                            temp=temp, hum=hum, ph=ph,
                            N=N, P=P, K=K, moist=moist
                        )
                        crop, fert = run_prediction(temp, hum, ph, N, P, K, moist)
                        shared["crop_result"] = crop
                        shared["fert_result"] = fert
                        shared["status"]      = "done"
                        ser.close()
                        return
                    except Exception as parse_err:
                        shared["log"].append(f"❌ Parse error: {parse_err}")
            else:
                # log any other line as-is (e.g. DONE_PRESS_RESET)
                shared["log"].append(line)

        except Exception as e:
            shared["log"].append(f"❌ Read error: {e}")
            time.sleep(0.5)   # BUG 4 FIX: prevent tight error loop

    try:
        ser.close()
    except Exception:
        pass

# ════════════════════════════════════════════════════════════
# RESET
# BUG 6 FIX: removed unused "sample_no" key
# ════════════════════════════════════════════════════════════
def reset_shared():
    shared.update(
        status="idle",
        avg_data=None,
        crop_result=None,
        fert_result=None,
        log=[],
        error_msg="",
        stop_event=None,
        start_time=None,
    )

# ════════════════════════════════════════════════════════════
# SIDEBAR
# ════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("## ⚙️ System Configuration")
    raw   = [p.device for p in serial.tools.list_ports.comports()]
    ports = raw if raw else ["COM4"]
    sel_port = st.selectbox("Select COM Port", ports)
    baud     = st.selectbox("Baud Rate", [115200, 9600])

    st.divider()

    if model_err:
        st.error(f"❌ {model_err}")
    else:
        st.success("✅ AI Models Loaded")

    st.divider()

    if shared["log"]:
        st.markdown("### 📋 Serial Monitor")
        # BUG 5 FIX: added key= to prevent widget conflict on rerun
        st.text_area("", "\n".join(shared["log"][-20:]), height=250, key="sidebar_log")

    if st.button("🔄 Reset Dashboard"):
        ev = shared.get("stop_event")
        if ev:
            ev.set()
        reset_shared()
        st.rerun()

# ════════════════════════════════════════════════════════════
# HEADER
# ════════════════════════════════════════════════════════════
st.markdown('<div class="title">🌱 AI Smart Soil Analysis System</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="subtitle">IoT + Machine Learning Based Crop & Fertilizer Recommendation Dashboard</div>',
    unsafe_allow_html=True
)
st.markdown("<br>", unsafe_allow_html=True)

status = shared["status"]

# ════════════════════════════════════════════════════════════
# IDLE
# ════════════════════════════════════════════════════════════
if status == "idle":

    st.markdown("""
    <div class="hero">
        <div style="font-size:100px">🌾</div>
        <h2>Ready For Smart Soil Analysis</h2>
        <p>
        Insert the NPK sensor and DHT sensor into the soil,
        then click the button below to start AI-powered analysis.
        The system will automatically recommend the best crop
        and fertilizer based on real-time soil conditions.
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    if st.button("🔬 Start Soil Analysis"):
        reset_shared()
        stop_ev = threading.Event()
        threading.Thread(
            target=serial_reader, args=(sel_port, baud, stop_ev), daemon=True
        ).start()
        shared["stop_event"] = stop_ev
        shared["status"]     = "reading"
        shared["start_time"] = time.time()
        st.rerun()

    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown("## 🚀 System Workflow")

    c1, c2, c3, c4 = st.columns(4)
    steps = [
        ("📥", "Insert Sensor",    "Place NPK and DHT sensors into the soil."),
        ("📡", "Collect Data",     "ESP32 reads real-time soil parameters."),
        ("🤖", "AI Processing",    "Machine learning models analyse soil condition."),
        ("🌾", "Recommendations",  "Best crop and fertilizer are predicted."),
    ]
    for col, (icon, title, desc) in zip([c1, c2, c3, c4], steps):
        with col:
            st.markdown(f"""
            <div class="step">
                <div style="font-size:50px">{icon}</div>
                <h4>{title}</h4>
                <p>{desc}</p>
            </div>
            """, unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════
# READING
# BUG 2 FIX: replaced 5-sample UI with single-sample reading UI
# ════════════════════════════════════════════════════════════
elif status == "reading":

    elapsed = int(time.time() - (shared["start_time"] or time.time()))

    tc, sc = st.columns([5, 1])
    with tc:
        st.markdown("### 📡 Reading Soil Sensor...")
    with sc:
        if st.button("⏹ Stop"):
            ev = shared.get("stop_event")
            if ev: ev.set()
            reset_shared()
            st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    _, mid, _ = st.columns([1, 2, 1])
    with mid:
        st.markdown(f"""
        <div class="read-box">
            <div style="font-size:90px">📡</div>
            <h1 style="font-size:2.2rem;font-weight:900;color:#111827;margin-top:10px">
                Reading Soil Sensor...
            </h1>
            <p style="color:#4b5563;font-size:1.05rem;margin-top:10px;line-height:1.8">
                ESP32 is communicating with the 7-in-1 soil sensor via RS485 Modbus.<br>
                Please keep the sensor still in the soil.
            </p>
            <br>
            <div style="font-size:1.1rem;font-weight:700;color:#0077ff">
                ⏱️ Elapsed: {elapsed}s — waiting for sensor data...
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Live log — BUG 5 FIX: unique key so no widget conflict on rerun
    if shared["log"]:
        st.markdown("### 📋 Live Sensor Activity")
        st.text_area(
            "",
            "\n".join(shared["log"][-15:]),
            height=180,
            key=f"live_log_{elapsed}"   # BUG 5 FIX: unique key per second
        )

    time.sleep(1)
    st.rerun()

# ════════════════════════════════════════════════════════════
# DONE
# ════════════════════════════════════════════════════════════
elif status == "done":

    data = shared["avg_data"]

    st.success("✅ AI Analysis Completed Successfully")
    st.markdown("<br>", unsafe_allow_html=True)

    # Results
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f"""
        <div class="result-card crop-card">
            <div class="result-icon">🌾</div>
            <div class="result-title">Recommended Crop</div>
            <div class="result-value">{shared["crop_result"] or "N/A"}</div>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
        <div class="result-card fert-card">
            <div class="result-icon">🌿</div>
            <div class="result-title">Recommended Fertilizer</div>
            <div class="result-value">{shared["fert_result"] or "N/A"}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br><br>", unsafe_allow_html=True)

    # Sensor values
    st.markdown("## 📊 Live Sensor Values")
    metrics = [
        ("🌡️", "Temperature", f"{data['temp']:.1f} °C"),
        ("💧", "Humidity",     f"{data['hum']:.1f}%"),
        ("🌊", "Moisture",     f"{data['moist']:.1f}%"),
        ("⚗️", "pH",           f"{data['ph']:.2f}"),
        ("🧪", "Nitrogen",     f"{data['N']:.0f}"),
        ("🧫", "Phosphorus",   f"{data['P']:.0f}"),
        ("⚡", "Potassium",    f"{data['K']:.0f}"),
    ]
    cols = st.columns(7)
    for col, (icon, label, value) in zip(cols, metrics):
        with col:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-icon">{icon}</div>
                <div class="metric-label">{label}</div>
                <div class="metric-value">{value}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<br><br>", unsafe_allow_html=True)

    # NPK Chart
    st.markdown("## 📈 NPK Nutrient Analysis")
    chart_df = pd.DataFrame({
        "Nutrients": ["Nitrogen", "Phosphorus", "Potassium"],
        "Values":    [data["N"],  data["P"],    data["K"]],
    }).set_index("Nutrients")
    st.bar_chart(chart_df, height=350)

    st.divider()
    st.info("💡 To analyse another soil spot, press **Reset Dashboard** in the sidebar.")

# ════════════════════════════════════════════════════════════
# ERROR
# ════════════════════════════════════════════════════════════
elif status == "error":
    st.error(f"❌ Serial Connection Error: {shared['error_msg']}")
    st.markdown("""
### Troubleshooting
- Ensure ESP32 is connected via USB
- Select the correct COM port in the sidebar
- Close Arduino IDE Serial Monitor (it blocks the port)
- Press the Reset button on the ESP32 and try again
""")
    if st.button("🔄 Try Again"):
        reset_shared()
        st.rerun()