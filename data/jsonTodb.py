import json
import mysql.connector
from datetime import date

DB_CONFIG = {
    "host": "localhost",
    "user": "fairAI",
    "password": "211502",
    "database": "fairDispatch"
}

DATA_FILE = "data/jsonFiles/stoppingandpackage.json"
VISIT_DATE = date.today()  


def main():
    # Load JSON
    with open(DATA_FILE, "r") as f:
        data = json.load(f)

    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()

    insert_stop = """
        INSERT INTO stoppings (stop_id, latitude, longitude, floor, has_lift)
        VALUES (%s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE stop_id = stop_id;
    """

    insert_visit = """
        INSERT INTO stop_visits (visit_id, stop_id, visit_date)
        VALUES (%s, %s, %s);
    """

    insert_package = """
        INSERT INTO packages
        (package_id, visit_id, weight, height, width, breadth)
        VALUES (%s, %s, %s, %s, %s, %s);
    """

    for stop in data:
        stop_id = stop["stop_id"]
        lon, lat = stop["location"]

        first_pkg = stop["packages"][0]
        floor = first_pkg["floor"]
        has_lift = first_pkg["has_elevator"]

        cursor.execute(
            insert_stop,
            (stop_id, lat, lon, floor, has_lift)
        )

        visit_id = f"{stop_id}_{VISIT_DATE}"
        cursor.execute(
            insert_visit,
            (visit_id, stop_id, VISIT_DATE)
        )

        for pkg in stop["packages"]:
            cursor.execute(
                insert_package,
                (
                    pkg["package_id"],
                    visit_id,
                    pkg["weight"],
                    pkg["height"],
                    pkg["width"],
                    pkg["breadth"]
                )
            )

    conn.commit()
    cursor.close()
    conn.close()

    print("Data inserted successfully.")


if __name__ == "__main__":
    main()
