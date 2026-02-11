import json
from math import fsum

DATA_DIR = "data/jsonFiles"

def mean(values):
    return fsum(values) / len(values) if values else 0.0

def main():
    with open(f"{DATA_DIR}/clustered_stoppings.json", "r") as f:
        clustered = json.load(f)

    with open(f"{DATA_DIR}/stoppingandpackage.json", "r") as f:
        stops = json.load(f)

    stop_to_packages = {s["stop_id"]: s.get("packages", []) for s in stops}
    cluster_features = {}

    for cluster_name, cluster_stops in clustered.items():
        stop_ids = list(cluster_stops.keys())
        pkgs = [p for sid in stop_ids for p in stop_to_packages.get(sid, [])]

        n = len(pkgs)
        weights = [float(p.get("weight_kg", 0.0)) for p in pkgs]
        volumes = [
            float(p.get("height_cm", 0.0)) * float(p.get("length_cm", 0.0)) * float(p.get("breadth_cm", 0.0))
            for p in pkgs
        ]
        floors = [int(p.get("floor", 0)) for p in pkgs]
        no_elevator = [1 if not p.get("has_elevator", False) else 0 for p in pkgs]

        stair_load = sum(w * max(fl, 0) * ne for w, fl, ne in zip(weights, floors, no_elevator))

        cluster_features[cluster_name] = {
            "num_stops": len(stop_ids),
            "num_packages": n,
            "packages_per_stop": (n / len(stop_ids)) if stop_ids else 0.0,
            "total_weight_kg": sum(weights),
            "avg_weight_kg": mean(weights),
            "heavy_pkg_ratio_gt10kg": (sum(w > 10 for w in weights) / n) if n else 0.0,
            "total_volume_cm3": sum(volumes),
            "avg_volume_cm3": mean(volumes),
            "bulky_pkg_ratio_gt50000cm3": (sum(v > 50000 for v in volumes) / n) if n else 0.0,
            "avg_floor": mean(floors),
            "high_floor_ratio_ge3": (sum(fl >= 3 for fl in floors) / n) if n else 0.0,
            "elevator_coverage_ratio": 1.0 - ((sum(no_elevator) / n) if n else 0.0),
            "stair_load_index": stair_load,
        }

    with open(f"{DATA_DIR}/package_features_cluster.json", "w") as f:
        json.dump(cluster_features, f, indent=2)

if __name__ == "__main__":
    main()
