# Robot.ino – Detailed Documentation

## Overview
`Robot.ino` is the **main Arduino sketch**. It runs on the Arduino board and is responsible for:
1. Reading serial commands from the PC
2. Managing robot movement state
3. Obstacle detection via ultrasonic sensor
4. Executing movement commands (forward, rotate left/right, stop)

---

## Table of Contents
1. Global Variables
2. Function Reference (`setup()`, `loop()`)
3. Control Flow & State Machine
4. Diagrams
5. Example Runtime Trace

---

## 1) Global Variables

| Variable | Type | Purpose | Initial Value |
|---|---|---|---|
| `current_cmd` | `char` | Holds the command being executed | `0` (null) |
| `stopped` | `bool` | Tracks if robot is stationary | `false` |

### Notes
- `current_cmd` is the "active" command; it persists until a new valid command arrives or obstacle forces stop.
- `stopped` tracks motion state (helps coordinate smooth transitions between commands).

---

## 2) Function Reference

### `setup()`

**Purpose:** Initialize all hardware and prepare the Arduino for operation.

**Called:** Once at startup.

**Steps:**

1. **Initialize right leg servo (pin 9)**
   ```
   R_leg_setup(9);
   ```
   Calls function from `Robot.cpp` to attach servo.

2. **Initialize left leg servo (pin 10)**
   ```
   L_leg_setup(10);
   ```

3. **Initialize ultrasonic sensor (pins 11, 12)**
   ```
   ultrsnc_head_setup(12, 11);
   // Echo pin: 12 (input)
   // Trigger pin: 11 (output)
   ```

4. **Stop robot (safety)**
   ```
   robot_stop();
   stopped = true;
   ```
   Ensures legs are neutral at startup.

5. **Start serial communication at 115200 baud**
   ```
   Serial.begin(115200);
   ```
   Matches the PC baud rate.

**Diagram:**
```mermaid
flowchart TD
  A["setup()"] --> B["R_leg_setup(9)"]
  B --> C["L_leg_setup(10)"]
  C --> D["ultrsnc_head_setup(12, 11)"]
  D --> E["robot_stop()"]
  E --> F["stopped = true"]
  F --> G["Serial.begin(115200)"]
  G --> H["Ready for loop()"]
```

---

### `loop()`

**Purpose:** Main execution loop that runs repeatedly until power off.

**Called:** Continuously after `setup()`.

**High-level flow:**
```
while (true) {
  1. Read serial command (if available)
  2. Detect obstacles with ultrasonic
  3. Execute current command (one step)
}
```

---

#### Part 1: Read Serial Command

**Code:**
```cpp
if (Serial.available() > 0)   // Data waiting?
{
    int in = Serial.read();    // Read one byte
    char cmd = (char) in;      // Convert to char
    
    if (cmd != current_cmd && (cmd == 'F' || cmd == 'L' || cmd == 'R' || cmd == 'S'))
    {
        if(!stopped)
        {
            robot_stop();
            stopped = true;
        }
        current_cmd = cmd;
    }
}
```

**Logic:**
1. Check if `Serial.available() > 0` (data in buffer)
2. If yes, read one byte and convert to char
3. If the command is:
   - **Different from current** AND
   - **One of F/L/R/S**
   
   Then:
   - If robot is moving (`!stopped`), call `robot_stop()` first
   - Set `stopped = true`
   - Store the new command in `current_cmd`

4. If serial data unavailable or invalid command, skip this section

**Purpose of "stop then move" logic:**
- Ensures smooth transition between commands
- Prevents leg conflicts (e.g., moving forward while rotating)

**Diagram:**
```mermaid
flowchart TD
  A["Serial.available()?"] -->|No| B["Skip serial"]
  A -->|Yes| C["Read byte → cmd"]
  C --> D{cmd != current_cmd<br/>AND<br/>cmd in F/L/R/S?}
  D -->|No| E["Ignore cmd"]
  D -->|Yes| F{stopped == false?}
  F -->|Yes| G["robot_stop()"]
  G --> H["stopped = true"]
  F -->|No| I["(already stopped)"]
  H --> J["current_cmd = cmd"]
  I --> J
  B --> K["Continue..."]
  E --> K
  J --> K
```

---

#### Part 2: Obstacle Detection

**Code:**
```cpp
float distance = read_distance();

if (distance > 0 && distance <= 15)   // Obstacle within 15 cm
{
    current_cmd = 'S';   // Force STOP
}
```

