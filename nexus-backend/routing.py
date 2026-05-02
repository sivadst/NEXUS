"""
NEXUS Routing Engine — Routing Algorithms
Custom Dijkstra and A* implementations over NetworkX graphs,
with full step tracking for frontend animation replay.
"""

from __future__ import annotations

import heapq
import math
from typing import Callable, Optional

import networkx as nx

from models import RouteResponse, RouteStep
from utils import CachedGraph, Timer, graph_cache, haversine_m, logger


# ── PRIORITY QUEUE HELPERS ───────────────────────────────────────────────────

class _PQ:
    """Thin wrapper around heapq that supports lazy deletion."""

    def __init__(self) -> None:
        self._heap: list[tuple[float, int]] = []
        self._removed: set[int] = set()

    def push(self, cost: float, node: int) -> None:
        heapq.heappush(self._heap, (cost, node))

    def pop(self) -> tuple[float, int]:
        while self._heap:
            cost, node = heapq.heappop(self._heap)
            if node not in self._removed:
                return cost, node
        raise IndexError("Priority queue is empty")

    def remove(self, node: int) -> None:
        self._removed.add(node)

    def empty(self) -> bool:
        return all(n in self._removed for _, n in self._heap)


# ── GRAPH WEIGHT ACCESSOR ─────────────────────────────────────────────────────

def _edge_weight(G: nx.MultiDiGraph, u: int, v: int) -> float:
    """Return minimum edge length (metres) between u and v (handles multi-edges)."""
    edges = G[u][v]
    return min(
        float(data.get("length", 1.0))
        for data in edges.values()
    )


# ── HEURISTIC FOR A* ─────────────────────────────────────────────────────────

def _haversine_heuristic(G: nx.MultiDiGraph, goal: int) -> Callable[[int], float]:
    """Return a closure that computes the haversine distance from any node to goal."""
    g_lat = G.nodes[goal]["y"]
    g_lon = G.nodes[goal]["x"]

    def h(node: int) -> float:
        n = G.nodes[node]
        return haversine_m(n["y"], n["x"], g_lat, g_lon)

    return h


# ── DIJKSTRA ─────────────────────────────────────────────────────────────────

def dijkstra(
    G: nx.MultiDiGraph,
    source: int,
    target: int,
) -> tuple[list[int], float, int]:
    """
    Classic Dijkstra's shortest path.

    Returns
    -------
    path      : ordered list of node IDs from source to target
    cost      : total path length in metres
    steps     : number of nodes popped from the priority queue
    """
    dist: dict[int, float] = {n: math.inf for n in G.nodes}
    dist[source] = 0.0
    prev: dict[int, Optional[int]] = {n: None for n in G.nodes}
    visited: set[int] = set()
    steps = 0

    pq = _PQ()
    pq.push(0.0, source)

    while not pq.empty():
        try:
            d, u = pq.pop()
        except IndexError:
            break

        if u in visited:
            continue
        visited.add(u)
        steps += 1

        if u == target:
            break

        for v in G.successors(u):
            if v in visited:
                continue
            weight = _edge_weight(G, u, v)
            nd = d + weight
            if nd < dist[v]:
                dist[v] = nd
                prev[v] = u
                pq.push(nd, v)

    if math.isinf(dist[target]):
        return [], math.inf, steps

    path = _reconstruct_path(prev, source, target)
    return path, dist[target], steps


# ── A* ────────────────────────────────────────────────────────────────────────

def astar(
    G: nx.MultiDiGraph,
    source: int,
    target: int,
) -> tuple[list[int], float, int]:
    """
    A* shortest path with haversine heuristic.

    Returns
    -------
    path      : ordered list of node IDs from source to target
    cost      : total path length in metres (g-score)
    steps     : number of nodes expanded
    """
    h = _haversine_heuristic(G, target)

    g_score: dict[int, float] = {n: math.inf for n in G.nodes}
    g_score[source] = 0.0
    prev: dict[int, Optional[int]] = {n: None for n in G.nodes}
    closed: set[int] = set()
    steps = 0

    pq = _PQ()
    pq.push(h(source), source)

    while not pq.empty():
        try:
            _, u = pq.pop()
        except IndexError:
            break

        if u in closed:
            continue
        closed.add(u)
        steps += 1

        if u == target:
            break

        for v in G.successors(u):
            if v in closed:
                continue
            weight = _edge_weight(G, u, v)
            tentative_g = g_score[u] + weight
            if tentative_g < g_score[v]:
                g_score[v] = tentative_g
                prev[v] = u
                f = tentative_g + h(v)
                pq.push(f, v)

    if math.isinf(g_score[target]):
        return [], math.inf, steps

    path = _reconstruct_path(prev, source, target)
    return path, g_score[target], steps


# ── PATH RECONSTRUCTION ───────────────────────────────────────────────────────

def _reconstruct_path(
    prev: dict[int, Optional[int]],
    source: int,
    target: int,
) -> list[int]:
    path: list[int] = []
    cur: Optional[int] = target
    while cur is not None:
        path.append(cur)
        cur = prev[cur]
        if cur == source:
            path.append(source)
            break
    path.reverse()
    return path if path and path[0] == source else []


# ── PUBLIC ENTRY POINT ────────────────────────────────────────────────────────

def compute_route(
    graph_id: str,
    start: int,
    end: int,
    algorithm: str,
) -> RouteResponse:
    """
    Look up the cached graph and run the requested routing algorithm.
    Raises KeyError if graph not found, ValueError for unreachable nodes.
    """
    cached: Optional[CachedGraph] = graph_cache.get(graph_id)
    if cached is None:
        raise KeyError(f"Graph '{graph_id}' not found. Call /load-map first.")

    G = cached.G

    # Validate node existence
    if start not in G.nodes:
        raise ValueError(f"Start node {start} not in graph '{graph_id}'.")
    if end not in G.nodes:
        raise ValueError(f"End node {end} not in graph '{graph_id}'.")
    if start == end:
        raise ValueError("Start and end nodes must be different.")

    logger.info(
        "Routing %s → %s via %s on graph %s",
        start, end, algorithm.upper(), graph_id,
    )

    with Timer() as t:
        if algorithm == "dijkstra":
            path, cost, steps = dijkstra(G, start, end)
        elif algorithm == "astar":
            path, cost, steps = astar(G, start, end)
        else:
            raise ValueError(f"Unknown algorithm '{algorithm}'. Use 'dijkstra' or 'astar'.")

    if not path or math.isinf(cost):
        raise ValueError(
            f"No path found between nodes {start} and {end}. "
            "They may be in disconnected parts of the graph."
        )

    logger.info(
        "Route found: %d nodes, %.1f m, %d steps, %.1f ms",
        len(path), cost, steps, t.ms,
    )

    # Build lat/lon coords for the path (frontend polyline)
    path_coords = [
        {"lat": G.nodes[n]["y"], "lon": G.nodes[n]["x"]}
        for n in path
    ]

    return RouteResponse(
        path=path,
        cost=round(cost, 3),
        cost_km=round(cost / 1000, 4),
        steps=steps,
        exec_time_ms=t.ms,
        algorithm=algorithm,
        path_coords=path_coords,
    )
