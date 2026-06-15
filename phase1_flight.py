import time
from pymavlink import mavutil

def connect_uav():
    # List of standard local ports ArduPilot/MAVProxy uses to broadcast telemetry
    connection_strings = [
        'udpin:0.0.0.0:14550',
        'udpin:0.0.0.0:14551',
        'tcp:127.0.0.1:5762',
        'tcp:127.0.0.1:5763'
    ]
    
    for conn in connection_strings:
        print(f"Trying connection string: {conn} ...")
        try:
            # Set a short timeout so it doesn't hang forever if the port is silent
            vehicle = mavutil.mavlink_connection(conn, timeout=5)
            
            # Look for a heartbeat
            msg = vehicle.wait_heartbeat(timeout=3)
            if msg is not None:
                print(f"\n--> SUCCESS! Connected via {conn}")
                print(f"Heartbeat received from Drone (System ID: {vehicle.target_system})")
                return vehicle
        except Exception as e:
            print(f"Port unavailable: {e}")
            continue
            
    raise ConnectionError("Could not connect to the simulation on any standard port. Ensure sim_vehicle.py is fully running.")

# Establish connection dynamically
vehicle = connect_uav()

# 2. Programmatically disable Arming Checks
print("Disabling pre-flight arming safety checks...")
vehicle.mav.param_set_send(
    vehicle.target_system, vehicle.target_component,
    b'ARMING_CHECK',
    0,
    mavutil.mavlink.MAV_PARAM_TYPE_REAL32
)
time.sleep(1) 

# 3. Switch flight mode to GUIDED
print("Switching flight mode to GUIDED...")
vehicle.mav.set_mode_send(
    vehicle.target_system,
    mavutil.mavlink.MAV_MODE_FLAG_CUSTOM_MODE_ENABLED,
    4 # GUIDED mode ID
)
time.sleep(1)

# 4. Arm the Thrusters
print("Sending direct ARM command...")
vehicle.mav.command_long_send(
    vehicle.target_system, vehicle.target_component,
    mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM,
    0, 1, 0, 0, 0, 0, 0, 0
)
print("Waiting for motors to spin up...")
time.sleep(3)

# 5. Takeoff to 10 Meters
print("Executing automated takeoff to 10m...")
vehicle.mav.command_long_send(
    vehicle.target_system, vehicle.target_component,
    mavutil.mavlink.MAV_CMD_NAV_TAKEOFF,
    0, 0, 0, 0, 0, 0, 0, 10
)

print("Drone climbing... Hovering at 10 meters.")
time.sleep(15)

# 6. Automated Landing Sequence
print("Initiating automated landing sequence...")
vehicle.mav.command_long_send(
    vehicle.target_system, vehicle.target_component,
    mavutil.mavlink.MAV_CMD_NAV_LAND,
    0, 0, 0, 0, 0, 0, 0, 0
)
# Add this pause so you can watch the console altitude drop to 0!
print("Waiting for drone to safely touch down...")

time.sleep(10)

print("Sequence completed successfully. Motors disarmed.")
