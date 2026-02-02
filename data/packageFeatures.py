import json

def main():
    with open("jsonFiles/stoppingandpackage.json" , "r") as f:
        data = json.load(f)
    
    packageDetails = {
        stop["stop_id"] : stop["packages"]
        for stop in data
    }