**Logic:**
1. Call `read_distance()` from `Robot.cpp` (returns distance in cm, or -1 if none detected)
2. If `0 < distance <= 15`:
   - Force `current_cmd = 'S'` (stops robot)
   - This overrides any command from serial

**Purpose:**
- Safety: prevent robot from crashing into obstacles
- Priority: obstacle avoidance > serial commands

**Note:**
- Distance reading takes ~2.34 ms max (due to `pulseIn()` timeout)
- `millis()` based delays allow this function to be non-blocking

---

#### Part 3: Execute Command (One Step)

**Code:**
```cpp
switch (current_cmd)
{
    case 'F':      // Move Forward
        move(500, 250);
        if(stopped == true) { stopped = false; }
        break;

    case 'L':      // Rotate Left
        rotate(RIGHT_LEG, 500, 250);
        if(stopped) { stopped = false; }
        break;

    case 'R':      // Rotate Right
        rotate(LEFT_LEG, 500, 250);
        if(stopped) { stopped = false; }
        break;

    case 'S':      // Stop
        if(!stopped) {
            robot_stop();
            stopped = true;
        }
        break;

    default:       // Invalid or uninitialized
        if(!stopped) {
            robot_stop();
            stopped = true;
        }
        break;
}
```

**Behavior per command:**

| Command | Action | Stops Robot First? |
|---|---|---|
| `'F'` | Calls `move(500, 250)` | Yes (before loop) |
| `'L'` | Calls `rotate(RIGHT_LEG, 500, 250)` | Yes (before loop) |
| `'R'` | Calls `rotate(LEFT_LEG, 500, 250)` | Yes (before loop) |
| `'S'` | Calls `robot_stop()` if not stopped | N/A |
| default | Calls `robot_stop()` if not stopped | N/A |

**Important:**
- `move()` and `rotate()` are **non-blocking**
  - Each call executes exactly **one state** of the state machine
  - The state advances only after the required delay has elapsed
  - Multiple calls are needed to complete a full step

- `stopped` flag tracks whether robot is mid-motion or idle
  - Used to prevent redundant `robot_stop()` calls
  - Set to `false` when motion command begins

**Full Loop Diagram:**
```mermaid
flowchart TD
  A["loop() starts"] --> B["Serial.available()?"]
  B -->|Yes| C["Read command, validate"]
  C --> D{New valid cmd?}
  D -->|Yes| E["Stop if moving"]
  E --> F["current_cmd = new cmd"]
  D -->|No| G["Keep current_cmd"]
  B -->|No| G

  F --> H["distance = read_distance()"]
  G --> H

  H --> I{distance in range<br/>0 < d <= 15?}
  I -->|Yes| J["current_cmd = 'S'"]
  I -->|No| K["Keep current_cmd"]

  J --> L["switch(current_cmd)"]
  K --> L

  L -->|'F'| M["move(500,250)"]
  L -->|'L'| N["rotate(RIGHT_LEG,500,250)"]
  L -->|'R'| O["rotate(LEFT_LEG,500,250)"]
  L -->|'S'| P["robot_stop() if needed"]
  L -->|default| Q["robot_stop() if needed"]

  M --> R["stopped = false"]
  N --> R
  O --> R
  P --> S["Continue to next iteration"]
  Q --> S
  R --> S

  S --> T["(loop repeats)"]
```

---

## 3) Control Flow & State Machine

### Complete Finite State Machine

The Robot.ino system can be modeled as a finite state machine with the following states and transitions:

