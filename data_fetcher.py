"""
data_fetcher.py
================
Builds a connected road-network graph for the selected USA region
(Illinois) and saves it to `map_data.json`.

Data sources
------------
  * Nominatim (OpenStreetMap) geocoding API  -> latitude / longitude of each city
  * OSRM routing API                          -> real driving distance (miles) for
                                                 every road connection we define

How the graph is represented
----------------------------
  locations : { "City, IL": {"lat": ..., "lon": ...}, ... }
  graph     : adjacency list  { "City A": {"City B": miles, "City C": miles}, ... }

  Every edge is stored in BOTH directions (undirected graph), because you can
  drive either way along a highway.  The edge weight (miles) is the *path cost*
  used by UCS and A*.

Run with:  python data_fetcher.py
"""

import json
import math
import time
from collections import deque

import requests

# ---------------------------------------------------------------------------
# Configuration: selected USA region and its cities (must be >= 20)
# ---------------------------------------------------------------------------
REGION_NAME = "Illinois, USA"

CITIES = [
    # Chicago metro
    "Chicago, IL",
    "Evanston, IL",
    "Skokie, IL",
    "Des Plaines, IL",
    "Arlington Heights, IL",
    "Palatine, IL",
    "Schaumburg, IL",
    "Elgin, IL",
    "Waukegan, IL",
    "Naperville, IL",
    "Aurora, IL",
    "Bolingbrook, IL",
    "Joliet, IL",
    "Orland Park, IL",
    # Northern / western Illinois
    "DeKalb, IL",
    "Rockford, IL",
    "Ottawa, IL",
    "Moline, IL",
    "Quincy, IL",
    # Central Illinois
    "Peoria, IL",
    "Bloomington, IL",
    "Champaign, IL",
    "Danville, IL",
    "Decatur, IL",
    "Springfield, IL",
    "Kankakee, IL",
    # Southern Illinois
    "Effingham, IL",
    "Carbondale, IL",
]

# Undirected road connections (mostly following interstates / US highways).
# The graph must be CONNECTED: every city reachable from every other city.
ROAD_CONNECTIONS = [
    # Chicago metro core
    ("Chicago, IL", "Evanston, IL"),
    ("Chicago, IL", "Skokie, IL"),
    ("Chicago, IL", "Des Plaines, IL"),
    ("Chicago, IL", "Naperville, IL"),
    ("Chicago, IL", "Joliet, IL"),
    ("Chicago, IL", "Orland Park, IL"),
    ("Evanston, IL", "Skokie, IL"),
    ("Evanston, IL", "Waukegan, IL"),
    ("Skokie, IL", "Des Plaines, IL"),
    ("Des Plaines, IL", "Arlington Heights, IL"),
    ("Arlington Heights, IL", "Palatine, IL"),
    ("Arlington Heights, IL", "Waukegan, IL"),
    ("Palatine, IL", "Schaumburg, IL"),
    ("Schaumburg, IL", "Elgin, IL"),
    ("Schaumburg, IL", "Naperville, IL"),
    ("Naperville, IL", "Aurora, IL"),
    ("Naperville, IL", "Bolingbrook, IL"),
    ("Bolingbrook, IL", "Joliet, IL"),
    ("Aurora, IL", "Joliet, IL"),
    ("Joliet, IL", "Orland Park, IL"),
    ("Joliet, IL", "Kankakee, IL"),
    # Northern / western Illinois
    ("Aurora, IL", "DeKalb, IL"),
    ("Elgin, IL", "DeKalb, IL"),
    ("Elgin, IL", "Rockford, IL"),
    ("DeKalb, IL", "Rockford, IL"),
    ("DeKalb, IL", "Ottawa, IL"),
    ("DeKalb, IL", "Moline, IL"),
    ("Rockford, IL", "Moline, IL"),
    ("Joliet, IL", "Ottawa, IL"),
    ("Ottawa, IL", "Peoria, IL"),
    ("Ottawa, IL", "Bloomington, IL"),
    ("Moline, IL", "Peoria, IL"),
    ("Moline, IL", "Quincy, IL"),
    ("Quincy, IL", "Springfield, IL"),
    ("Quincy, IL", "Peoria, IL"),
    # Central Illinois
    ("Peoria, IL", "Bloomington, IL"),
    ("Peoria, IL", "Springfield, IL"),
    ("Bloomington, IL", "Champaign, IL"),
    ("Bloomington, IL", "Decatur, IL"),
    ("Bloomington, IL", "Springfield, IL"),
    ("Kankakee, IL", "Champaign, IL"),
    ("Kankakee, IL", "Danville, IL"),
    ("Champaign, IL", "Danville, IL"),
    ("Champaign, IL", "Decatur, IL"),
    ("Decatur, IL", "Springfield, IL"),
    # Southern Illinois
    ("Champaign, IL", "Effingham, IL"),
    ("Decatur, IL", "Effingham, IL"),
    ("Effingham, IL", "Carbondale, IL"),
    ("Springfield, IL", "Carbondale, IL"),
]

