import json
from math import radians, sin, cos, sqrt, atan2

datadir = "data/jsonFiles"

def loadData(datadir, n):
    with open(f"{datadir}/routes_Cluster {n}.json") as f:
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
    features = {}

    total_duration = routeData["summary"]["duration"]

    for route in routeData["routes"]:
        route_id = route["vehicle"]

        steps = route["steps"]
        coords = [s["location"] for s in steps]

        total_distance = sum(
            haversine(coords[i], coords[i + 1])
            for i in range(len(coords) - 1)
        )

        freeflow_duration = total_distance / 13.89  # 50 km/h in m/s
        traffic_index = total_duration / freeflow_duration

        job_stops = [s for s in steps if s["type"] == "job"]
        num_stops = len(job_stops)

        stop_density = num_stops / total_distance
        parking_difficulty = stop_density * traffic_index

        features[route_id] = {
            "total_distance": total_distance,
            "total_duration": total_duration,
            "stops": num_stops,
            "stop_density": stop_density,
            "traffic_index": traffic_index,
            "parking_difficulty": parking_difficulty
        }

    return features

def main():
    all_features = {}

    for n in range(0, 3):
        routeData = loadData(datadir, n)
        features = extractFeatures(routeData)
        all_features.update(features)

    with open(f"{datadir}/route_features.json", "w") as f:
        json.dump(all_features, f, indent=4)

if __name__ == "__main__":
    main()
