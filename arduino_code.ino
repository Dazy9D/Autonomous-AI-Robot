#include <Servo.h>

// --- MOTOR PINS (L298N) ---
const int enA = 3;  
const int in1 = 4;  
const int in2 = 8;  

const int enB = 5;  
const int in3 = 7;  
const int in4 = 6;  

// --- SENSOR PINS ---
const int pirPin = 2;
const int trigPin = A0; 
const int echoPin = A1; 
const int servoPin = 11;

// --- VARIABLES ---
Servo neckServo;
long duration;
int distance;
bool humanDetectedFlag = false;
int robotSpeed = 150; 

// --- SERVO "RADAR" VARIABLES ---
unsigned long previousServoMillis = 0;
const long servoInterval = 30; 
int servoPos = 90;
int servoDirection = 1; 

// --- NEW: STATE TRACKER ---
bool isMoving = false; // Tracks if the robot is currently driving

void setup() {
  Serial.begin(9600); 
  
  pinMode(pirPin, INPUT);
  pinMode(trigPin, OUTPUT);
  pinMode(echoPin, INPUT);
  
  pinMode(enA, OUTPUT);
  pinMode(in1, OUTPUT);
  pinMode(in2, OUTPUT);
  
  pinMode(enB, OUTPUT);
  pinMode(in3, OUTPUT);
  pinMode(in4, OUTPUT);

  neckServo.attach(servoPin);
  neckServo.write(90); 

  stopMotors();
}

void loop() {
  // 1. REFLEX: Ultrasonic Crash Prevention
  digitalWrite(trigPin, LOW);
  delayMicroseconds(2);
  digitalWrite(trigPin, HIGH);
  delayMicroseconds(10);
  digitalWrite(trigPin, LOW);
  
  duration = pulseIn(echoPin, HIGH);
  distance = duration * 0.034 / 2;
  
  if (distance > 0 && distance < 15) { 
    stopMotors();
  }

  // --- UPDATED: SMART RADAR SWEEP ---
  // Only sweep the head if the robot is completely stopped
  if (!isMoving) {
    unsigned long currentMillis = millis();
    if (currentMillis - previousServoMillis >= servoInterval) {
      previousServoMillis = currentMillis;
      servoPos += servoDirection;
      
      if (servoPos >= 135 || servoPos <= 45) { 
        servoDirection = -servoDirection; 
      }
      neckServo.write(servoPos);
    }
  }

  // 2. SENSE: PIR Human Detection
  int currentPirState = digitalRead(pirPin);
  if (currentPirState == HIGH && !humanDetectedFlag) {
    Serial.println("HUMAN_DETECTED"); 
    humanDetectedFlag = true; 
  } else if (currentPirState == LOW) {
    humanDetectedFlag = false; 
  }

  // 3. LISTEN: Commands from the Raspberry Pi
  if (Serial.available() > 0) {
    String command = Serial.readStringUntil('\n');
    command.trim(); 
    
    if (command == "FORWARD" && distance >= 15) {
      moveForward();
    } else if (command == "BACKWARD") {
      moveBackward();
    } else if (command == "STOP") {
      stopMotors();
    }
  }
  
  delay(50); // Keep the loop stable
}

// --- Motor Control Functions ---

void moveForward() {
  isMoving = true;        // Tell the brain we are moving
  neckServo.write(90);    // Snap head to center to watch for crashes
  analogWrite(enA, robotSpeed); 
  analogWrite(enB, robotSpeed);
  digitalWrite(in1, HIGH); digitalWrite(in2, LOW);
  digitalWrite(in3, HIGH); digitalWrite(in4, LOW);
}

void moveBackward() {
  isMoving = true;        // Tell the brain we are moving
  neckServo.write(90);    // Snap head to center
  analogWrite(enA, robotSpeed); 
  analogWrite(enB, robotSpeed);
  digitalWrite(in1, LOW); digitalWrite(in2, HIGH);
  digitalWrite(in3, LOW); digitalWrite(in4, HIGH);
}

void stopMotors() {
  isMoving = false;       // Tell the brain we stopped (radar will resume)
  analogWrite(enA, 0); 
  analogWrite(enB, 0);
  digitalWrite(in1, LOW); digitalWrite(in2, LOW);
  digitalWrite(in3, LOW); digitalWrite(in4, LOW);
}


