import json
from dotenv import load_dotenv
import requests as req
import os

load_dotenv()

API_KEY = os.getenv("API")
if not API_KEY:
    raise RuntimeError("Missing API key")

with open("data/clustered_stoppings.json", "r") as f:
    clustered_stoppings = json.load(f)

starting_point = [78.17611956533857, 11.683720337350456]
ending_point   = [78.15988980734215, 11.675583838261142]

url = "https://api.openrouteservice.org/optimization"
headers = {
    "Authorization": API_KEY,
    "Content-Type": "application/json"
}

for idx, cluster in enumerate(clustered_stoppings):
    stops = clustered_stoppings[cluster]
    payload = {
        "vehicles": [
            {
                "id": idx + 1,
                "profile" : "driving-car",
                "start": starting_point,
                "end": ending_point
            }
        ],
        "jobs": [
            {"id": i + 1, "location": loc}
            for i, loc in enumerate(stops)
        ]
    }

    print(f"Processing {cluster} with {len(stops)} jobs")

    response = req.post(url, json=payload, headers=headers)

    if response.status_code != 200:
        print("ORS ERROR:", response.status_code)
        print(response.text)
        continue

    with open(f"data/routes_{cluster}.json", "w") as f:
        json.dump(response.json(), f, indent=2)