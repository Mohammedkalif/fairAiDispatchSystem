import json
import pickle as pkl
from tracemalloc import stop
import requests as req
import numpy as np
import matplotlib.pyplot as plt
from sklearn.cluster import DBSCAN
from sklearn.preprocessing import StandardScaler
from sklearn.neighbors import NearestCentroid 
SCALER_PATH = "data/stopping_scaler.pkl"

def fit_and_save_scaler(data, path=SCALER_PATH):
    scaler = StandardScaler()
    scaled = scaler.fit_transform(data)
    with open(path, "wb") as f:
        pkl.dump(scaler, f)
    return scaled


def load_scaler(path=SCALER_PATH):
    with open(path, "rb") as f:
        return pkl.load(f)


def normalize_stoppings(stoppings, scaler):
    return scaler.transform(stoppings)


def denormalize_stoppings(stoppings, scaler):
    return scaler.inverse_transform(stoppings)


def merge_noise_with_nearest_cluster(data, labels):

    noise_mask = labels == -1
    cluster_mask = ~noise_mask

    if not np.any(noise_mask) or not np.any(cluster_mask):
        return labels

    centroid_model = NearestCentroid()
    centroid_model.fit(data[cluster_mask], labels[cluster_mask])

    labels[noise_mask] = centroid_model.predict(data[noise_mask])
    return labels


def cluster_stoppings(normalized_stoppings, eps=0.5, min_samples=5):
    dbscan = DBSCAN(eps=eps, min_samples=min_samples)
    labels = dbscan.fit_predict(normalized_stoppings)
    return merge_noise_with_nearest_cluster(normalized_stoppings, labels)

def plot_clusters(data, labels):
    plt.figure(figsize=(6,6))
    unique_labels = np.unique(labels)
    for label in unique_labels:
        mask = labels == label
        plt.scatter(data[mask, 0], data[mask, 1], label=f"Cluster {label}")
    plt.title("DBSCAN Clustering of Stoppings")
    plt.xlabel("Feature 1")
    plt.ylabel("Feature 2")
    plt.legend()
    plt.savefig("data/cluster_plot.png")


def main():
    with open("data/jsonFiles/stoppingandpackage.json") as f:
        data = json.load(f)
    stop_location_dict = {
        stop["stop_id"]: stop["location"]
        for stop in data
    }
    stoppings = list(stop_location_dict.values())
    stoppings = np.array(stoppings, dtype=float)

    normalized_stoppings = fit_and_save_scaler(stoppings)
    scaler = load_scaler()

    labels = cluster_stoppings(normalized_stoppings)

    clustered_stoppings = {}
    stop_ids = list(stop_location_dict.keys())
    for label in np.unique(labels):
        mask = labels == label
        cluster_stops = {}
        masked_stop_ids = [stop_ids[i] for i in range(len(stop_ids)) if mask[i]]
        denormalized_coords = denormalize_stoppings(normalized_stoppings[mask], scaler).tolist()
        for stop_id, coords in zip(masked_stop_ids, denormalized_coords):
            cluster_stops[stop_id] = coords
        clustered_stoppings[f"Cluster {label}"] = cluster_stops
    
    plot_clusters(normalized_stoppings, labels)

    with open("data/jsonFiles/clustered_stoppings.json", "w") as f:
        json.dump(clustered_stoppings, f, indent=1)


if __name__ == "__main__":
    main()
