# Sensor Connections — Smart Soil Analysis System

## Components

| Component | Description |
|---|---|
| ESP32 DevKit v1 | Main microcontroller |
| NPK + Moisture + pH Sensor | RS-485 Modbus RTU, slave ID 1 |
| MAX485 Module | RS-485 to TTL level shifter |
| DHT11 | Temperature & humidity sensor |

---

## ESP32 → MAX485 (RS-485 Level Shifter)

| MAX485 Pin | ESP32 GPIO | Notes |
|---|---|---|
| DE + RE (bridged) | GPIO 4 | Direction control (HIGH=TX, LOW=RX) |
| DI | GPIO 17 (TX2) | Data In (transmit to sensor) |
| RO | GPIO 18 (RX2) | Receiver Output (receive from sensor) |
| VCC | 3.3V | Power |
| GND | GND | Ground |

---

## MAX485 → NPK Sensor

| MAX485 Pin | Sensor Wire | Notes |
|---|---|---|
| A | A (Yellow) | RS-485 differential line A |
| B | B (White) | RS-485 differential line B |

Sensor Power:
- Red wire → 12V DC supply
- Black wire → GND (common with ESP32 GND)

---

## ESP32 → DHT11

| DHT11 Pin | ESP32 GPIO | Notes |
|---|---|---|
| VCC | 3.3V | Power |
| DATA | GPIO 15 | Data signal with 10kΩ pull-up to 3.3V |
| GND | GND | Ground |

---

## Modbus Register Map (NPK Sensor)

| Register | Address | Scale | Parameter |
|---|---|---|---|
| 0 | 0x0000 | ÷ 10 | Soil Moisture (%) |
| 1 | 0x0001 | ÷ 10 | Soil Temperature (°C) |
| 2 | 0x0002 | ÷ 10 | Electrical Conductivity |
| 3 | 0x0003 | ÷ 10 | Soil pH |
| 4 | 0x0004 | ×1 | Nitrogen — N (mg/kg) |
| 5 | 0x0005 | ×1 | Phosphorus — P (mg/kg) |
| 6 | 0x0006 | ×1 | Potassium — K (mg/kg) |

Modbus settings: **9600 baud, 8N1, Slave ID 1**

---

## Serial Data Output Format

The ESP32 sends one line over USB Serial (115200 baud) after averaging 5 samples:

```
DATA:<temp>,<hum>,<ph>,<N>,<P>,<K>,<moist>
```

Example:
```
DATA:28.50,65.30,6.80,62.00,48.00,41.00,55.40
```

`bridge.py` on the PC reads this line and feeds it into the ML models.

---

## Power Supply

| Rail | Source | Consumers |
|---|---|---|
| 5V USB | PC USB port | ESP32 |
| 3.3V | ESP32 onboard LDO | MAX485, DHT11 |
| 12V DC | External adapter | NPK/Moisture/pH sensor |

> ⚠️ The NPK sensor requires a dedicated 12V supply. Do **not** power it from the ESP32 3.3V pin.