```mermaid
stateDiagram-v2
  [*] --> INIT: Power On

  INIT --> STOPPED: setup() completes

  STOPPED --> MOVING_FORWARD: Serial 'F' received
  STOPPED --> MOVING_LEFT: Serial 'L' received
  STOPPED --> MOVING_RIGHT: Serial 'R' received
  STOPPED --> STOPPED: Serial 'S' received

  MOVING_FORWARD --> STOPPED: New command<br/>(robot_stop)
  MOVING_FORWARD --> STOPPED: Obstacle<br/>(distance ≤ 15cm)
  MOVING_FORWARD --> MOVING_FORWARD: Continue<br/>move(500,250)

  MOVING_LEFT --> STOPPED: New command<br/>(robot_stop)
  MOVING_LEFT --> STOPPED: Obstacle<br/>(distance ≤ 15cm)
  MOVING_LEFT --> MOVING_LEFT: Continue<br/>rotate(RIGHT_LEG,500,250)

  MOVING_RIGHT --> STOPPED: New command<br/>(robot_stop)
  MOVING_RIGHT --> STOPPED: Obstacle<br/>(distance ≤ 15cm)
  MOVING_RIGHT --> MOVING_RIGHT: Continue<br/>rotate(LEFT_LEG,500,250)

  STOPPED --> MOVING_FORWARD: Serial 'F'
  STOPPED --> MOVING_LEFT: Serial 'L'
  STOPPED --> MOVING_RIGHT: Serial 'R'

  note right of INIT
    Setup phase:
    - Attach servos
    - Init ultrasonic
    - Serial begin
    - robot_stop()
  end note

  note right of STOPPED
    State variables:
    - stopped = true
    - current_cmd = 'S' or 0
    Both legs at 90°
  end note

  note right of MOVING_FORWARD
    State variables:
    - stopped = false
    - current_cmd = 'F'
    Alternating leg motion
  end note

  note right of MOVING_LEFT
    State variables:
    - stopped = false
    - current_cmd = 'L'
    Right leg moving
  end note

  note right of MOVING_RIGHT
    State variables:
    - stopped = false
    - current_cmd = 'R'
    Left leg moving
  end note
```

### State Definitions

| State | `current_cmd` | `stopped` | Servo Action |
|---|---|---|---|
| **INIT** | `0` | `true` | Initializing hardware |
| **STOPPED** | `'S'` or `0` | `true` | Both legs at 90° |
| **MOVING_FORWARD** | `'F'` | `false` | `move(500, 250)` alternates legs |
| **MOVING_LEFT** | `'L'` | `false` | `rotate(RIGHT_LEG, 500, 250)` |
| **MOVING_RIGHT** | `'R'` | `false` | `rotate(LEFT_LEG, 500, 250)` |

### Transition Conditions

#### Entering States

**→ STOPPED:**
- From INIT: After `setup()` completes
- From any MOVING state:
  - New serial command received (different from current)
  - Obstacle detected (distance ≤ 15 cm)
  - Serial 'S' command received

**→ MOVING_FORWARD:**
- From STOPPED: Serial 'F' received

**→ MOVING_LEFT:**
- From STOPPED: Serial 'L' received

**→ MOVING_RIGHT:**
- From STOPPED: Serial 'R' received

#### Transition Priority (High → Low)
1. **Obstacle Detection** (distance ≤ 15 cm) → Forces `STOPPED` state
2. **New Serial Command** (different from current) → Transition via `STOPPED`
3. **Continue Current Command** → Stay in current state

### Command Hierarchy
```
Serial Input (from PC)
    ↓
(validate & store in current_cmd)
    ↓
Obstacle Detection
    ↓
(may override current_cmd to 'S')
    ↓
Execute current_cmd
```

### Robot States (Physical)
- **STOPPED:** Legs are at rest (90°)
- **MOVING:** One or both legs in motion (0° or 180°)

### Transition Rules
```
STOPPED + Serial 'F' → Start move() → MOVING_FORWARD
STOPPED + Serial 'L' → Start rotate(RIGHT_LEG) → MOVING_LEFT
STOPPED + Serial 'R' → Start rotate(LEFT_LEG) → MOVING_RIGHT
STOPPED + Serial 'S' → Stay STOPPED

MOVING_* + New command → Call robot_stop() first → STOPPED → Execute new

MOVING_* + Obstacle detected → Call robot_stop() → STOPPED
```

### State Transition Examples

**Example 1: Forward → Left Turn**
```
State: MOVING_FORWARD (current_cmd='F', stopped=false)
    ↓ Serial receives 'L'
    ↓ (cmd != current_cmd) → robot_stop()
State: STOPPED (current_cmd='L', stopped=true)
    ↓ Next loop iteration
    ↓ switch(current_cmd) → case 'L'
State: MOVING_LEFT (current_cmd='L', stopped=false)
```

**Example 2: Moving → Obstacle Detected**
```
State: MOVING_FORWARD (current_cmd='F', stopped=false)
    ↓ read_distance() returns 12 cm
    ↓ (distance ≤ 15) → current_cmd = 'S'
State: (transitioning) (current_cmd='S', stopped=false)
    ↓ switch(current_cmd) → case 'S'
    ↓ robot_stop() called
State: STOPPED (current_cmd='S', stopped=true)
```

