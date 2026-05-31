/*
 * Smart Soil Analysis System — ESP32 Firmware
 * =============================================
 * Reads soil NPK, moisture, pH via RS-485 Modbus sensor
 * Reads temperature & humidity via DHT11
 * Averages TOTAL_SAMPLES readings and sends CSV over Serial
 *
 * Serial output format (sent to PC / bridge.py):
 *   DATA:<temp>,<hum>,<ph>,<N>,<P>,<K>,<moist>
 *
 * Hardware:
 *   - ESP32 DevKit
 *   - RS-485 to TTL module  (MAX485)  → GPIO 4 (RE/DE), 17 (TX2), 18 (RX2)
 *   - NPK + Moisture + pH sensor      → Modbus RTU slave ID 1
 *   - DHT11 temperature/humidity      → GPIO 15
 */

#include <ModbusMaster.h>
#include <DHT.h>

// ─── Pin definitions ───────────────────────────────────────
#define MAX485_RE_DE  4     // RS-485 direction pin (HIGH = transmit)
#define RX2_PIN      18     // UART2 RX
#define TX2_PIN      17     // UART2 TX
#define DHTPIN       15     // DHT11 data pin
#define DHTTYPE      DHT11

// ─── Sampling config ───────────────────────────────────────
const int TOTAL_SAMPLES    = 5;      // Number of readings to average
const int SAMPLE_DELAY_MS  = 10000;  // Delay between samples (ms)

// ─── Globals ───────────────────────────────────────────────
ModbusMaster node;
DHT           dht(DHTPIN, DHTTYPE);
bool          isFinished = false;

// ─── RS-485 direction control ──────────────────────────────
void preTransmission()  { digitalWrite(MAX485_RE_DE, HIGH); }
void postTransmission() { digitalWrite(MAX485_RE_DE, LOW);  }

// ───────────────────────────────────────────────────────────
void setup() {
  Serial.begin(115200);
  Serial2.begin(9600, SERIAL_8N1, RX2_PIN, TX2_PIN);

  pinMode(MAX485_RE_DE, OUTPUT);
  digitalWrite(MAX485_RE_DE, LOW);  // Start in receive mode

  node.begin(1, Serial2);           // Modbus slave ID = 1
  node.preTransmission(preTransmission);
  node.postTransmission(postTransmission);

  dht.begin();
  Serial.println("SYSTEM_READY");
  delay(2000);
}

// ───────────────────────────────────────────────────────────
void loop() {
  if (isFinished) {
    Serial.println("DONE_PRESS_RESET");
    delay(3000);
    return;
  }

  // Accumulators for averaging
  float tempSum = 0, humSum = 0, phSum = 0, moistSum = 0;
  float NSum    = 0, PSum   = 0, KSum  = 0;
  int   validSamples = 0;

  for (int i = 1; i <= TOTAL_SAMPLES; i++) {
    Serial.print("READING_SAMPLE:");
    Serial.println(i);

    // ── Read NPK sensor via Modbus (7 registers from 0x0000) ──
    uint8_t result = node.readHoldingRegisters(0x0000, 7);

    if (result == node.ku8MBSuccess) {

      // ── Read DHT11 ──
      float temp = dht.readTemperature();
      float hum  = dht.readHumidity();

      if (isnan(temp) || isnan(hum)) {
        Serial.println("DHT_ERROR");
        delay(3000);
        continue;
      }

      // Register map (from sensor datasheet)
      // 0x00 → Moisture ×10   0x03 → pH ×10
      // 0x04 → N (mg/kg)      0x05 → P (mg/kg)   0x06 → K (mg/kg)
      float    moist = node.getResponseBuffer(0) / 10.0;
      float    ph    = node.getResponseBuffer(3) / 10.0;
      uint16_t N     = node.getResponseBuffer(4);
      uint16_t P     = node.getResponseBuffer(5);
      uint16_t K     = node.getResponseBuffer(6);

      tempSum  += temp;
      humSum   += hum;
      phSum    += ph;
      moistSum += moist;
      NSum     += N;
      PSum     += P;
      KSum     += K;
      validSamples++;

      Serial.println("SAMPLE_OK");
    } else {
      Serial.println("MODBUS_ERROR");
    }

    if (i < TOTAL_SAMPLES) {
      Serial.println("WAITING_NEXT_SAMPLE");
      delay(SAMPLE_DELAY_MS);
    }
  }

  // ── Send averaged data if we have valid samples ────────────
  if (validSamples > 0) {
    float avgTemp  = tempSum  / validSamples;
    float avgHum   = humSum   / validSamples;
    float avgPh    = phSum    / validSamples;
    float avgMoist = moistSum / validSamples;
    float avgN     = NSum     / validSamples;
    float avgP     = PSum     / validSamples;
    float avgK     = KSum     / validSamples;

    // CSV line consumed by bridge.py
    Serial.print("DATA:");
    Serial.print(avgTemp);   Serial.print(",");
    Serial.print(avgHum);    Serial.print(",");
    Serial.print(avgPh);     Serial.print(",");
    Serial.print(avgN);      Serial.print(",");
    Serial.print(avgP);      Serial.print(",");
    Serial.print(avgK);      Serial.print(",");
    Serial.println(avgMoist);

    Serial.println("AVERAGE_COMPLETE");
    isFinished = true;
  } else {
    Serial.println("NO_VALID_SAMPLES");
    delay(3000);
  }
}
