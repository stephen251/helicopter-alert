import os
import requests
from geopy.distance import geodesic

HOME_LAT = 55.611
HOME_LON = -4.495
RADIUS_MILES = 3

BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

def get_bbox(lat, lon, miles):
    delta_lat = miles / 69
    delta_lon = miles / (69 * 0.57)
    return lat - delta_lat, lon - delta_lon, lat + delta_lat, lon + delta_lon

def send_alert(message):
    response = requests.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
        json={
            "chat_id": CHAT_ID,
            "text": message
        },
        timeout=30
    )
    response.raise_for_status()

def get_aircraft():
    lamin, lomin, lamax, lomax = get_bbox(HOME_LAT, HOME_LON, RADIUS_MILES)

    url = "https://opensky-network.org/api/states/all"
    params = {
        "lamin": lamin,
        "lomin": lomin,
        "lamax": lamax,
        "lomax": lomax
    }

    response = requests.get(url, params=params, timeout=30)
    response.raise_for_status()

    data = response.json()
    return data.get("states") or []

def main():
    try:
        aircraft = get_aircraft()
    except requests.exceptions.RequestException as e:
        print(f"OpenSky request failed: {e}")
        return

    print(f"Aircraft found: {len(aircraft)}")

    for state in aircraft:
        icao24 = state[0]
        callsign = state[1].strip() if state[1] else "Unknown"
        lon = state[5]
        lat = state[6]

        if lat is None or lon is None:
            continue

        distance = geodesic((HOME_LAT, HOME_LON), (lat, lon)).miles

        if distance <= RADIUS_MILES:
            message = f"Aircraft nearby: {callsign} / {icao24} — {distance:.1f} miles"
            print(message)
            send_alert(message)

if __name__ == "__main__":
    main()