USER_AGENT = "CS411-Search-Visualizer/1.0 (uic-cs411-student-project)"
OUTPUT_FILE = "map_data.json"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def haversine_distance(coord1, coord2):
    """
    Straight-line (great-circle) distance in miles between two (lat, lon)
    points.  Used only as a FALLBACK if the OSRM routing request fails.
    """
    lat1, lon1 = coord1
    lat2, lon2 = coord2
    R = 3958.8  # Earth radius in miles

    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)

    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return round(R * c, 2)


def fetch_coordinates(city_name):
    """
    Geocode a city name with the Nominatim OpenStreetMap API.
    Returns {"lat": float, "lon": float} or None on failure.
    """
    url = "https://nominatim.openstreetmap.org/search"
    params = {"q": city_name, "format": "json", "limit": 1, "countrycodes": "us"}
    headers = {"User-Agent": USER_AGENT}

    try:
        response = requests.get(url, params=params, headers=headers, timeout=15)
        if response.status_code == 200:
            data = response.json()
            if data:
                return {"lat": float(data[0]["lat"]), "lon": float(data[0]["lon"])}
        else:
            print(f"  [Warning] Nominatim returned HTTP {response.status_code} for {city_name}")
    except Exception as e:
        print(f"  [Warning] Failed to fetch coordinates for {city_name}: {e}")

    return None


def fetch_road_distance(coord1, coord2):
    """
    Real driving distance in miles between two (lat, lon) points using the
    public OSRM routing API.  Falls back to the straight-line distance if the
    routing request fails so the graph is never left with a missing edge.
    """
    lat1, lon1 = coord1
    lat2, lon2 = coord2
    # OSRM expects lon,lat order
    url = f"https://router.project-osrm.org/route/v1/driving/{lon1},{lat1};{lon2},{lat2}"
    params = {"overview": "false"}

    try:
        response = requests.get(url, params=params, timeout=15)
        if response.status_code == 200:
            data = response.json()
            if data.get("code") == "Ok" and data.get("routes"):
                distance_meters = data["routes"][0]["distance"]
                return round(distance_meters * 0.000621371, 2)
        else:
            print(f"  [Warning] OSRM returned HTTP {response.status_code}")
    except Exception as e:
        print(f"  [Warning] OSRM routing failed ({coord1} -> {coord2}): {e}")

    print("  [Fallback] Using straight-line distance for this edge.")
    return haversine_distance(coord1, coord2)


def is_connected(graph):
    """
    Breadth-first traversal from an arbitrary city.  The graph is connected
    if every city is reached.  (Also a nice preview of BFS itself!)
    """
    if not graph:
        return False
    start = next(iter(graph))
    seen = {start}
    queue = deque([start])
    while queue:
        city = queue.popleft()
        for neighbor in graph[city]:
            if neighbor not in seen:
                seen.add(neighbor)
                queue.append(neighbor)
    return len(seen) == len(graph)


# ---------------------------------------------------------------------------
# Main build routine
# ---------------------------------------------------------------------------
def build_graph():
    print(f"Building map graph for region: {REGION_NAME}")
    print(f"Total locations to geocode: {len(CITIES)}\n")

    # 1. Geocode every city -----------------------------------------------
    locations = {}
    for idx, city in enumerate(CITIES, 1):
        print(f"[{idx}/{len(CITIES)}] Geocoding: {city} ...")
        coords = fetch_coordinates(city)
        if coords:
            locations[city] = coords
            print(f"       -> ({coords['lat']:.5f}, {coords['lon']:.5f})")
        else:
            print(f"  [Error] Could not find coordinates for {city}")
        # Nominatim usage policy: at most 1 request per second
        time.sleep(1.1)

    # 2. Fetch road distance for each defined connection --------------------
    graph = {city: {} for city in locations}
    print(f"\nFetching road distances for {len(ROAD_CONNECTIONS)} connections ...")
    total_edges = 0
    for u, v in ROAD_CONNECTIONS:
        if u in locations and v in locations:
            c1 = (locations[u]["lat"], locations[u]["lon"])
            c2 = (locations[v]["lat"], locations[v]["lon"])
            dist = fetch_road_distance(c1, c2)
            graph[u][v] = dist          # store both directions: undirected road
            graph[v][u] = dist
            total_edges += 1
            print(f"  {u} <---> {v} : {dist} miles")
            time.sleep(0.3)
        else:
            print(f"  [Warning] Skipping edge ({u}, {v}) - missing coordinates.")

    # 3. Validate ------------------------------------------------------------
    connected = is_connected(graph)
    print(f"\nCities: {len(locations)}   Edges: {total_edges}   Connected: {connected}")
    if len(locations) < 20:
        print("  [Error] Fewer than 20 cities were geocoded - check the CITIES list.")
    if not connected:
        print("  [Error] Graph is NOT connected - add more ROAD_CONNECTIONS.")

    # 4. Save ----------------------------------------------------------------
    map_data = {
        "region": REGION_NAME,
        "total_cities": len(locations),
        "total_edges": total_edges,
        "connected": connected,
        "locations": locations,
        "graph": graph,
    }
    with open(OUTPUT_FILE, "w") as f:
        json.dump(map_data, f, indent=2)

    print(f"\nGraph construction complete! Saved to {OUTPUT_FILE}.")


if __name__ == "__main__":
    build_graph()
