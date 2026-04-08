import json
import copy
import math

HEAVY_PERCENTILE = 0.75

DECAY_FACTORS = {
    "physical_load": 0.85,
    "stair_load": 0.85,
    "traffic_stress": 0.95,
    "route_distance": 0.92,
    "cognitive_density": 0.90
}


def openJson(filePath):
    with open(filePath, "r") as file:
        return json.load(file)



def applyDecay(driverData):
    for driver in driverData.values():
        for dim, value in driver["cumulative_effort_vector"].items():

            decay = DECAY_FACTORS.get(dim, 0.9)

            if isinstance(value, dict):
                for feature in value:
                    driver["cumulative_effort_vector"][dim][feature] *= decay
            else:
                driver["cumulative_effort_vector"][dim] *= decay



def compute_static_feature_bounds(effortVectors):

    bounds = {}

    for vec in effortVectors.values():
        for dim, value in vec.items():

            if isinstance(value, dict):
                for feature, val in value.items():
                    key = (dim, feature)
                    bounds.setdefault(key, []).append(val)
            else:
                key = (dim, None)
                bounds.setdefault(key, []).append(value)

    minmax = {}
    for key, values in bounds.items():
        minmax[key] = (min(values), max(values))

    return minmax


def normalizeValue(value, min_val, max_val):

    if max_val == min_val:
        return 0.0

    return (value - min_val) / (max_val - min_val)


def normalizedDimensionMagnitude(vector, dimension, bounds):

    value = vector[dimension]

    if isinstance(value, dict):

        total = 0
        count = 0

        for feature, val in value.items():

            min_val, max_val = bounds[(dimension, feature)]

            total += normalizeValue(val, min_val, max_val)
            count += 1

        return total / count if count else 0.0

    else:

        min_val, max_val = bounds[(dimension, None)]
        return normalizeValue(value, min_val, max_val)


def computeVariance(driverData, bounds):

    dimensions = [
        "physical_load",
        "stair_load",
        "traffic_stress",
        "route_distance",
        "cognitive_density"
    ]

    variancePerDimension = {}

    for dim in dimensions:

        values = []

        for driver in driverData.values():

            mag = normalizedDimensionMagnitude(
                driver["cumulative_effort_vector"],
                dim,
                bounds
            )

            values.append(mag)

        mean = sum(values) / len(values)

        variance = sum((x - mean) ** 2 for x in values) / len(values)

        variancePerDimension[dim] = variance

    return variancePerDimension


def fairnessPenalty(variance_dict):

    weights = {
        "physical_load": 1.5,
        "stair_load": 1.3,
        "traffic_stress": 1.0,
        "route_distance": 1.0,
        "cognitive_density": 0.8
    }

    return sum(weights[d] * variance_dict[d] for d in variance_dict)


def percentile(values, p):

    values = sorted(values)

    if not values:
        return 0

    k = (len(values) - 1) * p
    f = math.floor(k)
    c = math.ceil(k)

    if f == c:
        return values[int(k)]

    d0 = values[f] * (c - k)
    d1 = values[c] * (k - f)

    return d0 + d1


def computeHeavyThreshold(effortVectors):

    physical_weights = [
        c["physical_load"]["total_weight"]
        for c in effortVectors.values()
    ]

    durations = [
        c["route_distance"]["total_duration"]
        for c in effortVectors.values()
    ]

    physical_threshold = percentile(physical_weights, HEAVY_PERCENTILE)
    duration_threshold = percentile(durations, HEAVY_PERCENTILE)

    return physical_threshold, duration_threshold


def isHeavyRoute(cluster, physical_threshold, duration_threshold):

    if cluster["physical_load"]["total_weight"] >= physical_threshold:
        return True

    if cluster["route_distance"]["total_duration"] >= duration_threshold:
        return True

    return False


def addVectors(v1, v2):

    result = copy.deepcopy(v1)

    for category in v2:

        if isinstance(v2[category], dict):

            for feature in v2[category]:
                result[category][feature] += v2[category][feature]

        else:
            result[category] += v2[category]

    return result


def compute_normalized_vector_magnitude(vector, bounds):

    dimensions = vector.keys()

    total = 0
    count = 0

    for dim in dimensions:

        mag = normalizedDimensionMagnitude(vector, dim, bounds)

        total += mag
        count += 1

    return total / count if count else 0



def allocateDrivers(effortVectors, driverData):

    applyDecay(driverData)

    bounds = compute_static_feature_bounds(effortVectors)

    physical_threshold, duration_threshold = computeHeavyThreshold(effortVectors)

    assignments = {}

    initial_variance = computeVariance(driverData, bounds)
    print("Initial Variance:", initial_variance)

    sorted_clusters = sorted(
        effortVectors.items(),
        key=lambda item: compute_normalized_vector_magnitude(item[1], bounds),
        reverse=True
    )

    for cluster_name, cluster_vector in sorted_clusters:

        best_driver = None
        lowest_penalty = math.inf

        for driver_name, driver_state in driverData.items():

            # Heavy constraint
            if isHeavyRoute(cluster_vector, physical_threshold, duration_threshold):
                if driver_state["consecutive_heavy_days"] >= 2:
                    continue

            temp_driverData = copy.deepcopy(driverData)

            updated_vector = addVectors(
                temp_driverData[driver_name]["cumulative_effort_vector"],
                cluster_vector
            )

            temp_driverData[driver_name]["cumulative_effort_vector"] = updated_vector

            variance_dict = computeVariance(temp_driverData, bounds)
            penalty = fairnessPenalty(variance_dict)

            if penalty < lowest_penalty:

                lowest_penalty = penalty
                best_driver = driver_name

        if best_driver:

            before = computeVariance(driverData, bounds)

            driverData[best_driver]["cumulative_effort_vector"] = addVectors(
                driverData[best_driver]["cumulative_effort_vector"],
                cluster_vector
            )

            after = computeVariance(driverData, bounds)

            print(f"\nCluster {cluster_name} : {best_driver}")
            print("Variance Before:", before)
            print("Variance After :", after)

            if isHeavyRoute(cluster_vector, physical_threshold, duration_threshold):
                driverData[best_driver]["consecutive_heavy_days"] += 1
            else:
                driverData[best_driver]["consecutive_heavy_days"] = 0

            assignments[cluster_name] = best_driver

    return assignments


def main():

    effortVectors = openJson("data/jsonFiles/finalFeatures.json")
    driverData = openJson("data/jsonFiles/driversdata.json")

    assignments = allocateDrivers(effortVectors, driverData)

    print("\nFinal Assignments:")
    print(assignments)


if __name__ == "__main__":
    main()