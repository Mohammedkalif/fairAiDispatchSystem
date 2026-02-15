import json
import copy
import math

def openJson (filePath):
    with open(filePath , "r") as file:
        return json.load(file)

def addVectors(v1 , v2):
    result = copy.deepcopy(v1)
    for category in v2:
        if isinstance(v2[category] , dict):
            for feature in v2[category]:
                result[category][feature] += v2[category][feature]
    return result

def dimensionMagnitude(vector , dimension):
    value = vector[dimension]
    if isinstance(value , dict):
        return sum(value.values())
    else:
        return value

def computeVariance(driverData):
    dimensions  = [
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
            magn = dimensionMagnitude(
                driver["cumulative_effort_vector"], 
                dim
            )
            values.append(magn)

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

    total = 0

    for dim in variance_dict:
        total += weights[dim] * variance_dict[dim]

    return total


def isHeavyRoute(cluster):
    physical = sum(cluster["physical_load"].values())
    duration = cluster["route_distance"]["total_duration"]
    return (physical + duration) > 1000

def allocateDrivers(effortVectors, driverData):

    assignments = {}

    # Sort clusters by heaviness (heavy first)
    sorted_clusters = sorted(
        effortVectors.items(),
        key=lambda x: sum(x[1]["physical_load"].values()),
        reverse=True
    )

    for cluster_name, cluster_vector in sorted_clusters:

        best_driver = None
        lowest_penalty = math.inf

        for driver_name, driver_state in driverData.items():

            # Hard constraint: heavy day rule
            if isHeavyRoute(cluster_vector):
                if driver_state["consecutive_heavy_days"] >= 2:
                    continue

            # Simulate
            temp_driverData = copy.deepcopy(driverData)

            updated_vector = addVectors(
                temp_driverData[driver_name]["cumulative_effort_vector"],
                cluster_vector
            )

            temp_driverData[driver_name]["cumulative_effort_vector"] = updated_vector

            # Compute fairness
            variance_dict = computeVariance(temp_driverData)
            penalty = fairnessPenalty(variance_dict)

            if penalty < lowest_penalty:
                lowest_penalty = penalty
                best_driver = driver_name

        # Assign
        if best_driver is not None:

            driverData[best_driver]["cumulative_effort_vector"] = addVectors(
                driverData[best_driver]["cumulative_effort_vector"],
                cluster_vector
            )

            if isHeavyRoute(cluster_vector):
                driverData[best_driver]["consecutive_heavy_days"] += 1
            else:
                driverData[best_driver]["consecutive_heavy_days"] = 0

            assignments[cluster_name] = best_driver

    return assignments



def main():
    effortVectors = openJson("data/jsonFiles/finalFeatures.json")
    driverData = openJson("data/jsonFiles/driversdata.json")
    assignments = allocateDrivers(effortVectors, driverData)
    print(assignments)

if __name__ == "__main__":
    main()