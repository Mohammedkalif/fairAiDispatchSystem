"""
main.py — project entry point
──────────────────────────────
1. Loads and preprocesses raw data files
2. Calls agents.supervisorGraph.run_dispatch()
3. Prints the final allocation, fairness report, critique, and explanation

Run:
    python main.py
"""

import json
import os
import sys

# ── Make sure project root is on the path so `agents` is importable ──────────
sys.path.insert(0, os.path.dirname(__file__))

from agents.supervisorGraph import run_dispatch


# ─── Data paths ───────────────────────────────────────────────────────────────

DATA_DIR        = os.path.join(os.path.dirname(__file__), "data", "jsonFiles")
EFFORT_VECTORS_PATH = os.path.join(DATA_DIR, "finalFeatures.json")
DRIVERS_PATH        = os.path.join(DATA_DIR, "driversdata.json")


# ─── Preprocessing helpers ────────────────────────────────────────────────────

def load_json(path: str) -> dict:
    with open(path, "r") as f:
        return json.load(f)


def validate_effort_vectors(vectors: dict) -> dict:
    """
    Basic sanity check on effort vectors:
      - Remove clusters with all-zero physical_load (empty routes)
      - Ensure required keys exist with defaults
    """
    cleaned = {}
    for cluster_id, vec in vectors.items():
        pl = vec.get("physical_load", {})
        if pl.get("total_weight", 0) == 0 and pl.get("heavy_pkg_ratio", 0) == 0:
            print(f"[Preprocess] Skipping empty cluster: {cluster_id}")
            continue
        # Ensure cognitive_density exists
        vec.setdefault("cognitive_density", 0.0)
        cleaned[cluster_id] = vec
    return cleaned


def validate_drivers(drivers: dict) -> dict:
    """
    Ensure every driver has the required keys with safe defaults.
    """
    required_ev = {
        "physical_load":  {"total_weight": 0, "heavy_pkg_ratio": 0, "bulky_ratio": 0},
        "stair_load":     {"stair_load_index": 0, "avg_floor": 0, "elevator_coverage": 0},
        "traffic_stress": {"traffic_index": 0, "parking_stress": 0, "stop_density": 0},
        "route_distance": {"total_distance": 0, "total_duration": 0},
        "cognitive_density": 0.0,
    }
    for name, data in drivers.items():
        data.setdefault("consecutive_heavy_days", 0)
        ev = data.setdefault("cumulative_effort_vector", {})
        for key, default in required_ev.items():
            ev.setdefault(key, default)
    return drivers


# ─── Entry point ──────────────────────────────────────────────────────────────

def main():
    print("═" * 60)
    print("Dispatch System — starting")
    print("═" * 60)

    # 1. Load raw data
    print("\n[main] Loading data...")
    effort_vectors = load_json(EFFORT_VECTORS_PATH)
    driver_data    = load_json(DRIVERS_PATH)
    print(f"[main] {len(effort_vectors)} clusters | {len(driver_data)} drivers")

    # 2. Preprocess
    print("\n[main] Preprocessing...")
    effort_vectors = validate_effort_vectors(effort_vectors)
    driver_data    = validate_drivers(driver_data)
    print(f"[main] After preprocessing: {len(effort_vectors)} clusters")

    # ── Add your own preprocessing steps here ─────────────────────────────
    # e.g. merge route features, recompute stair indices, etc.
    # ──────────────────────────────────────────────────────────────────────

    # 3. Run dispatch agent
    print("\n[main] Handing off to supervisor graph...")
    result = run_dispatch(effort_vectors, driver_data)

    # 4. Output
    print("\n" + "═" * 60)
    print("FINAL ALLOCATION")
    print("═" * 60)
    print(json.dumps(result["allocation"], indent=2))

    print("\n" + "═" * 60)
    print("FAIRNESS REPORT")
    print("═" * 60)
    print(json.dumps(result["fairness_report"], indent=2))

    print("\n" + "═" * 60)
    print("CRITIQUE")
    print("═" * 60)
    print(json.dumps(result["critique"], indent=2))

    print("\n" + "═" * 60)
    print("EXPLANATION")
    print("═" * 60)
    print(result["explanation"])


if __name__ == "__main__":
    main()