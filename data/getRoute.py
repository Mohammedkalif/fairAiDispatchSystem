import json
import os
import requests
from dotenv import load_dotenv
from typing import List, Dict


ORS_OPTIMIZATION_URL = "https://api.openrouteservice.org/optimization"
DATA_DIR = "data"

STARTING_POINT = [78.17611956533857, 11.683720337350456]
ENDING_POINT   = [78.15988980734215, 11.675583838261142]


def load_api_key(env_var: str = "API") -> str:
    load_dotenv()
    api_key = os.getenv(env_var)
    if not api_key:
        raise RuntimeError("Missing API key")
    return api_key


def load_clustered_stoppings(filepath: str) -> Dict[str, List[List[float]]]:
    with open(filepath, "r") as file:
        return json.load(file)


def build_payload(
    vehicle_id: int,
    stops: List[List[float]],
    start: List[float],
    end: List[float]
) -> Dict:
    return {
        "vehicles": [
            {
                "id": vehicle_id,
                "profile": "driving-car",
                "start": start,
                "end": end,
            }
        ],
        "jobs": [
            {"id": idx + 1, "location": location}
            for idx, location in enumerate(stops)
        ],
    }


def send_optimization_request(
    url: str,
    api_key: str,
    payload: Dict
) -> Dict | None:
    headers = {
        "Authorization": api_key,
        "Content-Type": "application/json",
    }

    response = requests.post(url, json=payload, headers=headers)

    if response.status_code != 200:
        print("ORS ERROR:", response.status_code)
        print(response.text)
        return None

    return response.json()


def save_route(filepath: str, data: Dict) -> None:
    """Save route data to JSON file."""
    with open(filepath, "w") as file:
        json.dump(data, file, indent=2)

def main() -> None:
    api_key = load_api_key()
    clustered_stoppings = load_clustered_stoppings(
        os.path.join(DATA_DIR, "clustered_stoppings.json")
    )

    for idx, (cluster_name, stops) in enumerate(clustered_stoppings.items(), start=1):
        print(f"Processing {cluster_name} with {len(stops)} jobs")

        payload = build_payload(
            vehicle_id=idx,
            stops=stops,
            start=STARTING_POINT,
            end=ENDING_POINT,
        )

        result = send_optimization_request(
            url=ORS_OPTIMIZATION_URL,
            api_key=api_key,
            payload=payload,
        )

        if result is None:
            continue

        output_path = os.path.join(DATA_DIR, f"routes_{cluster_name}.json")
        save_route(output_path, result)


if __name__ == "__main__":
    main()
