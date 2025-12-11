/* 
esp32cam
*/

#include "esp_camera.h"
#include <WiFi.h>
#include "FS.h"
#include "SD_MMC.h"

// -------- WIFI CONFIG --------
const char* WIFI_SSID = "xxxxxx";
const char* WIFI_PASS = "xxxxxx";

// -------- FLASH LED (AI THINKER uses GPIO 33 for onboard flash) --------
#define LED_FLASH_PIN 33   // DO NOT USE GPIO 4 (conflicts with SDIO)

// -------- Camera pin config for AI Thinker --------
#define PWDN_GPIO_NUM     32
#define RESET_GPIO_NUM    -1
#define XCLK_GPIO_NUM     0
#define SIOD_GPIO_NUM     26
#define SIOC_GPIO_NUM     27

#define Y9_GPIO_NUM       35
#define Y8_GPIO_NUM       34
#define Y7_GPIO_NUM       39
#define Y6_GPIO_NUM       36
#define Y5_GPIO_NUM       21
#define Y4_GPIO_NUM       19
#define Y3_GPIO_NUM       18
#define Y2_GPIO_NUM       5
#define VSYNC_GPIO_NUM    25
#define HREF_GPIO_NUM     23
#define PCLK_GPIO_NUM     22

WiFiServer server(80);

// -------- Timestamp generator --------
String getTimestamp() {
  time_t now = time(nullptr);
  if (now == 0) return "t" + String(millis() / 1000);

  struct tm ti;
  localtime_r(&now, &ti);
  char buf[32];
  strftime(buf, sizeof(buf), "%Y%m%d_%H%M%S", &ti);
  return String(buf);
}

// -------- Camera init --------
bool initCamera() {
  camera_config_t config;
  config.ledc_channel = LEDC_CHANNEL_0;
  config.ledc_timer = LEDC_TIMER_0;

  config.pin_d0 = Y2_GPIO_NUM;
  config.pin_d1 = Y3_GPIO_NUM;
  config.pin_d2 = Y4_GPIO_NUM;
  config.pin_d3 = Y5_GPIO_NUM;
  config.pin_d4 = Y6_GPIO_NUM;
  config.pin_d5 = Y7_GPIO_NUM;
  config.pin_d6 = Y8_GPIO_NUM;
  config.pin_d7 = Y9_GPIO_NUM;

  config.pin_xclk = XCLK_GPIO_NUM;
  config.pin_pclk = PCLK_GPIO_NUM;
  config.pin_vsync = VSYNC_GPIO_NUM;
  config.pin_href = HREF_GPIO_NUM;

  config.pin_sscb_sda = SIOD_GPIO_NUM;
  config.pin_sscb_scl = SIOC_GPIO_NUM;
  config.pin_pwdn = PWDN_GPIO_NUM;
  config.pin_reset = RESET_GPIO_NUM;

  config.xclk_freq_hz = 20000000;
  config.pixel_format = PIXFORMAT_JPEG;

  config.frame_size = FRAMESIZE_SVGA;
  config.jpeg_quality = 12;
  config.fb_count = 1;

  esp_err_t err = esp_camera_init(&config);
  return (err == ESP_OK);
}

// -------- SD init (uses 1-bit mode for stability) --------
bool initSD() {
  // 1-bit SDMMC mode = true
  if (!SD_MMC.begin("/sdcard", true)) {
    Serial.println("SD mount FAILED");
    return false;
  }

  if (SD_MMC.cardType() == CARD_NONE) {
    Serial.println("No SD card detected");
    return false;
  }

  Serial.println("SD OK (1-bit mode)");
  return true;
}

// -------- Save photo --------
void savePhotoToSD(const String &fname) {
  // turn on flash
  digitalWrite(LED_FLASH_PIN, HIGH);
  delay(60);

  camera_fb_t *fb = esp_camera_fb_get();

  // turn off flash
  digitalWrite(LED_FLASH_PIN, LOW);

  if (!fb) {
    Serial.println("PHOTO FAIL (no framebuffer)");
    return;
  }

  String path = "/" + fname + ".jpg";
  File file = SD_MMC.open(path, FILE_WRITE);

  if (!file) {
    Serial.println("FILE OPEN FAIL");
    esp_camera_fb_return(fb);
    return;
  }

  file.write(fb->buf, fb->len);
  Serial.printf("Saved %s (%u bytes)\n", path.c_str(), fb->len);

  file.close();
  esp_camera_fb_return(fb);
}

// -------- Handle incoming HTTP requests --------
void handleClient(WiFiClient client) {
  String req = client.readStringUntil('\r');
  client.readStringUntil('\n');

  if (req.indexOf("GET /capture") >= 0) {

    // Parse ?t=TIMESTAMP
    String t = "";
    int idx = req.indexOf("t=");
    if (idx > 0) {
      int s = idx + 2;
      int e = req.indexOf(' ', s);
      t = req.substring(s, e);
    }
    if (t == "") t = getTimestamp();

    savePhotoToSD("IMG_" + t);

    // Respond
    client.println("HTTP/1.1 200 OK");
    client.println("Content-Type: text/plain");
    client.println("Connection: close");
    client.println();
    client.println("OK");
    return;
  }

  // Default /
  client.println("HTTP/1.1 200 OK");
  client.println("Content-Type: text/plain");
  client.println();
  client.println("ESP32-CAM ready");
}

void setup() {
  Serial.begin(115200);
  delay(400);

  pinMode(LED_FLASH_PIN, OUTPUT);
  digitalWrite(LED_FLASH_PIN, LOW);

  WiFi.begin(WIFI_SSID, WIFI_PASS);
  Serial.print("WiFi ");
  while (WiFi.status() != WL_CONNECTED) {
    delay(250);
    Serial.print(".");
  }
  Serial.println("\nIP: " + WiFi.localIP().toString());

  if (initCamera()) Serial.println("CAM OK");
  else Serial.println("CAM FAIL");

  if (initSD()) Serial.println("SD READY");
  else Serial.println("SD ERROR");

  server.begin();
}

void loop() {
  WiFiClient c = server.available();
  if (c) {
    unsigned long t0 = millis();
    while (!c.available() && millis() - t0 < 1000) delay(1);
    if (c.available()) handleClient(c);
    c.stop();
  }
}

