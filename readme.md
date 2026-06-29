# 🚁 Project Title: Autonomous Telemetry & Control Streams via Pymavlink

### Developer Name: Priyanshu

### Status: Phase 1 – Week 1 Milestone Achieved Successfully

---

# 1. Executive Summary

This project focuses on developing an autonomous UAV control framework using the MAVLink communication protocol and ArduPilot's Software-In-The-Loop (SITL) simulation environment.

The primary objective of Phase 1 was to establish reliable telemetry and command communication between an independent Python application and a simulated quadcopter flight controller. The implemented solution successfully demonstrated automated mode switching, vehicle arming, autonomous takeoff, hovering, and landing without manual pilot intervention.

The successful completion of this milestone validates the software architecture required for future navigation and mission-planning capabilities.

---

# 2. Technical Objective

The objectives of Phase 1 were:

* Establish a functional ArduPilot SITL environment.
* Create a MAVLink communication bridge using `pymavlink`.
* Develop an independent Python-based flight controller.
* Programmatically bypass development-stage pre-arm checks.
* Switch the vehicle into GUIDED mode.
* Arm the vehicle remotely.
* Execute an autonomous takeoff sequence.
* Maintain controlled hover.
* Perform a safe autonomous landing sequence.

---

# 3. System Architecture

The system separates flight simulation from autonomous control logic through network-based communication.

```text
Python Flight Script
        │
        ▼
   MAVLink Protocol
        │
        ▼
    MAVProxy Router
        │
        ▼
  ArduPilot SITL Vehicle
        │
        ▼
 Simulation Environment
```

---

# 4. Network Layout

The communication framework utilizes local TCP sockets.

### Simulation Core

* ArduPilot SITL running ArduCopter firmware.
* Simulates vehicle dynamics and onboard flight controller behavior.

### Telemetry Routing

MAVProxy captures the primary telemetry stream:

```text
tcp:127.0.0.1:5760
```

and exposes a secondary developer endpoint:

```text
tcp:127.0.0.1:5762
```

used by external applications.

### Control Pipeline

```text
phase1_flight.py
       │
       ▼
tcp://127.0.0.1:5762
       │
       ▼
 MAVProxy
       │
       ▼
 ArduPilot SITL
```

---

# 5. Development Environment

## Operating System

* Ubuntu 22.04 LTS
* Ubuntu 24.04 LTS
* WSL2 (Windows Subsystem for Linux)

## Software Stack

* ArduPilot
* MAVProxy
* Python 3.12+
* pymavlink
* VS Code

---

# 6. Installation Procedure

## Clone ArduPilot

```bash
cd ~

git clone https://github.com/ArduPilot/ardupilot.git

cd ardupilot

git submodule update --init --recursive
```

## Install Dependencies

```bash
./Tools/environment_install/install-prereqs-ubuntu.sh -y

. ~/.profile
```

## Activate Virtual Environment

```bash
source ~/venv-ardupilot/bin/activate
```

## Install pymavlink

```bash
pip install pymavlink
```

---

# 7. Autonomous Flight Control Script

File:

```text
phase1_flight.py
```

Core functionalities implemented:

* TCP handshake establishment
* MAVLink heartbeat synchronization
* Pre-flight arming check override
* GUIDED mode activation
* Vehicle arming
* Autonomous takeoff
* Hover stabilization
* Autonomous landing

---

# 8. Flight Sequence Workflow

```text
Connect to Vehicle
        │
        ▼
Wait for Heartbeat
        │
        ▼
Disable Arming Checks
        │
        ▼
Switch to GUIDED Mode
        │
        ▼
Arm Vehicle
        │
        ▼
Takeoff to 10 m
        │
        ▼
Hover
        │
        ▼
LAND Command
        │
        ▼
Automatic Disarm
```

---

# 9. Engineering Challenges & Debugging

## Problem Identified

Running SITL under one Linux user namespace and executing Python scripts under another administrative namespace caused the following error:

```text
ConnectionRefusedError: [Errno 111]
```

The Python application could not access the MAVProxy TCP endpoint.

## Root Cause

Loopback interfaces became isolated due to inconsistent execution environments.

```text
root@DESKTOP
        ≠
priyanshu@DESKTOP
```

