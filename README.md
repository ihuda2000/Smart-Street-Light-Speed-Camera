# Smart-Street-Light-Speed-Camera

This project is a DIY embedded speed-camera system built using an ESP32 DevKit, an HB100 Doppler radar module, an LM358 amplifier, and an ESP32-CAM.
The system detects vehicle speed using Doppler shift and automatically captures a photo when a speed threshold is exceeded. Photos are saved to a microSD card, and the ESP32 DevKit sends UDP telemetry (speed + timestamp) to a computer.


## Features
- HB100 Doppler radar with LM358 amplification
- Real-time FFT speed calculation on ESP32 DevKit
- Automatic speed-triggered photo capture
- ESP32-CAM SD card photo storage
- Local web interface (/list, /file?name=...) to browse images
- UDP telemetry to PC
- Power via USB or 5V power bank

## Hardware Used
- ESP32 DevKit (NodeMCU-32S)
- ESP32-CAM (AI-Thinker)
- HB100 Doppler Radar
- LM358 Op-Amp
- MicroSD card
- Breadboard, jumper wires

##Wiring Summary
- ESP32-CAM:
  Powered by 5V → 5V, GND → GND
  SD card wired internally (default AI Thinker pins)
  DevKit triggers capture via WiFi HTTP request
  
- HB100 → LM358:
- VCC → 5V
- GND → GND
- IF → LM358 + input
- LM358 output → ESP32 DevKit ADC pin GPIO36

Shared:
Common ground between both ESP32 boards
