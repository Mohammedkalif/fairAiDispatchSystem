import json
import pickle as pkl
from tracemalloc import stop
import requests as req
import numpy as np
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from scipy.spatial import distance_matrix
from scipy.optimize import linear_sum_assignment 
SCALER_PATH = "stopping_scaler.pkl"

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


def cluster_stoppings(normalized_stoppings, max_size=50):
    n_points = len(normalized_stoppings)
    n_clusters = (n_points + max_size - 1) // max_size
    
    if n_clusters == 0:
        return np.array([])
        
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init='auto')
    kmeans.fit(normalized_stoppings)
    centers = kmeans.cluster_centers_
    
    dist = distance_matrix(normalized_stoppings, centers)
    cost_matrix = np.repeat(dist, max_size, axis=1)
    
    row_ind, col_ind = linear_sum_assignment(cost_matrix)
    labels = col_ind // max_size
    
    return labels[np.argsort(row_ind)]

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
