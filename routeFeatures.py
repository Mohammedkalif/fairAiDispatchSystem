import json
from math import radians, sin, cos, sqrt, atan2
import os
import glob

datadir = "data/jsonFiles"

def loadData(filepath):
    with open(filepath) as f:
        return json.load(f)

# Haversine distance in meters
def haversine(p1, p2):
    R = 6371000 
    lon1, lat1 = p1
    lon2, lat2 = p2

    dlon = radians(lon2 - lon1)
    dlat = radians(lat2 - lat1)

    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return R * c

def extractFeatures(routeData):
    routes = routeData.get("routes", [])
    if not routes:
        return None

    total_duration = routeData.get("summary", {}).get("duration", 0)
    route = routes[0]

    steps = route.get("steps", [])
    coords = [s["location"] for s in steps]

    total_distance = sum(
        haversine(coords[i], coords[i + 1])
        for i in range(len(coords) - 1)
    )

    freeflow_duration = total_distance / 13.89 if total_distance else 0.0  # 50 km/h in m/s
    traffic_index = (total_duration / freeflow_duration) if freeflow_duration else 0.0

    job_stops = [s for s in steps if s.get("type") == "job"]
    num_stops = len(job_stops)

    stop_density = (num_stops / total_distance) if total_distance else 0.0
    parking_stress = stop_density * traffic_index

    return {
        "total_distance": total_distance,
        "total_duration": total_duration,
        "stops": num_stops,
        "stop_density": stop_density,
        "traffic_index": traffic_index,
        "parking_stress": parking_stress,
    }

def main():
    all_features = {}
    
    # Find all files matching the pattern
    pattern = os.path.join(datadir, "routes_Cluster *.json")
    cluster_files = glob.glob(pattern)
    
    for filepath in sorted(cluster_files):
        filename = os.path.basename(filepath)
        n = int(filename.split("Cluster ")[1].split(".json")[0])

        routeData = loadData(filepath)
        features = extractFeatures(routeData)
        if features is not None:
            all_features[f"Cluster {n}"] = features
    
    with open(f"{datadir}/route_features.json", "w") as f:
        json.dump(all_features, f, indent=4)

if __name__ == "__main__":
    main()
