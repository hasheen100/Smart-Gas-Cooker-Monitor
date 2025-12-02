// ===================== PINS =====================
#define GAS_PIN   32
#define GAS_LED   27

#define LDR_PIN   35
#define LDR_LED   26

#define VOLT_PIN  34
#define VOLT_LED  25
#define ALWAYS_ON_LED 12


// ===================== GAS SENSOR =====================
int dangerLevel = 350;
float gasAlpha = 0.05;           // Reduced alpha for stronger smoothing
float filteredGas = 0.0;
const int gasSamples = 5;        // Moving average for extra smoothing
int gasBuffer[gasSamples];
int gasIndex = 0;
long gasTotal = 0;

// ===================== LDR SENSOR =====================
const int ldrSamples = 10;
int ldrReadings[ldrSamples];
int ldrIndex = 0;
long ldrTotal = 0;
int averageLDR = 0;
int darkThreshold = 1500;
float ldrAlpha = 0.03;           // Stronger LPF
float ldrLPF = 0.0;
unsigned long ldrPrevMillis = 0;
const unsigned long ldrInterval = 20;
unsigned long startTime;

// ===================== VOLTAGE SENSOR =====================
float thresholdVoltage = 2.0;
float voltAlpha = 0.05;
float filteredVoltage = 0;

// Mode control
bool manualMode = false;  // false = Auto, true = Manual

// Function declarations
void checkCommands();
void handleLEDCommand(String command);

void setup() {
  Serial.begin(115200);

  // LEDs
  pinMode(GAS_LED, OUTPUT);  digitalWrite(GAS_LED, LOW);
  pinMode(LDR_LED, OUTPUT);  digitalWrite(LDR_LED, LOW);
  pinMode(VOLT_LED, OUTPUT); digitalWrite(VOLT_LED, LOW);
  pinMode(ALWAYS_ON_LED, OUTPUT); digitalWrite(ALWAYS_ON_LED,HIGH);

  // GAS sensor init
  filteredGas = analogRead(GAS_PIN);
  for(int i=0; i<gasSamples; i++) {
    gasBuffer[i] = filteredGas;
    gasTotal += filteredGas;
  }

  // LDR init
  for(int i=0; i<ldrSamples; i++) {
    ldrReadings[i] = 0;
  }

  startTime = millis();
  Serial.println("SYSTEM_READY:Auto Mode");
}

void loop() {
  unsigned long currentMillis = millis();

  // Check for commands from Python app
  checkCommands();

  // ===================== GAS SENSOR =====================
  int rawGas = analogRead(GAS_PIN);

  // Moving average
  gasTotal -= gasBuffer[gasIndex];
  gasBuffer[gasIndex] = rawGas;
  gasTotal += gasBuffer[gasIndex];
  gasIndex = (gasIndex + 1) % gasSamples;
  float avgGas = gasTotal / (float)gasSamples;

  // Low-pass filter
  filteredGas = filteredGas + gasAlpha * (avgGas - filteredGas);

  // Send gas data
  Serial.print("GAS:");
  Serial.print(filteredGas);
  Serial.print(",");
  Serial.println(dangerLevel);

  // Auto mode LED control for Gas
  if(!manualMode) {
    if(filteredGas > dangerLevel) {
      digitalWrite(GAS_LED, HIGH);
    } else {
      digitalWrite(GAS_LED, LOW);
    }
  }

  // ===================== LDR SENSOR =====================
  if(currentMillis - ldrPrevMillis >= ldrInterval) {
    ldrPrevMillis = currentMillis;

    // Moving average
    ldrTotal -= ldrReadings[ldrIndex];
    ldrReadings[ldrIndex] = analogRead(LDR_PIN);
    ldrTotal += ldrReadings[ldrIndex];
    ldrIndex = (ldrIndex + 1) % ldrSamples;
    averageLDR = ldrTotal / ldrSamples;

    // Strong LPF
    ldrLPF = ldrLPF + ldrAlpha * (averageLDR - ldrLPF);

    // Send LDR data
    float t = (currentMillis - startTime)/1000.0;
    Serial.print("LDR:");
    Serial.print(t);
    Serial.print(",");
    Serial.println(ldrLPF);

    // Auto mode LED control for LDR
    if(!manualMode) {
      if(ldrLPF < darkThreshold) {
        digitalWrite(LDR_LED, LOW);
      } else {
        digitalWrite(LDR_LED, HIGH);
      }
    }
  }

  // ===================== VOLTAGE SENSOR =====================
  int rawVolt = analogRead(VOLT_PIN);
  float voltage = rawVolt * (3.3 / 4095.0);
  filteredVoltage = filteredVoltage + voltAlpha * (voltage - filteredVoltage);

  // Send voltage data
  Serial.print("VOLT:");
  Serial.print(0);
  Serial.print(",");
  Serial.print(filteredVoltage, 3);
  Serial.print(",");
  Serial.println(3.3);

  // Auto mode LED control for Voltage
  if(!manualMode) {
    if(filteredVoltage > thresholdVoltage) {
      digitalWrite(VOLT_LED, HIGH);
    } else {
      digitalWrite(VOLT_LED, LOW);
    }
  }

  // Send LED status
  Serial.print("LED_STATUS:");
  Serial.print(digitalRead(GAS_LED));
  Serial.print(",");
  Serial.print(digitalRead(LDR_LED));
  Serial.print(",");
  Serial.println(digitalRead(VOLT_LED));

  delay(50);
}

void checkCommands() {
  if (Serial.available() > 0) {
    String command = Serial.readStringUntil('\n');
    command.trim();
    
    if (command == "MODE_AUTO") {
      manualMode = false;
      Serial.println("MODE_CHANGED:AUTO");
    }
    else if (command == "MODE_MANUAL") {
      manualMode = true;
      Serial.println("MODE_CHANGED:MANUAL");
    }
    else if (command.startsWith("LED")) {
      if (manualMode) {
        handleLEDCommand(command);
      } else {
        Serial.println("ERROR: Switch to manual mode first");
      }
    }
  }
}

void handleLEDCommand(String command) {
  if (command == "LED1_ON") {
    digitalWrite(GAS_LED, HIGH);
    Serial.println("LED1:ON");
  }
  else if (command == "LED1_OFF") {
    digitalWrite(GAS_LED, LOW);
    Serial.println("LED1:OFF");
  }
  else if (command == "LED2_ON") {
    digitalWrite(LDR_LED, HIGH);
    Serial.println("LED2:ON");
  }
  else if (command == "LED2_OFF") {
    digitalWrite(LDR_LED, LOW);
    Serial.println("LED2:OFF");
  }
  else if (command == "LED3_ON") {
    digitalWrite(VOLT_LED, HIGH);
    Serial.println("LED3:ON");
  }
  else if (command == "LED3_OFF") {
    digitalWrite(VOLT_LED, LOW);
    Serial.println("LED3:OFF");
  }
  else if (command == "ALL_ON") {
    digitalWrite(GAS_LED, HIGH);
    digitalWrite(LDR_LED, HIGH);
    digitalWrite(VOLT_LED, HIGH);
    Serial.println("ALL_LEDS:ON");
  }
  else if (command == "ALL_OFF") {
    digitalWrite(GAS_LED, LOW);
    digitalWrite(LDR_LED, LOW);
    digitalWrite(VOLT_LED, LOW);
    Serial.println("ALL_LEDS:OFF");
  }
}