---

## Solution Implemented

A unified Python virtual environment was used.

```text
venv-ardupilot
```

All SITL and Python processes were executed within the same user context.

Result:

```text
Stable MAVLink communication established.
```

---

# 10. Validation Results

The following milestones were verified successfully.

| Capability            | Status |
| --------------------- | ------ |
| SITL Launch           | ✅      |
| Heartbeat Detection   | ✅      |
| GUIDED Mode Switching | ✅      |
| Vehicle Arming        | ✅      |
| Autonomous Takeoff    | ✅      |
| Hover Stabilization   | ✅      |
| Autonomous Landing    | ✅      |
| Automatic Disarming   | ✅      |

---

# 11. Execution Logs

Example output:

```text
Connecting to virtual UAV via TCP port 5762...

Connected! Heartbeat received.

Disabling pre-flight checks...

Switching to GUIDED mode...

Sending ARM command...

Executing automated takeoff to 10m...

Drone climbing...

Initiating landing sequence...

Sequence completed successfully.
```
---

# 12. Screenshots

## Figure 12.1 – Python Automation Log
![alt text](./screenshots/connection.png)

Description:

Terminal output confirming successful execution of the complete autonomous flight sequence.

---

## Figure 12.2 – SITL Telemetry Validation
![alt text](./screenshots/takeoff.png)

Description:

ArduPilot console showing:

* altitude acquisition,
* LAND mode transition,
* surface contact detection,
* automatic motor disarming.

---

# 13. Project Structure

```text
aerotronix_project/
│
├── phase1_flight.py
├── README.md
├── requirements.txt
├── screenshots/
│   ├── connection.png
│   ├── takeoff.png
│   └── landing.png
└── docs/
    └── Phase1_Week1_Report.pdf
```

---

# 14. Running the Project

## Terminal 1

```bash
cd ~/ardupilot/ArduCopter

sim_vehicle.py --console --map
```

Wait for SITL initialization and GPS lock.

---

## Terminal 2

```bash
cd ~/aerotronix_project

python3 phase1_flight.py
```

---

# 15. Phase 1 Deliverables

Successfully achieved:

* Autonomous telemetry acquisition.
* Direct MAVLink command transmission.
* Independent Python flight control.
* Full takeoff-hover-land cycle in SITL.

Phase 1 confirms readiness for mission-level autonomy development.

---

# 16. Future Roadmap

## Phase 2

* Waypoint navigation
* Mission upload support
* GPS path execution
* Telemetry logging
* Geofencing

## ports explanation
Our drones are broadcasting on 5760, 5770, and 5780. When you use sim_vehicle.py with the -I flag, it defaults to outputting MAVLink data on 14550 + (10 * instance_number).

Drone 1 (-I0): Outputting to 14550

Drone 2 (-I1): Outputting to 14560

Drone 3 (-I2): Outputting to 14570

Step 2: Configure Mission Planner Connections
Do not use port 14550 for all of them. Change your connection settings for each window as follows:

Window 1: Connect via UDP, set port to 14550.

Window 2: Connect via UDP, set port to 14560.

Window 3 (if open): Connect via UDP, set port to 14570.
UDP14550-1-QUADROTOR
``` bash 
cd ~/aerotronix_project

# Run each command in seperate terminal
sim_vehicle.py -v ArduCopter -I0 --console --out 127.0.0.1:14555

sim_vehicle.py -v ArduCopter -I1 --console --out 127.0.0.1:14565

sim_vehicle.py -v ArduCopter -I2 --console --out 127.0.0.1:14575 
 
``` bash
python swarm_move.py

## Phase 3

* Computer vision integration
* Obstacle avoidance
* Target tracking
* Hardware deployment on real UAV platforms

---

# 17. Conclusion

Phase 1 – Week 1 has been completed successfully.

The developed architecture demonstrates that an independent Python application can reliably communicate with an ArduPilot-based UAV through MAVLink and execute autonomous flight routines within a simulated environment.

This milestone establishes the foundational infrastructure necessary for advanced UAV autonomy research and future deployment on physical flight systems.

---

## Author

**Priyanshu**

Aerotronix India

UAV Autonomy & Flight Control Development
