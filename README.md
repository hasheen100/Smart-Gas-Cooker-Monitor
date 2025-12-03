# GasHealth Monitor - ESP32 Multi-Sensor Dashboard

<div align="center">


**Real-time Gas Cooker Safety Monitoring System**


*A comprehensive desktop application for monitoring gas cooker safety parameters using ESP32 and Python* 
*( GUI Development Tkinter usually comes with Python)*

</div>

## 📋 Table of Contents
- [✨ Features](#-features)
- [🛠️ Hardware Requirements](#️-hardware-requirements)
- [💻 Software Requirements](#-software-requirements)
- [🚀 Quick Start](#-quick-start)
- [📦 Installation](#-installation)
- [🔧 Usage Guide](#-usage-guide)
- [📊 Sensor Specifications](#-sensor-specifications)
- [🏗️ Project Structure](#️-project-structure)
- [🔌 Wiring Diagram](#-wiring-diagram)
- [📝 Code Examples](#-code-examples)
- [🤝 Contributing](#-contributing)
- [📄 License](#-license)
- [🙏 Acknowledgments](#-acknowledgments)

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

## 🛠️ Hardware Requirements

### **Essential Components**
| Component | Specification | Purpose |
|-----------|---------------|---------|
| **ESP32 Board** | ESP32 DevKit v1 or similar | Main microcontroller |
| **Gas Sensor** | MQ-2/MQ-5/MQ-9 | Gas concentration detection |
| **LDR Sensor** | Photoresistor GL5528 | Light intensity measurement |
| **Temperature Sensor** | LM35 or NTC thermistor | Temperature monitoring |
| **LEDs** | 5mm LEDs (Red/Green/Blue) | Status indicators |
| **Resistors** | 220Ω for LEDs, 10kΩ for LDR | Current limiting/pull-up |
| **Breadboard & Jumper Wires** | Standard kit | Circuit connections |
| **Doat Board** | Standard kit | Stable Circuit connections |

### **Optional Add-ons**
- **OLED Display** for local monitoring
- **Buzzer** for audible alerts
- **Relay Module** for automatic shutoff
- **External Power Supply** for stability

## 💻 Software Requirements

### **Python Dependencies**
```txt
Python >= 3.7
pyserial >= 3.5
numpy >= 1.19.0
tkinter (usually included with Python)
