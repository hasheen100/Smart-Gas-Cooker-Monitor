# GasHealth Monitor - ESP32 Multi-Sensor Dashboard

<div align="center">

<img width="1364" height="719" alt="image" src="https://github.com/user-attachments/assets/ef9f42ba-5601-43a3-af9a-ed7e79f8e5a2" />
**Real-time Gas Cooker Safety Monitoring System**


*A comprehensive desktop application for monitoring gas cooker safety parameters using ESP32 and Python* 
*( GUI Development Tkinter usually comes with Python)*
<img width="1364" height="716" alt="image" src="https://github.com/user-attachments/assets/02c57c36-7a26-4ca9-bbe3-9c5a1bf20e71" />


</div>

## 📋 Table of Contents
- [✨ Features](#-features)
- [🛠️ Hardware Requirements](#️-hardware-requirements)
- [💻 Software Requirements](#-software-requirements)


## ✨ Features

### **🎯 Core Capabilities**
- **Real-time Monitoring** of Gas, Light, and Temperature sensors
- **Three Visualization Modes** for each sensor (Graph, Speed Meter, Digital)
- **Dual Operation Modes** (Auto Monitoring & Manual Control)
- **Advanced Noise Filtering** for stable readings
- **Automatic Warning System** for unsafe conditions

### **📊 Visualization Options**
| Sensor | Graph View | Speed Meter | Digital Display |
|--------|------------|-------------|-----------------|
| **Gas** | Time-series with danger line | Color-coded gauge | Large digits with status |
| **Light** | Threshold-based graph | Brightness meter | ADC values with state |
| **Temperature** | Temperature trend | Multi-zone gauge | Celsius display |


### **⚡ Performance**
- **100ms update rate** for real-time responsiveness
- **Adaptive filtering** that improves over time
- **Efficient memory usage** with optimized buffers
- **Thread-safe serial communication**
- - **can change the Sensivity**

## 🛠️ Hardware Requirements

### **Essential Components**
| Component | Specification | Purpose |
|-----------|---------------|---------|
| **ESP32 Board** | ESP32 DevKit v1 or similar | Main microcontroller |
| **Gas Sensor** | MQ-2/MQ-135 | Gas concentration detection |
| **LDR Sensor** | Photoresistor GL5528 | Light intensity measurement |
| **Temperature Sensor** | NTC thermistor | Temperature monitoring |
| **LEDs** | 5mm LEDs (Red/Green/RED) | Status indicators |
| **Resistors** | 220Ω for LEDs, 10kΩ for LDR | Current limiting/pull-up |
| **Breadboard & Jumper Wires** | Standard kit | Circuit connections |
| **Doat Board** | Standard kit | Stable Circuit connections |

### **Optional Add-ons**
- **OLED Display** for local monitoring
- **Buzzer** for Danger thinges
- **Relay Module** for automatic shutoff
- **External Power Supply** for stability

## 💻 Software Requirements

### **Python Dependencies**
```txt
Python >= 3.7(Basically needed)
tkinter (usually included with Python)
(I uploaded .exe fle,So can try it)


