import threading
from dronekit import connect, VehicleMode, LocationGlobalRelative
import time
import math

# Target ports
connections = ['127.0.0.1:14555', '127.0.0.1:14565', '127.0.0.1:14575']
vehicles = {}

# --- STEP 1: SAFE SEQUENTIAL CONNECTION ---
print("--- Initializing Drone Connections Safely ---")
for conn in connections:
    try:
        print(f"Connecting to {conn}...")
        # wait_ready=False prevents downloading all 1300 parameters at once, stopping the crash
        vehicle = connect(conn, wait_ready=False)
        vehicles[conn] = vehicle
        time.sleep(1.5) # Give it a moment before connecting the next one
    except Exception as e:
        print(f"Failed to connect to {conn}: {e}")

# --- STEP 2: INDEPENDENT FLIGHT TASKS ---
def execute_flight(conn, vehicle, direction, distance, height, speed):
    try:
        # Wait until the vehicle is fully ready to accept arm commands
        while not vehicle.is_armable:
            print(f"[{conn}] Waiting for GPS lock / initialization...")
            time.sleep(1)
            
        print(f"[{conn}] Arming and setting to GUIDED mode...")
        vehicle.mode = VehicleMode("GUIDED")
        vehicle.armed = True
        while not vehicle.armed:
            time.sleep(0.2)
            
        print(f"[{conn}] Launching! Climbing to {height}m...")
        vehicle.simple_takeoff(height)
        
        # Monitor altitude climb safely
        while True:
            alt = vehicle.location.global_relative_frame.alt
            if alt >= height * 0.90:
                break
            time.sleep(0.5)
            
        print(f"[{conn}] Target altitude reached. Configuring flight dynamics...")
        
        # Set speed parameters cleanly with fallback protection
        speed_cms = speed * 100
        try:
            vehicle.parameters['WPNAV_SPEED_MAX'] = speed_cms
            vehicle.parameters['WPNAV_SPEED'] = speed_cms
            vehicle.groundspeed = speed
        except Exception:
            pass # Skip parameter blocks if MAVLink queue is temporarily busy

        # Coordinate calculations
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

        print(f"[{conn}] Accelerating {distance}m {direction} at {speed}m/s...")
        vehicle.simple_goto(target_loc)
        
        # Calculate dynamic hold time
        time.sleep((distance / speed) + 5)
        
        print(f"[{conn}] Action finished. Triggering RTL...")
        vehicle.mode = VehicleMode("RTL")
        
    except Exception as e:
        print(f"Error executing flight on {conn}: {e}")

# --- STEP 3: SIMULTANEOUS SWARM LAUNCH ---
print("\n--- All Drones Linked. Initiating Synchronized Swarm Launch Now ---")
flight_threads = []

# Map your specific project direction requirements here
directions = {
    '127.0.0.1:14555': ("NORTH", 200, 30, 5),
    '127.0.0.1:14565': ("NORTH", 200, 30, 5),
    '127.0.0.1:14575': ("NORTH", 200, 30, 5)
}

for conn, vehicle in vehicles.items():
    dir_name, dist, alt, spd = directions[conn]
    t = threading.Thread(target=execute_flight, args=(conn, vehicle, dir_name, dist, alt, spd))
    flight_threads.append(t)

# Fire all flight paths at the exact same millisecond
for t in flight_threads: 
    t.start()

# Hold main script until all tasks finish
for t in flight_threads: 
    t.join()

# Clean disconnect
for conn, vehicle in vehicles.items():
    vehicle.close()

print("\nSwarm mission successfully completed!")