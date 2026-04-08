import json
import random
import os
import math

try:
    from sklearn.cluster import KMeans
    import numpy as np
except ImportError:
    print("scikit-learn is required. Please install it using: pip install scikit-learn")
    exit(1)

# Configuration
NUM_STOPS = 300
NUM_DRIVERS = 50
NUM_CLUSTERS = 10

# Geographic Base (Salem approx)
BASE_LNG = 78.16
BASE_LAT = 11.68
RANGE_LNG = 0.08  # Approx 8km spread
RANGE_LAT = 0.08

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "jsonFiles")
os.makedirs(OUTPUT_DIR, exist_ok=True)

def generate_stoppings():
    stoppings = []
    # Create clusters naturally by defining some "hotspots"
    hotspots = [
        (BASE_LNG + random.uniform(-RANGE_LNG/2, RANGE_LNG/2), 
         BASE_LAT + random.uniform(-RANGE_LAT/2, RANGE_LAT/2))
        for _ in range(NUM_CLUSTERS)
    ]
    
    for _ in range(NUM_STOPS):
        # Pick a random hotspot
        hx, hy = random.choice(hotspots)
        # Add some Gaussian noise around the hotspot
        lng = np.random.normal(hx, RANGE_LNG / 10)
        lat = np.random.normal(hy, RANGE_LAT / 10)
        stoppings.append([lng, lat])
        
    return stoppings

def generate_drivers():
    drivers = {}
    for i in range(1, NUM_DRIVERS + 1):
        driver_id = f"D{i}"
        
        # Simulate varying driver capacities/histories
        total_weight_3d = random.uniform(50.0, 350.0)
        heavy_pkg_ratio_3d = random.uniform(0.05, 0.50)
        bulky_ratio_3d = random.uniform(0.05, 0.40)
        
        stair_load_idx_3d = random.uniform(10.0, 100.0)
        avg_floor_3d = random.uniform(1.0, 10.0)
        elevator_cov_3d = random.uniform(0.1, 0.95)
        
        traffic_idx_3d = random.uniform(1.0, 6.0)
        park_stress_3d = random.uniform(0.002, 0.08)
        stop_dens_3d = random.uniform(0.001, 0.02)
        
        dist_3d = random.uniform(1500.0, 15000.0)
        dur_3d = random.uniform(300.0, 720.0)
        
        # Cumulative is roughly proportional but with some lifetime variation
        drivers[driver_id] = {
            "cumulative_effort_vector": {
                "physical_load": {
                    "total_weight": total_weight_3d * random.uniform(0.8, 1.2),
                    "heavy_pkg_ratio": heavy_pkg_ratio_3d * random.uniform(0.8, 1.2),
                    "bulky_ratio": bulky_ratio_3d * random.uniform(0.8, 1.2)
                },
                "stair_load": {
                    "stair_load_index": stair_load_idx_3d * random.uniform(0.8, 1.2),
                    "avg_floor": avg_floor_3d * random.uniform(0.8, 1.2),
                    "elevator_coverage": elevator_cov_3d * random.uniform(0.8, 1.2)
                },
                "traffic_stress": {
                    "traffic_index": traffic_idx_3d * random.uniform(0.8, 1.2),
                    "parking_stress": park_stress_3d * random.uniform(0.8, 1.2),
                    "stop_density": stop_dens_3d * random.uniform(0.8, 1.2)
                },
                "route_distance": {
                    "total_distance": dist_3d * random.uniform(0.8, 1.2),
                    "total_duration": dur_3d * random.uniform(0.8, 1.2)
                },
                "cognitive_density": random.uniform(0.002, 0.02)
            },
            "last_3_days_vector": {
                "physical_load": {
                    "total_weight": total_weight_3d,
                    "heavy_pkg_ratio": heavy_pkg_ratio_3d,
                    "bulky_ratio": bulky_ratio_3d
                },
                "stair_load": {
                    "stair_load_index": stair_load_idx_3d,
                    "avg_floor": avg_floor_3d,
                    "elevator_coverage": elevator_cov_3d
                },
                "traffic_stress": {
                    "traffic_index": traffic_idx_3d,
                    "parking_stress": park_stress_3d,
                    "stop_density": stop_dens_3d
                },
                "route_distance": {
                    "total_distance": dist_3d,
                    "total_duration": dur_3d
                },
                "cognitive_density": random.uniform(0.002, 0.02)
            },
            "consecutive_heavy_days": random.randint(0, 10) # Includes extreme bounds over the past 3 days/historical
        }
    return drivers

def generate_packages_and_stops(stoppings):
    stopping_and_package = []
    stop_ids = []
    
    for i, loc in enumerate(stoppings):
        stop_id = f"STOP_{str(i+1).zfill(3)}"
        stop_ids.append(stop_id)
        
        num_packages = random.randint(1, 10) # 1 to 10 packages
        packages = []
        for j in range(num_packages):
            floor = random.choice([0, 1, 2, 3, 4, 5, 8, 10, 15, 20, 25])
            has_elevator = random.choice([True, False])
            # If floor > 5, increased chance of elevator true, but not guaranteed
            if floor > 5 and random.random() > 0.2:
                has_elevator = True
                
            pkg = {
                "package_id": f"PKG_{stop_id}_{chr(65+j) if j < 26 else str(j)}",
                "floor": floor,
                "height_cm": random.randint(5, 100),
                "length_cm": random.randint(10, 100),
                "breadth_cm": random.randint(5, 80),
                "weight_kg": round(random.uniform(0.5, 40.0), 2),
                "has_elevator": has_elevator
            }
            packages.append(pkg)
            
        stopping_and_package.append({
            "stop_id": stop_id,
            "location": loc,
            "packages": packages
        })
        
    return stopping_and_package, stop_ids

def generate_clusters(stoppings, stop_ids):
    # Convert to standard list if it's not
    coords = np.array(stoppings)
    kmeans = KMeans(n_clusters=NUM_CLUSTERS, random_state=42, n_init="auto")
    labels = kmeans.fit_predict(coords)
    
    clustered = {f"Cluster {i}": {} for i in range(NUM_CLUSTERS)}
    
    for i, (loc, label) in enumerate(zip(stoppings, labels)):
        stop_id = stop_ids[i]
        clustered[f"Cluster {label}"][stop_id] = loc
        
    return clustered

if __name__ == "__main__":
    print("Generating complex synthetic data...")
    stoppings = generate_stoppings()
    drivers = generate_drivers()
    stopping_and_package, stop_ids = generate_packages_and_stops(stoppings)
    clustered = generate_clusters(stoppings, stop_ids)
    
    # Save files
    with open(os.path.join(OUTPUT_DIR, "stoppings.json"), "w") as f:
        json.dump(stoppings, f, indent=4)
        
    with open(os.path.join(OUTPUT_DIR, "driversdata.json"), "w") as f:
        json.dump(drivers, f, indent=4)
        
    with open(os.path.join(OUTPUT_DIR, "stoppingandpackage.json"), "w") as f:
        json.dump(stopping_and_package, f, indent=4)
        
    with open(os.path.join(OUTPUT_DIR, "clustered_stoppings.json"), "w") as f:
        json.dump(clustered, f, indent=4)
        
    print(f"Generated {NUM_STOPS} stops, {NUM_DRIVERS} drivers, and {NUM_CLUSTERS} clusters.")
    print(f"Files saved in {OUTPUT_DIR}")
