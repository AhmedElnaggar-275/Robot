# Documentation Index & Quick Reference

Welcome! This folder contains comprehensive documentation of the Face Tracking Robot project.

---

## 📚 Documentation Files

### 1. **REPORT.md** – System-Level Overview
   - **What:** High-level architecture, protocol, and design decisions
   - **Who should read:** Anyone new to the project
   - **Contains:** System diagrams, serial protocol, tuning guide
   - **Time to read:** ~10 minutes

### 2. **OBJECTDETECTION_DETAILED.md** – Python Script (PC-side)
   - **What:** Complete breakdown of `ObjectDetection.py`
   - **Who should read:** Developers modifying face detection or command logic
   - **Contains:** All functions, state diagram, data flow, examples
   - **Time to read:** ~20 minutes

### 3. **ROBOT_INO_DETAILED.md** – Arduino Sketch (Main)
   - **What:** Complete breakdown of `Robot.ino`
   - **Who should read:** Developers working on command handling or serial logic
   - **Contains:** `setup()` and `loop()` explained, state machine, timing
   - **Time to read:** ~15 minutes

### 4. **ROBOT_CPP_DETAILED.md** – Arduino Movement Implementation
   - **What:** Complete breakdown of `Robot.cpp` movement functions
   - **Who should read:** Developers tuning motion or implementing new movements
   - **Contains:** State machines, non-blocking timing, servo control, ultrasonic
   - **Time to read:** ~20 minutes

### 5. **ROBOT_H_DETAILED.md** – Arduino Header File
   - **What:** Complete reference of `Robot.h` constants and prototypes
   - **Who should read:** Anyone needing pin assignments or function signatures
   - **Contains:** Macros, enums, pin mapping, function lookup tables
   - **Time to read:** ~10 minutes

---

## 🗺️ Quick Navigation by Task

### "I want to understand the whole system"
→ Read: **REPORT.md**

### "The robot isn't detecting faces correctly"
→ Read: **OBJECTDETECTION_DETAILED.md** → Section 3.3 (calculate_movement_command)

### "I want to change face detection thresholds"
→ Read: **OBJECTDETECTION_DETAILED.md** → Section 4 (Data Flow & State)

### "Commands aren't reaching the Arduino"
→ Read: **ROBOT_INO_DETAILED.md** → Section 2 (loop function, Part 1)

### "The robot moves slowly/jerky"
→ Read: **ROBOT_CPP_DETAILED.md** → Section 5 (State Machines)

### "I need to change servo angles or timings"
→ Read: **ROBOT_H_DETAILED.md** → Section 2 (Macros)
        + **ROBOT_CPP_DETAILED.md** → Section 5 (move/rotate functions)

### "What pins are used and why?"
→ Read: **ROBOT_H_DETAILED.md** → Section 5 (Pin Configuration table)

### "How does the robot avoid obstacles?"
→ Read: **ROBOT_INO_DETAILED.md** → Section 2 (loop, Part 2)
        + **ROBOT_CPP_DETAILED.md** → Section 3 (read_distance)

---

## 📊 File Structure

```
Robot/
├── ObjectDetection.py          [PC-side Python face detection + serial]
├── Robot.ino                   [Arduino main sketch]
├── Robot.cpp                   [Arduino movement implementation]
├── Robot.h                     [Arduino header with macros/enums]
│
├── REPORT.md                   [System overview & architecture]
├── OBJECTDETECTION_DETAILED.md [Python documentation]
├── ROBOT_INO_DETAILED.md       [Arduino sketch documentation]
├── ROBOT_CPP_DETAILED.md       [Arduino implementation documentation]
├── ROBOT_H_DETAILED.md         [Header file reference]
└── DOCUMENTATION_INDEX.md      [This file]
```

---

## 🔄 Data Flow Summary

```
┌─────────────────────────────────────────────────────────┐
│ PC (ObjectDetection.py)                                │
│                                                         │
│ Camera → Face Detect → Decision Logic → Serial Write   │
│                            ↓                            │
│                       F / L / R / S                    │
└─────────────────────────────────────────────────────────┘
                           ↓ USB Serial
                      115200 baud
                           ↓
┌─────────────────────────────────────────────────────────┐
│ Arduino (Robot.ino + Robot.cpp)                        │
│                                                         │
│ Serial Read → Validate Command → Obstacle Check       │
│                ↓                  ↓                     │
│           Execute Move      Override if needed         │
│           (State Machine)                              │
│                ↓                                        │
│           Servo Control (Legs)                         │
└─────────────────────────────────────────────────────────┘
```

---

## ⚡ Key Concepts

### Commands (F/L/R/S)
| Command | Meaning | Action |
|---|---|---|
| `F` | Forward | Both legs move forward alternately |
| `L` | Rotate Left | Right leg moves, left locked |
| `R` | Rotate Right | Left leg moves, right locked |
| `S` | Stop | Both legs go to neutral (90°) |

