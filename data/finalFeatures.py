import json
import re
from pathlib import Path

ROUTE_FEATURES_CANDIDATES = [
    "data/jsonFiles/route_features.json",
]
PACKAGE_FEATURES_CANDIDATES = [
    "data/jsonFiles/package_features.json",
    "data/jsonFiles/package_features_cluster.json",
]
OUTPUT_PATH = "data/jsonFiles/finalFeatures.json"


def open_json(path):
    with open(path, "r") as file:
        return json.load(file)


def first_existing_path(candidates):
    for candidate in candidates:
        if Path(candidate).exists():
            return candidate
    raise FileNotFoundError(f"None of these files exist: {candidates}")


def cluster_sort_key(cluster_name):
    match = re.search(r"\d+", cluster_name)
    return int(match.group()) if match else float("inf")


def build_final_features(route_features, package_features):
    final = {}
    clusters = sorted(
        set(route_features.keys()) | set(package_features.keys()),
        key=cluster_sort_key,
    )

    for cluster_name in clusters:
        route = route_features.get(cluster_name, {})
        package = package_features.get(cluster_name, {})

        stop_density = float(route.get("stop_density", 0.0))
        packages_per_stop = float(package.get("packages_per_stop", 0.0))

        final[cluster_name] = {
            "physical_load": {
                "total_weight": float(package.get("total_weight_kg", 0.0)),
                "heavy_pkg_ratio": float(package.get("heavy_pkg_ratio_gt10kg", 0.0)),
                "bulky_ratio": float(package.get("bulky_pkg_ratio_gt50000cm3", 0.0)),
            },
            "stair_load": {
                "stair_load_index": float(package.get("stair_load_index", 0.0)),
                "avg_floor": float(package.get("avg_floor", 0.0)),
                "elevator_coverage": float(package.get("elevator_coverage_ratio", 0.0)),
            },
            "traffic_stress": {
                "traffic_index": float(route.get("traffic_index", 0.0)),
                "parking_stress": float(route.get("parking_stress", 0.0)),
                "stop_density": stop_density,
            },
            "route_distance": {
                "total_distance": float(route.get("total_distance", 0.0)),
                "total_duration": float(route.get("total_duration", 0.0)),
            },
            "cognitive_density": packages_per_stop * stop_density,
        }

    return final


def main():
    route_path = first_existing_path(ROUTE_FEATURES_CANDIDATES)
    package_path = first_existing_path(PACKAGE_FEATURES_CANDIDATES)

    route_features = open_json(route_path)
    package_features = open_json(package_path)

    final_features = build_final_features(route_features, package_features)

    with open(OUTPUT_PATH, "w") as file:
        json.dump(final_features, file, indent=2)

    print(f"Final features written to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
