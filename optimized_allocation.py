import numpy as np
import time

HEAVY_PERCENTILE = 0.75

DECAY_FACTORS = {
    "physical_load": 0.85,
    "stair_load": 0.85,
    "traffic_stress": 0.95,
    "route_distance": 0.92,
    "cognitive_density": 0.90
}

DIMENSIONS = [
    "physical_load",
    "stair_load",
    "traffic_stress",
    "route_distance",
    "cognitive_density"
]

DIM_WEIGHTS = {
    "physical_load": 1.5,
    "stair_load": 1.3,
    "traffic_stress": 1.0,
    "route_distance": 1.2, 
    "cognitive_density": 0.8
}

# -----------------------------
# Flattening
# -----------------------------
def flatten_effort_vector(vector):
    flat = []

    pl = vector.get("physical_load", {})
    flat.extend([pl.get("total_weight", 0), pl.get("heavy_pkg_ratio", 0), pl.get("bulky_ratio", 0)])

    sl = vector.get("stair_load", {})
    flat.extend([sl.get("stair_load_index", 0), sl.get("avg_floor", 0), sl.get("elevator_coverage", 0)])

    ts = vector.get("traffic_stress", {})
    flat.extend([ts.get("traffic_index", 0), ts.get("parking_stress", 0), ts.get("stop_density", 0)])

    rd = vector.get("route_distance", {})
    flat.extend([rd.get("total_distance", 0), rd.get("total_duration", 0)])

    flat.append(vector.get("cognitive_density", 0))

    return np.array(flat, dtype=float)


def get_feature_meta():
    indices = {
        "physical_load": [0, 1, 2],
        "stair_load": [3, 4, 5],
        "traffic_stress": [6, 7, 8],
        "route_distance": [9, 10],
        "cognitive_density": [11]
    }

    decay = np.zeros(12)
    weights = np.zeros(12)

    for dim, idxs in indices.items():
        for i in idxs:
            decay[i] = DECAY_FACTORS.get(dim, 0.9)
            weights[i] = DIM_WEIGHTS.get(dim, 1.0)

    return indices, decay, weights


# -----------------------------
# Core Optimized Algorithm
# -----------------------------
def allocateDrivers_optimized(effortVectors, driverData, driver_locations=None, cluster_locations=None):
    start_time = time.time()

    driver_names = list(driverData.keys())
    cluster_names = list(effortVectors.keys())

    indices_map, decay_arr, dim_weights_arr = get_feature_meta()

    # Flatten
    driver_efforts = np.array([
        flatten_effort_vector(d["cumulative_effort_vector"])
        for d in driverData.values()
    ]) * decay_arr

    cluster_vectors = np.array([
        flatten_effort_vector(v)
        for v in effortVectors.values()
    ])

    consecutive_heavy = np.array([
        d.get("consecutive_heavy_days", 0)
        for d in driverData.values()
    ])

    # Normalization
    bounds_min = np.min(cluster_vectors, axis=0)
    bounds_max = np.max(cluster_vectors, axis=0)
    bounds_range = bounds_max - bounds_min
    bounds_range[bounds_range == 0] = 1.0

    def normalize(x):
        return (x - bounds_min) / bounds_range

    # Heavy cluster detection
    physical_weights = cluster_vectors[:, 0]
    durations = cluster_vectors[:, 10]

    physical_threshold = np.percentile(physical_weights, HEAVY_PERCENTILE * 100)
    duration_threshold = np.percentile(durations, HEAVY_PERCENTILE * 100)

    is_heavy_cluster = (physical_weights >= physical_threshold) | (durations >= duration_threshold)

    # Weighted magnitude (FIXED)
    def compute_weighted_magnitude(vectors):
        normed = normalize(vectors)
        mags = []

        for dim, idxs in indices_map.items():
            dim_val = np.mean(normed[:, idxs], axis=1)
            mags.append(DIM_WEIGHTS[dim] * dim_val)

        return np.sum(np.array(mags), axis=0)

    cluster_mags = compute_weighted_magnitude(cluster_vectors)
    sorted_indices = np.argsort(cluster_mags)[::-1]

    # Spatial cost (NEW)
    def spatial_penalty(d_idx, c_idx):
        if driver_locations is None or cluster_locations is None:
            return 0
        d = np.array(driver_locations[d_idx])
        c = np.array(cluster_locations[c_idx])
        return np.linalg.norm(d - c) * 0.05

    # Fast penalty computation
    def calculate_penalty(efforts, consecutive_heavy):
        normed = normalize(efforts)

        dim_variances = 0
        driver_totals = []

        for dim, idxs in indices_map.items():
            vals = np.mean(normed[:, idxs], axis=1)
            dim_variances += DIM_WEIGHTS[dim] * np.var(vals)
            driver_totals.append(vals)

        driver_totals = np.mean(np.array(driver_totals), axis=0)

        imbalance = np.var(driver_totals)

        fatigue = np.sum(consecutive_heavy >= 3) * 0.5

        return dim_variances + 1.5 * imbalance + fatigue

    assignments = {}

    # Multi-start (NEW improvement)
    best_global = None
    best_score = float("inf")

    for _ in range(3):  # small beam search
        local_efforts = driver_efforts.copy()
        local_consecutive = consecutive_heavy.copy()
        local_assign = {}

        for idx in sorted_indices:
            cluster_vec = cluster_vectors[idx]
            is_heavy = is_heavy_cluster[idx]

            best_driver = -1
            best_penalty = float("inf")

            for d_idx in range(len(driver_names)):
                if is_heavy and local_consecutive[d_idx] >= 2:
                    continue

                local_efforts[d_idx] += cluster_vec

                penalty = calculate_penalty(local_efforts, local_consecutive)
                penalty += spatial_penalty(d_idx, idx)

                if local_consecutive[d_idx] >= 2:
                    penalty += 0.3

                if penalty < best_penalty:
                    best_penalty = penalty
                    best_driver = d_idx

                local_efforts[d_idx] -= cluster_vec

            if best_driver != -1:
                local_efforts[best_driver] += cluster_vec

                if is_heavy:
                    local_consecutive[best_driver] += 1
                else:
                    local_consecutive[best_driver] = 0

                local_assign[cluster_names[idx]] = driver_names[best_driver]

        final_penalty = calculate_penalty(local_efforts, local_consecutive)

        if final_penalty < best_score:
            best_score = final_penalty
            best_global = local_assign

    # Update driver data
    for i, name in enumerate(driver_names):
        vec = driver_efforts[i]

        driverData[name]["cumulative_effort_vector"] = {
            "physical_load": {"total_weight": vec[0], "heavy_pkg_ratio": vec[1], "bulky_ratio": vec[2]},
            "stair_load": {"stair_load_index": vec[3], "avg_floor": vec[4], "elevator_coverage": vec[5]},
            "traffic_stress": {"traffic_index": vec[6], "parking_stress": vec[7], "stop_density": vec[8]},
            "route_distance": {"total_distance": vec[9], "total_duration": vec[10]},
            "cognitive_density": vec[11]
        }

        driverData[name]["consecutive_heavy_days"] = int(consecutive_heavy[i])

    print(f"Optimized Allocation Complete. Time: {time.time() - start_time:.4f}s")

    return best_global