**Example 3: Idle → Forward**
```
State: STOPPED (current_cmd=0, stopped=true)
    ↓ Serial receives 'F'
    ↓ (cmd != current_cmd) → current_cmd = 'F'
State: STOPPED (current_cmd='F', stopped=true)
    ↓ Next loop iteration
    ↓ switch(current_cmd) → case 'F'
    ↓ move(500, 250) called
State: MOVING_FORWARD (current_cmd='F', stopped=false)
```

---

## 4) Diagrams

### Startup Sequence
```mermaid
sequenceDiagram
  participant Power
  participant Arduino
  participant Servos
  participant Serial

  Power->>Arduino: Power on
  Arduino->>Arduino: setup()
  Arduino->>Servos: R_leg_setup(9)
  Arduino->>Servos: L_leg_setup(10)
  Arduino->>Servos: ultrsnc_head_setup(12,11)
  Arduino->>Servos: robot_stop()<br/>(legs to 90°)
  Arduino->>Serial: Serial.begin(115200)
  Arduino->>Arduino: Ready for loop()
  Serial->>Arduino: Waiting for commands...
```

### Command Processing State Machine
```mermaid
stateDiagram-v2
  [*] --> IDLE

  IDLE --> MOVING_F: Cmd 'F'
  IDLE --> MOVING_L: Cmd 'L'
  IDLE --> MOVING_R: Cmd 'R'
  IDLE --> STOPPED: Cmd 'S'

  MOVING_F --> IDLE: New cmd or\nobstacle
  MOVING_L --> IDLE: New cmd or\nobstacle
  MOVING_R --> IDLE: New cmd or\nobstacle

  STOPPED --> MOVING_F: Cmd 'F'
  STOPPED --> MOVING_L: Cmd 'L'
  STOPPED --> MOVING_R: Cmd 'R'

  note right of MOVING_F
    move(500, 250)
    executes step-by-step
  end note

  note right of MOVING_L
    rotate(RIGHT_LEG,500,250)
    executes step-by-step
  end note

  note right of MOVING_R
    rotate(LEFT_LEG,500,250)
    executes step-by-step
  end note
```

### Loop Timing (Approximate)
```
┌─ loop() iteration ─────────────────────────────────────┐
│                                                          │
│ Serial.read()        ~50 µs                             │
│ read_distance()      ~2340 µs (worst case)              │
│ move()/rotate()      ~50 µs (state advance)             │
│ (rest of loop)       ~100 µs                            │
│                                                          │
│ Total per iteration: ~2540 µs ≈ 2.54 ms               │
│                                                          │
│ Loop frequency:      ~393 loops/sec                     │
└────────────────────────────────────────────────────────┘

Note: move() and rotate() don't block the loop.
They use millis() timing, so delays happen
across multiple iterations.
```

---

## 5) Example Runtime Trace

### Scenario: Robot searching, then face detected, then obstacle

```
TIME    EVENT                               RESULT
────────────────────────────────────────────────────────────
 0 ms   Arduino starts
        setup() completes
        Serial ready                        current_cmd = 0, stopped = true

 1 ms   loop() → Serial has 'R'             current_cmd = 'R', stopped = false
        → rotate(LEFT_LEG, 500, 250)
        → (no obstacle)
        → Execute rotate (state: LEG_STOP)

 2 ms   loop() → No serial data
        → read_distance() → 100 cm
        → Execute rotate (state: LEG_MOVING)

 300 ms loop() → No serial data
        → distance = 100 cm
        → rotate() timings complete, state → LEG_STOP

 500 ms loop() → Serial has 'F'             current_cmd = 'F'
        → robot_stop() called first         stopped = true → false
        → move(500, 250) starts
        → (state: LEFT_STOP)

 505 ms loop() → No serial data
        → distance = 100 cm
        → move() continues (state: RIGHT_MOVING)

 800 ms loop() → No serial data
        → read_distance() → 12 cm (!!)      current_cmd = 'S' (forced!)
        → Stop immediately

 810 ms loop() → Serial has 'R'             current_cmd = 'R' (override)
        → robot_stop() called first
        → rotate(LEFT_LEG) starts

...     (continue)
```

---

## Summary

- **Purpose:** Read serial commands and execute robot movement
- **Main Loop:** Read → Detect obstacles → Execute (one step at a time)
- **Non-blocking:** Uses `millis()` for timing, not `delay()`
- **Safety:** Obstacle detection overrides serial commands
- **State:** Tracks `current_cmd` and `stopped` flag across iterations

