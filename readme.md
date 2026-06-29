Here is the complete, cleanly formatted `README.md` file. I have restored all the code blocks, tables, and spacing that got flattened so you can copy and paste this directly into your GitHub repository!

```markdown
# 🚁 Project Title: Autonomous Telemetry, Multi-Node Swarm Control & Control Streams

### Developer Name: Priyanshu
### Status: Phase 1 – Week 2 Milestone Achieved Successfully
### Affiliation: Aerotronix India (UAV Autonomy & Flight Control Development)

---

# 1. Executive Summary
This project focuses on developing an autonomous UAV control framework using the MAVLink communication protocol, DroneKit, and ArduPilot's Software-In-The-Loop (SITL) simulation environment.

* **Week 1 Milestone:** Successfully established reliable telemetry and command communication between an independent Python application and a single simulated quadcopter node. Demonstrated automated mode switching, vehicle arming, autonomous takeoff, hover, and landing without manual pilot intervention.
* **Week 2 Milestone:** Upgraded the system architecture to a parallelized multi-node control pipeline. The final implementation handles three independent copter instances executing synchronized routines (Takeoff, Geographic Coordinate Translation, Starburst Formation Flight, and Return-To-Launch) concurrently, utilizing multi-threading paradigms to bypass local network bottlenecks.

---

# 2. Technical Objectives

### Phase 1 – Week 1
* Establish a functional ArduPilot SITL environment under Ubuntu.
* Create a primary MAVLink communication bridge using `pymavlink`.
* Programmatically bypass development-stage pre-arm checks.
* Execute a single-vehicle autonomous takeoff, controlled hover, and landing sequence.

### Phase 1 – Week 2
* Initialize multiple simultaneous ArduPilot SITL vehicle nodes (`-I0`, `-I1`, `-I2`) using custom geographic coordinates (`-L`) to eliminate airspace hazard warnings.
* Configure unique identification parameters (`SYSID_THISMAV`) across nodes to avoid packet collisions.
* Route data pipelines through designated secondary endpoints (`14555`, `14565`, `14575`) to avoid port lockouts.
* Develop a math-based translation algorithm within a custom directional method (`chooseDirection`) supporting explicit compass vector tracking (North, South, East, West).
* Override local firmware safety clamps (`WPNAV_SPEED_MAX`) to achieve high-speed operation (20 m/s).
* Build a single-instance multiplexed telemetry view in Mission Planner via multi-UDP bridging.

---

# 3. System Architecture

The workflow isolates each virtual drone vehicle instance into its own parallel operational pipeline while routing execution back to a single master controller script.

```text
                  ┌──────────────────────────────┐
                  │       swarm_move.py          │
                  │ (Parallel Thread Execution)  │
                  └──────┬────────┬────────┬─────┘
                         │        │        │
         ┌───────────────┘        │        └───────────────┐
         ▼                        ▼                        ▼
   Thread-1 (I0)            Thread-2 (I1)            Thread-3 (I2)
         │                        │                        │
         ▼                        ▼                        ▼
 MAVLink (Port 14555)     MAVLink (Port 14565)     MAVLink (Port 14575)
         │                        │                        │
         ▼                        ▼                        ▼
 MAVProxy Router 0        MAVProxy Router 1        MAVProxy Router 2
         │                        │                        │
         ▼                        ▼                        ▼
  Drone Node 1             Drone Node 2             Drone Node 3

```

---

# 4. Network Layout & Telemetry Matrix

To prevent socket clashing, each drone processes separate output streams: one dedicated to the unified Ground Control Station and one dedicated to the automation script threads.

### Simulation Core Network (Week 1 Legacy)

MAVProxy captures the primary single-vehicle telemetry stream at `tcp:127.0.0.1:5760` and exposes a secondary developer endpoint at `tcp:127.0.0.1:5762`.

### Swarm Framework Port Allocation (Week 2 Production)

| Vehicle Node | SITL Instance ID | Global GCS Link Port | Script Thread Endpoint | System ID | Target Mission Mapping |
| --- | --- | --- | --- | --- | --- |
| **Drone 1** | `-I0` | `127.0.0.1:14550` | `127.0.0.1:14555` | `SYSID_THISMAV 1` | 200m North Vector Flight |
| **Drone 2** | `-I1` | `127.0.0.1:14560` | `127.0.0.1:14565` | `SYSID_THISMAV 2` | 200m East Vector Flight |
| **Drone 3** | `-I2` | `127.0.0.1:14570` | `127.0.0.1:14575` | `SYSID_THISMAV 3` | 200m West Vector Flight |

---

# 5. Development Environment & Library Patching

### Software Stack

* Ubuntu 22.04 / 24.04 LTS on Windows Subsystem for Linux (WSL2)
* ArduPilot Copter-4.5+ Firmware Core
* MAVProxy Router Engine
* Python 3.12+ Execution Environment
* DroneKit & PyMavlink Library Collections

### Python 3.12 Compatibility Patch

Because Python 3.12 completely deprecated legacy alias paths in the base `collections` module, standard legacy `dronekit` initializations throw an `AttributeError`. The following monkey-patch is injected directly at the top of the automation scripts to preserve runtime compatibility:

```python
import collections
import collections.abc
collections.MutableMapping = collections.abc.MutableMapping

