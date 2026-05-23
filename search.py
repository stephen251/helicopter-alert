import time
import requests
from geopy.distance import geodesic
import subprocess

HOME_LAT = 55.611
HOME_LON = -4.495
RADIUS_MILES = 3
CHECK_EVERY_SECONDS = 30

seen = set()

def get_bbox(lat, lon, miles):
    delta_lat = miles / 69
    delta_lon = miles / (69 * 0.57)
    return lat - delta_lat, lon - delta_lon, lat + delta_lat, lon + delta_lon

def get_aircraft():
    lamin, lomin, lamax, lomax = get_bbox(HOME_LAT, HOME_LON, RADIUS_MILES)

    url = "https://opensky-network.org/api/states/all"
    params = {
        "lamin": lamin,
        "lomin": lomin,
        "lamax": lamax,
        "lomax": lomax
    }

    r = requests.get(url, params=params, timeout=5)
    r.raise_for_status()

    data = r.json()
    return data.get("states") or []

def send_alert(callsign, icao24, distance):
    message = f"{callsign} — {distance:.1f} miles away"

    print(message, flush=True)

    subprocess.run([
        "osascript",
        "-e",
        f'display notification "{message}" with title "Aircraft nearby"'
    ])

while True:
    try:
        aircraft = get_aircraft()

        for state in aircraft:
            icao24 = state[0]
            callsign = state[1].strip() if state[1] else "Unknown"
            lon = state[5]
            lat = state[6]

            if lat is None or lon is None:
                continue

            distance = geodesic((HOME_LAT, HOME_LON), (lat, lon)).miles

            if distance <= RADIUS_MILES and icao24 not in seen:
                send_alert(callsign, icao24, distance)
                seen.add(icao24)

    except Exception as e:
        print(f"Error: {e}", flush=True)

    time.sleep(CHECK_EVERY_SECONDS)
