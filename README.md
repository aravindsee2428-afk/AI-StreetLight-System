# 💡 AI-Based Smart Street Lighting System

An intelligent street lighting system that uses **Artificial Intelligence (YOLOv8)** and **ESP32** to automatically adjust street light brightness based on real-time pedestrian detection, improving energy efficiency while ensuring public safety.

---

## 📌 Project Overview

Traditional street lights operate at full brightness throughout the night, regardless of road occupancy, resulting in unnecessary energy consumption.

This project introduces an **AI-based smart street lighting system** that analyzes live CCTV/IP camera video using the **YOLOv8 object detection model** to detect and count pedestrians. According to the number of detected people, the system dynamically adjusts the brightness of LED street lights using an **ESP32 microcontroller** and **PWM (Pulse Width Modulation)**.

The system also incorporates an **LDR sensor** for automatic day/night detection and **RCWL-0516 microwave sensors** for backup motion detection, making the solution reliable, scalable, and suitable for future smart city applications.

---

# 🚀 Features

- ✅ Real-time person detection using YOLOv8
- ✅ AI-based pedestrian counting
- ✅ Automatic LED brightness adjustment
- ✅ ESP32-based PWM light control
- ✅ LDR-based day/night detection
- ✅ RCWL-0516 microwave motion sensing
- ✅ Energy-efficient street lighting
- ✅ Existing CCTV/IP camera compatible
- ✅ Low-cost and scalable architecture

---

# 🛠 Hardware Used

| Component | Purpose |
|-----------|---------|
| ESP32 Development Board | Main Controller |
| RCWL-0516 Microwave Sensor | Motion Detection |
| LDR Sensor | Day/Night Detection |
| MOSFET Driver | LED Brightness Control |
| 12V LED Strip | Street Light Prototype |
| LM2596 Buck Converter | 12V to 5V Regulation |
| 12V DC Power Supply | Power Source |
| Mobile Phone (IP Webcam) | Prototype Camera |
| Laptop | AI Processing Unit |

---

# 💻 Software Used

- Python 3.x
- Arduino IDE
- OpenCV
- Ultralytics YOLOv8
- NumPy
- PySerial
- VS Code

---

# ⚙ System Architecture

```
                IP Camera / CCTV
                        │
                        ▼
             YOLOv8 Person Detection
                        │
                        ▼
              Person Counting Algorithm
                        │
                        ▼
          Calculate Required Brightness
                        │
                        ▼
        USB Serial / Wi-Fi Communication
                        │
                        ▼
                    ESP32 Controller
                        │
                PWM Signal Generation
                        │
                        ▼
             MOSFET LED Driver Circuit
                        │
                        ▼
              Street Light Brightness
```

---

# 🔄 Working Principle

1. LDR detects whether it is daytime or nighttime.
2. During nighttime, the IP camera continuously captures live video.
3. YOLOv8 detects and counts pedestrians in real time.
4. The AI calculates the appropriate brightness level.
5. The brightness value is sent to the ESP32.
6. ESP32 generates a PWM signal.
7. MOSFET adjusts the LED brightness accordingly.
8. RCWL-0516 sensors provide additional motion detection for improved reliability.

---

# 💡 Brightness Logic

| Number of People | Brightness |
|------------------|-----------|
| 0 | 20% |
| 1 | 40% |
| 2 | 60% |
| 3 | 80% |
| 4 or More | 100% |

---

# 📂 Repository Structure

```
AI-StreetLight-System
│
├── AI_Code
│   ├── main.py
│   ├── camera_test.py
│   ├── esp32_serial.py
│
├── ESP32_Code
│
├── Circuit
│
├── Images
│
├── PPT
│
├── Report
│
├── requirements.txt
│
└── README.md
```

---

# ▶ Installation

## Clone Repository

```bash
git clone https://github.com/aravindsee2428-afk/AI-StreetLight-System.git
```

## Install Python Libraries

```bash
pip install -r requirements.txt
```

## Download YOLOv8 Model

The model will automatically download during the first execution.

---

# 📷 Sample Output

The AI system performs:

- Real-time pedestrian detection
- Person counting
- Dynamic brightness calculation
- Automatic LED brightness control

---

# 🌍 Applications

- Smart Cities
- Residential Roads
- College Campuses
- Parks
- Industrial Areas
- Smart Highway Lighting

---

# 🔮 Future Improvements

- Wi-Fi Communication between AI and ESP32
- Cloud-based IoT Dashboard
- Multiple CCTV Camera Integration
- Vehicle Detection
- Emergency Vehicle Priority Lighting
- Predictive Energy Analytics
- Solar-Powered Smart Street Lights

---

# 👨‍💻 Team

**Project Title**

AI-Based Smart Street Lighting System

**Developed by**

- Aravind Sanakan
- Athul Krishna V
- Abhiram Raghu R
- Midhun SK

**Department**

Electrical and Electronics Engineering (EEE)

**College**

Saintgits College of Engineering (Autonomous)

---

# 📜 License

This project is developed for academic and research purposes.

---

## ⭐ If you found this project useful, consider giving the repository a Star!