```

---

# 6. Installation Procedure

### Clone ArduPilot

```bash
cd ~
git clone [https://github.com/ArduPilot/ardupilot.git](https://github.com/ArduPilot/ardupilot.git)
cd ardupilot
git submodule update --init --recursive

```

### Install Dependencies

```bash
./Tools/environment_install/install-prereqs-ubuntu.sh -y
. ~/.profile

```

### Activate Virtual Environment & Requirements

```bash
source ~/venv-ardupilot/bin/activate
pip install pymavlink dronekit

```

---

# 7. Implementation Scripts

### File 1: Single Vehicle Baseline (`phase1_flight.py`)

Provides single handshake initialization, telemetry acquisitions, and direct takeoff-land verification logic.

### File 2: Multi-Node Swarm Controller (`swarm_move.py`)

```python
import collections
import collections.abc
collections.MutableMapping = collections.abc.MutableMapping

import threading
from dronekit import connect, VehicleMode, LocationGlobalRelative
import time
import math

connections = ['127.0.0.1:14555', '127.0.0.1:14565', '127.0.0.1:14575']
vehicles = {}

print("--- Initializing Drone Connections Safely ---")
for conn in connections:
    try:
        print(f"Connecting to {conn}...")
        vehicle = connect(conn, wait_ready=False)
        vehicles[conn] = vehicle
        time.sleep(1.5)
    except Exception as e:
        print(f"Failed to connect to {conn}: {e}")

def chooseDirection(vehicle, conn, direction, distance, height, speed):
    try:
        print(f"[{conn}]: Taking off to {height}m...")
        vehicle.simple_takeoff(height)
        
        while True:
            alt = vehicle.location.global_relative_frame.alt
            if alt >= height * 0.90:
                print(f"[{conn}]: Target altitude reached.")
                break
            time.sleep(0.5)
            
        print(f"[{conn}]: Configuring flight dynamics to {speed} m/s...")
        speed_cms = speed * 100
        try:
            vehicle.parameters['WPNAV_SPEED_MAX'] = speed_cms
            vehicle.parameters['WPNAV_SPEED'] = speed_cms
            vehicle.groundspeed = speed
        except Exception:
            pass

        lat_deg_per_meter = 1.0 / 111000.0
        current_lat = vehicle.location.global_frame.lat
        lon_deg_per_meter = 1.0 / (111111.0 * math.cos(math.radians(current_lat)))

        lat_offset, lon_offset = 0, 0
        direction = direction.upper().strip()
        
        if direction == "NORTH": lat_offset = distance * lat_deg_per_meter
        elif direction == "SOUTH": lat_offset = -distance * lat_deg_per_meter
        elif direction == "EAST": lon_offset = distance * lon_deg_per_meter
        elif direction == "WEST": lon_offset = -distance * lon_deg_per_meter

        target_loc = LocationGlobalRelative(
            vehicle.location.global_frame.lat + lat_offset,
            vehicle.location.global_frame.lon + lon_offset, 
            height
        )

        print(f"[{conn}]: Moving {distance}m {direction}...")
        vehicle.simple_goto(target_loc)
        
        time.sleep((distance / speed) + 5)
        
        print(f"[{conn}]: Returning to Launch...")
        vehicle.mode = VehicleMode("RTL")
        
    except Exception as e:
        print(f"Error on {conn}: {e}")

print("\n--- Initiating Synchronized Swarm Launch ---")
flight_threads = []
directions = {
    '127.0.0.1:14555': ("NORTH", 200, 30, 20),
    '127.0.0.1:14565': ("EAST", 200, 30, 20),
    '127.0.0.1:14575': ("WEST", 200, 30, 20)
}

for conn, vehicle in vehicles.items():
    dir_name, dist, alt, spd = directions[conn]
    t = threading.Thread(target=chooseDirection, args=(conn, vehicle, dir_name, dist, alt, spd))
    flight_threads.append(t)

for t in flight_threads: t.start()
for t in flight_threads: t.join()

for conn, vehicle in vehicles.items(): vehicle.close()
print("\nSwarm mission successfully completed!")

```

---

# 8. Engineering Challenges & Debugging Logs

### Challenge 1: `ConnectionRefusedError: [Errno 111]` (Week 1)

* **Root Cause:** Running SITL simulation and control scripts under mismatched administrative namespaces isolated local host loopbacks.
* **Solution:** Standardized processes inside a unified Python virtual environment (`venv-ardupilot`) executed entirely within a single user space.

### Challenge 2: Connection Initialization Bottlenecks & Timeouts (Week 2)

* **Root Cause:** Launching `connect(..., wait_ready=True)` concurrently across parallel threads caused the drone nodes to query their entire parameter maps (1,300+ entries) simultaneously, flooding the loopback interface and throwing connection errors.
* **Solution:** Switched the setup to initialize with `wait_ready=False` and applied a minor connection delay loop in the primary setup thread to connect cleanly before launching flight tasks.

### Challenge 3: Firmware Velocity Safety Caps

* **Root Cause:** Requests to alter `groundspeed` beyond 10 m/s were rejected silently by the firmware's standard safety parameter boundaries.
* **Solution:** Added explicit parameter updates override targeting `WPNAV_SPEED_MAX` during runtime execution, enabling safe sprint tasks at 20 m/s.

---

# 9. Validation Matrix

| Milestone Metric | Target Verification Objective | Status |
| --- | --- | --- |
| **SITL Environment Initialization** | Multi-node indexing capability (`-I0`, `-I1`, `-I2`) | ✅ |
| **Heartbeat Synchronization** | Continuous MAVLink heartbeat handshake detection | ✅ |
| **Simultaneous Mode Shifting** | Parallel transitions into `GUIDED` flight state | ✅ |
| **Synchronized Motor Arming** | Concurrent motor activation logs across threads | ✅ |
| **Parallel Unison Takeoff** | Balanced, staggered-free altitude gain to 30 meters | ✅ |
| **Dynamic Parameter Overrides** | Velocity scaling up to 20 m/s (`WPNAV_SPEED_MAX`) | ✅ |
| **Starburst Vector Splits** | Geometric trajectory isolation (North / East / West) | ✅ |
| **Unified GCS Multiplexing** | 3 independent vehicle streams tracking on a single map | ✅ |

---

# 10. Repository Structure

```text
aerotronix_project/
│
├── swarm_move.py             # Multi-Threaded Multi-Node Swarm Controller (Week 2)
├── phase1_flight.py          # Legacy Single-Vehicle Control Script (Week 1)
├── README.md                 # Project Master Documentation Ledger
├── requirements.txt          # Python Environmental Dependencies
│
├── screenshots/
│   ├── connection.png        # Week 1 Telemetry Check Output
│   ├── multiplex_gcs.png     # Single Mission Planner multi-drone display panel
│   └── starburst_pattern.png # Map tracking vectors illustrating swarm separation
│
└── docs/
    ├── Phase1_Week1_Report.pdf
    └── Phase1_Week2_Report.pdf

```

---

# 11. Execution Blueprint

### Step 1: Initialize the Independent Simulation Nodes

Execute each command string inside its own individual terminal window to spin up the pre-separated drone cluster:

```bash
# Drone 1 Node
sim_vehicle.py -v ArduCopter -I0 --console --out 127.0.0.1:14555 -L 17.4483,78.3741,500,0

# Drone 2 Node
sim_vehicle.py -v ArduCopter -I1 --console --out 127.0.0.1:14565 -L 17.4485,78.3743,500,0

# Drone 3 Node
sim_vehicle.py -v ArduCopter -I2 --console --out 127.0.0.1:14575 -L 17.4487,78.3745,500,0

```

*Note: Run `param set SYSID_THISMAV [1/2/3]` inside their respective terminal command lines once to save unique identities.*

### Step 2: Configure the Unified Ground Control Display

1. Start one individual instance of Mission Planner.
2. Press **`Ctrl + F`** to display the advanced operations layout screen.
3. Select **MAVLink** in the sidebar.
4. Click **Add Port**, choose **UDP**, and enter ports `14550`, `14560`, and `14570` respectively.
5. All 3 vehicles will populate on the primary flight tracker map.

### Step 3: Run the Autonomous Mission Script

Open an isolated command prompt shell and run:

```bash
cd ~/aerotronix_project
source ~/venv-ardupilot/bin/activate
python swarm_move.py

```

---

# 12. Future Roadmap

* **Phase 2 (Dynamic Missions):** Implementation of dynamic runtime waypoint uploads, custom geographic pattern generation, perimeter geofencing, and internal collision prevention metrics.
* **Phase 3 (Hardware Integration):** Edge-computing deployment protocols using companion microcomputers (Raspberry Pi/Jetson architectures) interfacing with physical Pixhawk flight systems.

```

```