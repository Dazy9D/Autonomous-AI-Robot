import speech_recognition as sr
from gtts import gTTS
import pygame
import os
import time
import serial
import threading
from llama_cpp import Llama
import uuid

# --- FLASK IMPORTS ---
from flask import Flask, render_template_string, request
import logging

# ==========================================
# 1. HARDWARE CONNECTION (Arduino)
# ==========================================
try:
    # Most Arduino Unos show up as ttyACM0. If it fails, try '/dev/ttyUSB0'
    arduino = serial.Serial('/dev/ttyACM0', 9600, timeout=1)
    time.sleep(2) 
    print("Serial Bridge: Connected to Arduino!")
except Exception as e:
    print(f"Serial Error: {e}. Is the Arduino plugged in?")
    exit()

# ==========================================
# 2. WEB SERVER SETUP (Flask)
# ==========================================
app = Flask(__name__)

# Suppress the messy Flask terminal text so it doesn't interrupt your AI prints
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

HTML_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=0">
    <title>Robot Remote</title>
    <style>
        body { background-color: #222; display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100vh; margin: 0; }
        .row { display: flex; justify-content: center; width: 100%; }
        .btn { background-color: #4CAF50; border: none; padding: 30px; font-size: 40px; margin: 10px; border-radius: 20px; width: 120px; height: 120px; touch-action: manipulation;}
        .btn:active { background-color: #3e8e41; transform: scale(0.95); }
        .btn-stop { background-color: #f44336; }
        .btn-stop:active { background-color: #da190b; }
    </style>
</head>
<body>
    <div class="row"><button class="btn" onclick="fetch('/command?action=FORWARD')">⬆️</button></div>
    <div class="row"><button class="btn btn-stop" onclick="fetch('/command?action=STOP')">🛑</button></div>
    <div class="row"><button class="btn" onclick="fetch('/command?action=BACKWARD')">⬇️</button></div>
</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(HTML_PAGE)

@app.route('/command')
def command():
    action = request.args.get('action')
    if action in ['FORWARD', 'BACKWARD', 'STOP']:
        print(f"\n[ Phone Command: {action} ]")
        arduino.write((action + '\n').encode())
    return "OK"

def run_flask_server():
    # use_reloader=False is MANDATORY when running Flask inside a thread!
    app.run(host='0.0.0.0', port=5000, use_reloader=False)


# ==========================================
# 3. AI & AUDIO SETUP
# ==========================================
pygame.mixer.init()

print("Loading the brain... please wait.")
llm = Llama(
    model_path="./tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf", 
    n_ctx=512,  
    n_threads=4, # Forces it to use all 4 Pi cores
    verbose=False,
    chat_format="chatml"
)

recognizer = sr.Recognizer()
# Tweak to make the mic cut off faster when you stop speaking
recognizer.dynamic_energy_threshold = True

def speak(text):
    print(f"Robot: {text}")
    tts = gTTS(text=text, lang='en')
    
    # Generate a totally unique filename for every single sentence
    filename = f"response_{uuid.uuid4().hex}.mp3"
    tts.save(filename)
    
    pygame.mixer.music.load(filename)
    pygame.mixer.music.play()
    
    while pygame.mixer.music.get_busy():
        time.sleep(0.1)
        
    pygame.mixer.music.unload()
    
    # Safety check: Only delete it if it actually exists
    if os.path.exists(filename):
        os.remove(filename)

def listen_to_arduino():
    while True:
        if arduino.in_waiting > 0:
            msg = arduino.readline().decode('utf-8').strip()
            if msg == "HUMAN_DETECTED":
                print("\n[ PIR SENSOR TRIPPED ]")
                speak("Hello there! I sense a human approaching. How can I help you today?")
        time.sleep(0.1)


# ==========================================
# 4. THREAD LAUNCHER & MAIN LOOP
# ==========================================

# Start the Arduino listening thread in the background
threading.Thread(target=listen_to_arduino, daemon=True).start()

# Start the Web Server in the background
threading.Thread(target=run_flask_server, daemon=True).start()
print("\n[ Web Remote Online! Connect phone to Pi's IP address on port 5000 ]")

print("\nSystem Ready! Put on your headset.")
print("-" * 40)
speak("Systems online. Ready for commands.")

# The Memory Bank (System Rules)
conversation_history = [
    {"role": "system", "content": "You are a friendly, helpful robot. Answer concisely in exactly one sentence."}
]

# The Main Voice Loop
with sr.Microphone() as source:
    print("Calibrating background noise...")
    recognizer.adjust_for_ambient_noise(source, duration=1)
    
    while True:
        print("\n[ Listening... Speak now! ]")
        try:
            # Lowered timeout/phrase limit so it processes your voice faster
            audio = recognizer.listen(source, timeout=5, phrase_time_limit=5)
            
            # Convert audio to text
            user_text = recognizer.recognize_google(audio).lower()
            print(f"You: {user_text}")
            
            # --- HARDWARE COMMAND OVERRIDES ---
            if "move forward" in user_text:
                speak("Moving forward.")
                arduino.write(b"FORWARD\n")
                continue
            elif "move backward" in user_text:
                speak("Reversing.")
                arduino.write(b"BACKWARD\n")
                continue
            elif "stop moving" in user_text:
                speak("Stopping motors.")
                arduino.write(b"STOP\n")
                continue
            
            # Secret shutdown command
            if "shut down" in user_text or "quit" in user_text:
                speak("Shutting down now. Goodbye!")
                arduino.write(b"STOP\n")
                break

            # --- AI CONVERSATION PIPELINE ---
            print("[ Thinking... ]")
            
            # Add your new question to the memory bank
            conversation_history.append({"role": "user", "content": user_text})
            
            # The Micro-Memory Sliding Window
            if len(conversation_history) > 3:
                conversation_history = [conversation_history[0]] + conversation_history[-2:]

            # Send the optimized memory bank to the LLM
            response = llm.create_chat_completion(
                messages=conversation_history,
                max_tokens=64
            )
            
            reply = response['choices'][0]['message']['content'].strip()
            
            # Speak the LLM's response out loud
            speak(reply)
            
            # Add the robot's answer to the memory bank so it remembers what it just said
            conversation_history.append({"role": "assistant", "content": reply})
            
        except sr.WaitTimeoutError:
            pass 
        except sr.UnknownValueError:
            print("[ Didn't catch that, trying again... ]")
        except Exception as e:
            print(f"[ Error: {e} ]")