### Decision Logic (Python)
```
No face detected     → Send 'R' (search)
Face too close       → Send 'S' (stop)
Face off-center      → Send 'L' or 'R' (turn)
Face centered        → Send 'F' (forward)
```

### Non-blocking Motion (Arduino)
- Uses `millis()` instead of `delay()`
- Allows serial reading while servos move
- `loop()` runs ~393 times per second
- Each `move()` / `rotate()` call advances one state

### State Machines

**Walk (4 states):**
- LEFT_STOP → RIGHT_MOVING → RIGHT_STOP → LEFT_MOVING → [repeat]

**Rotate (2 states):**
- LEG_STOP → LEG_MOVING → [repeat]

---

## 🔧 Common Tuning Parameters

| Parameter | File | Default | Purpose |
|---|---|---|---|
| `dead_zone` | ObjectDetection.py | 80 pixels | Turning sensitivity |
| `max_face_size` | ObjectDetection.py | 60000 | "Too close" threshold |
| `min_face_size` | ObjectDetection.py | 15000 | UI only (unused) |
| `t_motion_delayms` | Robot.cpp | 500 ms | Servo motion duration |
| `t_stop_delayms` | Robot.cpp | 250 ms | Pause between steps |
| Servo angles | Robot.h | 0/90/180° | Movement range |

---

## ⚠️ Known Limitations

1. **Python:** `min_face_size` is used only for UI display (shows "TOO FAR"), not for command decisions
2. **Arduino:** Obstacle detection overrides all serial commands
3. **Distance:** Ultrasonic can only detect objects within ~40 cm
4. **Frame Rate:** Python FPS depends on camera + processing (~20–30 FPS typical)
5. **Command Frequency:** Python de-spams by sending only on change or every 5 frames

---

## 🚀 Quick Start

### Setup Arduino
1. Open `Robot.ino` in Arduino IDE
2. Select correct board and COM port
3. Upload

### Setup Python
```bash
pip install opencv-python pyserial
python ObjectDetection.py
```
- Follow prompts to select Arduino port and camera ID
- Press 'q' to quit

---

## 📞 Troubleshooting

**No face detected even with face visible?**
- Increase `minNeighbors` in `detect_face()` to reduce false positives
- Ensure adequate lighting
- Try adjusting `scaleFactor`

**Robot moves too slow/fast?**
- Change `t_motion_delayms` and `t_stop_delayms` in `move()`/`rotate()` calls

**Servos jerky or unstable?**
- Increase `t_stop_delayms` for longer pause between steps
- Check servo power supply stability

**Serial communication fails?**
- Verify baud rate is 115200 on both sides
- Check USB cable connection
- Try different COM port number
- Run `find_arduino_port()` to auto-detect

**Obstacle detection not working?**
- Check TRIG (pin 11) and ECHO (pin 12) connections
- Test with `Serial.println(read_distance())` to debug

---

## 📄 Function Quick Reference

### Python (ObjectDetection.py)
- `__init__()` – Initialize camera, serial, face detector
- `detect_face(frame)` – Haar cascade face detection
- `calculate_movement_command(face_rect)` – Decision logic
- `send_to_arduino(command)` – Serial write (with throttling)
- `draw_interface(...)` – UI overlay drawing
- `run()` – Main loop
- `cleanup()` – Close resources
- `find_arduino_port()` – Auto-detect Arduino

### Arduino (Robot.ino)
- `setup()` – Initialize hardware
- `loop()` – Main loop (read serial → obstacles → execute)

### Arduino (Robot.cpp)
- `R_leg_setup()`, `L_leg_setup()` – Servo init
- `ultrsnc_head_setup()` – Ultrasonic init
- `robot_stop()` – Stop both legs
- `read_distance()` – Ultrasonic measurement
- `leg_act()` – Send servo command
- `move()` – Forward walk FSM
- `rotate()` – Rotation FSM

### Arduino (Robot.h)
- **Macros:** `RIGHT_LEG`, `LEFT_LEG`, `MOVE_R`, `MOVE_L`, `STOP`
- **Enums:** `WalkState`, `RotateState`
- **Prototypes:** All function declarations

---

## 📖 Reading Recommendations by Experience Level

### Beginner
1. Read **REPORT.md** for overview
2. Read **ROBOT_H_DETAILED.md** for macro reference
3. Skim **ROBOT_INO_DETAILED.md** section 1

### Intermediate
1. Read all main documentation files in order
2. Focus on state machine diagrams
3. Trace a single command from PC to servos

### Advanced
1. Review all code directly
2. Use diagrams as reference for modifications
3. Understand non-blocking timing in Robot.cpp

---

## 📝 Notes

- All diagrams use Mermaid syntax (rendered in GitHub)
- Timing values (ms) are approximate; actual depends on Arduino load
- Serial communication is one-way (PC → Arduino only)
- No feedback from Arduino back to PC

---

**Last Updated:** December 27, 2025
**Repository:** AhmedElnaggar-275/Robot
**Branch:** main

