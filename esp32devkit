/*
esp32_devkit.ino
*/

#include <WiFi.h>
#include <WiFiUdp.h>
#include <HTTPClient.h>
#include <arduinoFFT.h>

// ------------------------ WIFI ------------------------
const char* WIFI_SSID     = "xxxxxx";
const char* WIFI_PASS     = "xxxxxx";

// ESP32-CAM target
const char* CAM_IP        = "xxxxxx";     // <-- update if CAM IP changes
const uint16_t CAM_PORT   = 80;

// PC for UDP telemetry
const char* PC_IP         = "xxxxxx";      // <-- your laptop IP
const uint16_t PC_UDP_PORT = 4210;

// Speed threshold
float SPEED_THRESHOLD_KMH = 0.30;    // adjust as needed

// FFT settings
const uint16_t SAMPLES = 1024;
const uint32_t SAMPLE_RATE = 8192;
const float HZ_PER_BIN = (float)SAMPLE_RATE / SAMPLES;
const float HZ_TO_KMH = 0.05134;

// ADC pin
const int ADC_PIN = 36;   // GPIO36

// Buffers
double vReal[SAMPLES];
double vImag[SAMPLES];

ArduinoFFT<double> FFT(vReal, vImag, SAMPLES, SAMPLE_RATE);

WiFiUDP udp;

// cooldown
unsigned long lastTrigger = 0;
const unsigned long TRIGGER_COOLDOWN_MS = 3000;

// NTP
#include "time.h"
const char* ntpServer = "pool.ntp.org";

// ------------------------ TIMESTAMP ------------------------
String getTimestamp() {
  time_t now = time(nullptr);
  if (now == 0) return "t" + String(millis() / 1000);

  struct tm ti;
  localtime_r(&now, &ti);
  char buf[32];
  strftime(buf, sizeof(buf), "%Y%m%d_%H%M%S", &ti);
  return String(buf);
}

// ------------------------ FFT MEASUREMENT ------------------------
float measureDopplerHz() {
  const float delayMicros = 1000000.0 / SAMPLE_RATE;

  for (int i = 0; i < SAMPLES; i++) {
    vReal[i] = analogRead(ADC_PIN) - 2048;
    vImag[i] = 0;

    uint32_t t0 = micros();
    while (micros() - t0 < delayMicros);
  }

  FFT.windowing(FFTWindow::Hann, FFTDirection::Forward);
  FFT.compute(FFTDirection::Forward);
  FFT.complexToMagnitude();

  int peakBin = 1;
  double peakVal = 0;

  for (int i = 1; i < SAMPLES/2; i++) {
    if (vReal[i] > peakVal) {
      peakVal = vReal[i];
      peakBin = i;
    }
  }

  float freq = peakBin * HZ_PER_BIN;

  Serial.printf("FFT Peak = %.1f Hz (bin %d)\n", freq, peakBin);

  return freq;
}

// ------------------------ CAMERA REQUEST ------------------------
bool triggerCamera(const String &ts) {
  if (WiFi.status() != WL_CONNECTED) return false;

  String url = "http://" + String(CAM_IP) + "/capture?t=" + ts;
  HTTPClient http;

  Serial.println("Triggering camera: " + url);

  http.begin(url);
  int code = http.GET();
  http.end();

  return (code == 200);
}

// ------------------------ UDP TELEMETRY ------------------------
void sendUDP(const String &ts, float speed) {
  char msg[128];
  snprintf(msg, sizeof(msg),
           "{\"ts\":\"%s\",\"speed\":%.2f}",
           ts.c_str(), speed);

  udp.beginPacket(PC_IP, PC_UDP_PORT);
  udp.write((uint8_t*)msg, strlen(msg));
  udp.endPacket();
}

// ------------------------ SETUP ------------------------
void setup() {
  Serial.begin(115200);
  delay(300);

  Serial.println("Connecting WiFi...");
  WiFi.begin(WIFI_SSID, WIFI_PASS);

  while (WiFi.status() != WL_CONNECTED) {
    delay(300);
    Serial.print(".");
  }
  Serial.println("\nConnected. IP: " + WiFi.localIP().toString());

  udp.begin(WiFi.localIP(), 0);
  configTime(0, 0, ntpServer);

  Serial.println("DevKit Ready.");
}

// ------------------------ LOOP ------------------------
void loop() {
  float dopplerHz = measureDopplerHz();
  float speedKmh = dopplerHz * HZ_TO_KMH;

  Serial.printf("Speed = %.2f km/h\n", speedKmh);

  unsigned long now = millis();

  if (speedKmh > SPEED_THRESHOLD_KMH &&
      now - lastTrigger > TRIGGER_COOLDOWN_MS) {

    lastTrigger = now;
    String ts = getTimestamp();

    bool camOK = triggerCamera(ts);

    if (!camOK)
      Serial.println("CAMERA FAIL");
    else
      Serial.println("CAMERA OK");

    sendUDP(ts, speedKmh);
    Serial.println("UDP sent");
  }

  delay(80);
}

