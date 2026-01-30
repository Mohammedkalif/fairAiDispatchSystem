import json
import pickle as pkl
import requests as req
import numpy as np
import matplotlib.pyplot as plt
from sklearn.cluster import DBSCAN
from sklearn.preprocessing import StandardScaler
from sklearn.neighbors import NearestCentroid
# from dotenv import load_dotenv
# load_dotenv()
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
    plt.figure(figsize=(10, 8))
    unique_labels = np.unique(labels)
    for label in unique_labels:
        mask = labels == label
        plt.scatter(data[mask, 0], data[mask, 1], label=f"Cluster {label}")
    plt.title("DBSCAN Clustering of Stoppings")
    plt.xlabel("Feature 1")
    plt.ylabel("Feature 2")
    plt.legend()
    plt.show()


def main():
    with open("data/jsonFiles/stoppings.json") as f:
        stoppings = np.array(json.load(f))

    normalized_stoppings = fit_and_save_scaler(stoppings)
    scaler = load_scaler()

    labels = cluster_stoppings(normalized_stoppings)

    clustered_stoppings = {}
    for label in np.unique(labels):
        mask = labels == label
        clustered_stoppings[f"Cluster {label}"] = (
            denormalize_stoppings(normalized_stoppings[mask], scaler)
            .tolist()
        )
    plot_clusters(normalized_stoppings , labels)

    with open("data/jsonFiles/clustered_stoppings.json", "w") as f:
        json.dump(clustered_stoppings, f, indent=1)


if __name__ == "__main__":
    main()
