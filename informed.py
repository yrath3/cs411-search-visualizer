"""
informed.py
===========
Informed (heuristic) search algorithms for the road-network graph:

    5. Greedy Best-First Search
    6. A* Search

Both use a HEURISTIC h(n): an estimate of the remaining distance from city n
to the goal.  We use the straight-line (great-circle / "haversine") distance
in miles, computed from the latitude/longitude that data_fetcher.py fetched
from Nominatim.

Why this heuristic is admissible and consistent
-----------------------------------------------
    * Admissible : a road can never be shorter than the straight line between
                   two cities, so h(n) never OVER-estimates the true remaining
                   road distance.  This is what makes A* optimal.
    * Consistent : straight-line distance obeys the triangle inequality,
                   h(n) <= cost(n, n') + h(n'), so A*'s graph-search version
                   (with an explored set) is still optimal.

Same graph format and return shape as uninformed.py:

    result = astar(graph, start, goal, locations)
    result == {"path": [...], "cost": miles, "nodes_expanded": k, "expanded_order": [...]}
"""

import heapq
import math
from itertools import count

from uninformed import make_result, neighbors, reconstruct_path


# ---------------------------------------------------------------------------
# Heuristic
# ---------------------------------------------------------------------------
def haversine(lat1, lon1, lat2, lon2):
    """Great-circle distance in miles between two lat/lon points."""
    R = 3958.8
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def make_heuristic(locations, goal):
    """
    Returns a function h(city) = straight-line miles from `city` to `goal`.
    `locations` is the {"City": {"lat":..,"lon":..}} dict from map_data.json.
    """
    g_lat, g_lon = locations[goal]["lat"], locations[goal]["lon"]

    def h(city):
        c = locations[city]
        return haversine(c["lat"], c["lon"], g_lat, g_lon)

    return h


# ---------------------------------------------------------------------------
# 5. Greedy Best-First Search
# ---------------------------------------------------------------------------
def greedy_best_first(graph, start, goal, locations):
    """
    Main idea   : always move toward whichever frontier city LOOKS closest to
                  the goal, ignoring how far we have already driven.
    Node choice : the frontier node with the LOWEST h(n).
    Information : heuristic h(n) only (no path cost).
    Complete    : yes on a finite graph with an explored set.
    Optimal     : no - it can be lured down a road that looks promising but is long.
    """
    h = make_heuristic(locations, goal)
    tie = count()
    frontier = [(h(start), next(tie), start)]   # (h, tie, node)
    parent = {start: None}
    explored = set()
    expanded = []

    while frontier:
        _, _, node = heapq.heappop(frontier)
        if node in explored:
            continue
        explored.add(node)
        expanded.append(node)

        if node == goal:
            return make_result(graph, reconstruct_path(parent, goal), expanded)

        for nb in neighbors(graph, node):
            if nb not in explored and nb not in parent:
                parent[nb] = node
                heapq.heappush(frontier, (h(nb), next(tie), nb))

    return make_result(graph, [], expanded)


# ---------------------------------------------------------------------------
# 6. A* Search
# ---------------------------------------------------------------------------
def astar(graph, start, goal, locations):
    """
    Main idea   : like UCS, but the priority is f(n) = g(n) + h(n): miles driven
                  so far PLUS the straight-line estimate of miles still to go.
                  The heuristic focuses the search toward the goal, so A*
                  usually expands far fewer nodes than UCS.
    Node choice : the frontier node with the LOWEST f(n) = g(n) + h(n).
    Information : path cost g(n) AND heuristic h(n).
    Complete    : yes.
    Optimal     : yes, because h is admissible (and consistent).
    """
    h = make_heuristic(locations, goal)
    tie = count()
    frontier = [(h(start), next(tie), 0.0, start)]  # (f, tie, g, node)
    best_g = {start: 0.0}
    parent = {start: None}
    explored = set()
    expanded = []

    while frontier:
        f, _, g, node = heapq.heappop(frontier)
        if node in explored:                 # stale entry with a worse g
            continue
        explored.add(node)
        expanded.append(node)

        # Late goal test (on pop) so the returned path is guaranteed optimal
        if node == goal:
            return make_result(graph, reconstruct_path(parent, goal), expanded)

        for nb in neighbors(graph, node):
            new_g = g + graph[node][nb]
            if nb not in best_g or new_g < best_g[nb]:
                best_g[nb] = new_g
                parent[nb] = node
                heapq.heappush(frontier, (new_g + h(nb), next(tie), new_g, nb))

    return make_result(graph, [], expanded)


# Registry used by app.py
INFORMED_ALGORITHMS = {
    "greedy": greedy_best_first,
    "astar": astar,
}
