## 🤖 Autonomous AI Chatbot Robot with Movement and Voice Interaction

A robot that moves around on its own, avoids obstacles, detects nearby people, and talks with them in natural language. A Raspberry Pi 4 handles the "brain" (speech recognition, a local LLM, text-to-speech), while an Arduino Uno handles the "reflexes" (sensors and motors).
 
## Features
 
- **Autonomous movement** with ultrasonic obstacle detection (stops at < 15 cm)
- **Human presence detection** using a PIR sensor, which triggers a voice greeting
- **Voice conversation**: speech-to-text (Google API), replies from a local **TinyLlama 1.1B** via `llama.cpp`, and text-to-speech (gTTS)
- **Remote control** through a Flask web interface on port 5000 (FORWARD / BACKWARD / STOP)
- **Multithreaded** design so voice, web server, and serial communication run in parallel
## System Overview
 
| Layer | Hardware | Role |
|-------|----------|------|
| Brain | Raspberry Pi 4 (4GB) | STT, LLM inference, TTS, Flask server |
| Control board | Arduino Uno R3 | Sensor polling, motor control via L298N |
 
The Pi and Arduino communicate over USB serial. When the Arduino detects a person, it sends `HUMAN_DETECTED` and the Pi starts the conversation.
 
## Components
 
Raspberry Pi 4 (4GB), Arduino Uno R3, HC-SR04 ultrasonic sensor, HC-SR505 PIR sensor, microphone, speaker, 2x DC motors, L298N motor driver, 2WD chassis kit, 2x 18650 batteries, 3.5" Raspberry Pi display.
 
**Estimated total cost:** 19,800 BDT
 
## Getting Started
 
1. Wire the hardware following the circuit diagrams in this repo.
2. Upload the Arduino sketch to the Uno.
3. On the Raspberry Pi, install the dependencies (`llama-cpp-python`, `SpeechRecognition`, `gTTS`, `Flask`, `pyserial`) and download the TinyLlama 1.1B model.
4. Run the main script:
```bash
   python master_bot.py
```
5. To use remote control, connect your phone to the same network and open `http://<pi-ip>:5000`.
> An internet connection is needed for Google STT and gTTS. The LLM itself runs fully offline.
 
## Results
 
| Test Case | Avg. Response Time | Success Rate |
|-----------|--------------------|--------------|
| Obstacle detection | 0.53 s | 100% |
| Voice command | ~1 min | 91% |
| Emergency stop | 1.2 s | 98% |
 
## Known Limitations
 
- A 2.4A power bank can slow the Pi during heavy inference (it needs 3A).
- Voice response can lag on the Pi 4 with TinyLlama.



## Team
 
| Members |
|---|
| Tauhidul Islam Pranto |
| Puspita Biswas Oishee |
| Aishiki Banik |
| Faiyaz Bin Yousuf |
| Fahmida Haque Mahima |
 
Department of Computer Science and Engineering, BRAC University
