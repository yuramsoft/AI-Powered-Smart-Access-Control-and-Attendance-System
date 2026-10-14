/*
 * ESP32 + MFRC522 RFID scan client — development reference only.
 * No physical relay/servo operation is performed by this sketch.
 * Use HTTPS with certificate validation outside an isolated test lab.
 * Do not commit real Wi-Fi credentials or device tokens.
 * Example MFRC522 wiring: SS=GPIO5, SCK=18, MOSI=23, MISO=19, RST=22.
 */
#include <WiFi.h>
#include <HTTPClient.h>
#include <SPI.h>
#include <MFRC522.h>

const char* WIFI_SSID = "REPLACE_WITH_WIFI_SSID";
const char* WIFI_PASSWORD = "REPLACE_WITH_WIFI_PASSWORD";
const char* API_URL = "http://192.168.1.10:8000/api/v1/access/scan/"; // local lab only
const char* DEVICE_ID = "lab-door-01";
const char* DEVICE_TOKEN = "REPLACE_WITH_PROVISIONED_TOKEN";
#define RFID_SS_PIN 5
#define RFID_RST_PIN 22
MFRC522 rfid(RFID_SS_PIN, RFID_RST_PIN);

String uidToHex() {
  String uid;
  for (byte i = 0; i < rfid.uid.size; i++) {
    if (rfid.uid.uidByte[i] < 0x10) uid += "0";
    uid += String(rfid.uid.uidByte[i], HEX);
  }
  uid.toUpperCase();
  return uid;
}

void connectWiFi() {
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  unsigned long started = millis();
  while (WiFi.status() != WL_CONNECTED && millis() - started < 20000) delay(500);
  if (WiFi.status() == WL_CONNECTED) {
    Serial.print("Wi-Fi connected; IP: "); Serial.println(WiFi.localIP());
  } else {
    Serial.println("Wi-Fi unavailable; no access decision; actuator remains disabled.");
  }
}

void sendScan(const String& cardUid) {
  if (WiFi.status() != WL_CONNECTED) { Serial.println("Backend unavailable; no grant."); return; }
  HTTPClient http;
  http.begin(API_URL); // For deployment configure HTTPS and validate server certificate.
  http.addHeader("Content-Type", "application/json");
  http.addHeader("X-Device-ID", DEVICE_ID);
  http.addHeader("X-Device-Token", DEVICE_TOKEN);
  String body = String("{\"device_id\":\"") + DEVICE_ID + "\",\"card_uid\":\"" + cardUid + "\",\"event_type\":\"ENTRY\"}";
  int code = http.POST(body);
  Serial.printf("HTTP status: %d\n", code);
  if (code > 0) Serial.println(http.getString());
  http.end();
  // Intentionally no actuator command here. Add only after a separate safety review.
}

void setup() {
  Serial.begin(115200);
  SPI.begin();
  rfid.PCD_Init();
  connectWiFi();
  Serial.println("RFID terminal ready.");
}

void loop() {
  if (!rfid.PICC_IsNewCardPresent() || !rfid.PICC_ReadCardSerial()) { delay(50); return; }
  String cardUid = uidToHex();
  Serial.print("Card UID: "); Serial.println(cardUid);
  sendScan(cardUid);
  rfid.PICC_HaltA();
  rfid.PCD_StopCrypto1();
  delay(1000); // simple demo debounce; replace with robust idempotency
}
