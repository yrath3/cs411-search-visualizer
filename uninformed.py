"""
uninformed.py
=============
Uninformed ("blind") search algorithms for the road-network graph:

    1. Breadth-First Search   (BFS)
    2. Depth-First Search     (DFS)
    3. Uniform-Cost Search    (UCS)
    4. Iterative Deepening    (IDS)

These algorithms use NO knowledge about how far a city is from the goal.
They only know the graph structure (and, for UCS, the edge costs).

Problem formulation (the same for every algorithm in this project)
-------------------------------------------------------------------
    State        : a city name, e.g. "Peoria, IL"
    Initial state: the source city the user picked
    Goal test    : state == destination city
    Actions      : drive to any neighbouring city  ->  graph[state].keys()
    Transition   : result(state, action) = the neighbouring city
    Path cost    : sum of road miles along the path  ->  graph[u][v]

Graph format:   graph = { "City A": {"City B": miles, "City C": miles}, ... }

Every function has the same signature and return shape:

    result = bfs(graph, start, goal)
    result == {
        "path":           ["City A", "City B", ...],   # [] if no path exists
        "cost":           123.45,                      # total road miles
        "nodes_expanded": 17,                          # how many nodes were popped
        "expanded_order": ["City A", ...],             # order of expansion (for the UI)
    }
"""

import heapq
from collections import deque
from itertools import count


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------
def reconstruct_path(parent, goal):
    """Walk backwards through the parent pointers to rebuild the path."""
    path = []
    node = goal
    while node is not None:
        path.append(node)
        node = parent[node]
    path.reverse()
    return path


def path_cost(graph, path):
    """Sum the edge weights (miles) along a path."""
    return round(sum(graph[path[i]][path[i + 1]] for i in range(len(path) - 1)), 2)


def make_result(graph, path, expanded):
    return {
        "path": path,
        "cost": path_cost(graph, path) if path else 0,
        "nodes_expanded": len(expanded),
        "expanded_order": expanded,
    }


def neighbors(graph, node):
    """Neighbours in a fixed (alphabetical) order so results are reproducible."""
    return sorted(graph.get(node, {}).keys())


# ---------------------------------------------------------------------------
# 1. Breadth-First Search
# ---------------------------------------------------------------------------
def bfs(graph, start, goal):
    """
    Main idea   : explore the graph level by level using a FIFO queue.
    Node choice : always expand the SHALLOWEST node in the frontier.
    Information : depth only (ignores road miles).
    Complete    : yes (finite graph).
    Optimal     : only in the number of edges, NOT in miles.
    """
    if start == goal:
        return make_result(graph, [start], [start])

    frontier = deque([start])
    parent = {start: None}          # doubles as the "reached" set
    expanded = []

    while frontier:
        node = frontier.popleft()   # FIFO -> shallowest first
        expanded.append(node)
        for nb in neighbors(graph, node):
            if nb not in parent:
                parent[nb] = node
                # Early goal test (when the node is GENERATED) - standard for BFS
                if nb == goal:
                    return make_result(graph, reconstruct_path(parent, goal), expanded)
                frontier.append(nb)

    return make_result(graph, [], expanded)


# ---------------------------------------------------------------------------
# 2. Depth-First Search
# ---------------------------------------------------------------------------
def dfs(graph, start, goal):
    """
    Main idea   : dive as deep as possible along one branch before backtracking,
                  using a LIFO stack.
    Node choice : always expand the DEEPEST (most recently generated) node.
    Information : none - not even depth or cost.
    Complete    : yes on a finite graph when we track visited nodes (graph search).
    Optimal     : no - the first path found is usually long and expensive.
    """
    stack = [start]
    parent = {start: None}
    visited = set()
    expanded = []

    while stack:
        node = stack.pop()          # LIFO -> deepest first
        if node in visited:
            continue
        visited.add(node)
        expanded.append(node)

        if node == goal:
            return make_result(graph, reconstruct_path(parent, goal), expanded)

        # Push in reverse alphabetical order so that the alphabetically-first
        # neighbour is popped (explored) first.
        for nb in reversed(neighbors(graph, node)):
            if nb not in visited:
                parent[nb] = node
                stack.append(nb)

    return make_result(graph, [], expanded)


# ---------------------------------------------------------------------------
# 3. Uniform-Cost Search
# ---------------------------------------------------------------------------
def ucs(graph, start, goal):
    """
    Main idea   : expand nodes in order of cheapest path cost so far, g(n),
                  using a priority queue (this is Dijkstra's algorithm).
    Node choice : the frontier node with the LOWEST g(n).
    Information : cumulative path cost g(n) = road miles from start.
    Complete    : yes (all edge costs > 0).
    Optimal     : yes - the first time the goal is popped, its cost is minimal.
    """
    tie = count()                            # tie-breaker so heapq never compares strings
    frontier = [(0.0, next(tie), start)]     # (g, tie, node)
    best_g = {start: 0.0}
    parent = {start: None}
    explored = set()
    expanded = []

    while frontier:
        g, _, node = heapq.heappop(frontier)
        if node in explored:                 # stale entry (a cheaper one was popped earlier)
            continue
        explored.add(node)
        expanded.append(node)

        # Late goal test (when the node is POPPED) - required for optimality
        if node == goal:
            return make_result(graph, reconstruct_path(parent, goal), expanded)

        for nb in neighbors(graph, node):
            new_g = g + graph[node][nb]
            if nb not in best_g or new_g < best_g[nb]:
                best_g[nb] = new_g
                parent[nb] = node
                heapq.heappush(frontier, (new_g, next(tie), nb))

    return make_result(graph, [], expanded)


# ---------------------------------------------------------------------------
# 4. Iterative Deepening Search
# ---------------------------------------------------------------------------
def depth_limited_search(graph, node, goal, limit, path, expanded):
    """
    Recursive DFS that refuses to go deeper than `limit` edges.
    `path` is the current path from the start (used to avoid cycles).

    Returns the full path if the goal is found, "cutoff" if the limit stopped
    us, or None if this branch is exhausted without reaching the goal.
    """
    expanded.append(node)
    if node == goal:
        return list(path)
    if limit == 0:
        return "cutoff"

    cutoff_occurred = False
    for nb in neighbors(graph, node):
        if nb in path:                       # cycle check along the current path
            continue
        path.append(nb)
        result = depth_limited_search(graph, nb, goal, limit - 1, path, expanded)
        path.pop()
        if result == "cutoff":
            cutoff_occurred = True
        elif result is not None:
            return result
    return "cutoff" if cutoff_occurred else None


def ids(graph, start, goal):
    """
    Main idea   : run depth-limited DFS with limit 0, 1, 2, ... until the goal is
                  found.  Combines DFS's tiny memory footprint with BFS's
                  shallowest-solution guarantee.
    Node choice : depth-first inside each iteration, but never deeper than the
                  current limit.
    Information : the current depth limit only.
    Complete    : yes.
    Optimal     : in number of edges (like BFS), not in miles.
    """
    expanded = []
    for limit in range(len(graph) + 1):      # depth can never exceed #cities
        result = depth_limited_search(graph, start, goal, limit, [start], expanded)
        if result == "cutoff":
            continue                         # deepen and try again
        if result is None:
            break                            # exhausted graph: no path
        return make_result(graph, result, expanded)

    return make_result(graph, [], expanded)


# Registry used by app.py
UNINFORMED_ALGORITHMS = {
    "bfs": bfs,
    "dfs": dfs,
    "ucs": ucs,
    "ids": ids,
}
