import heapq
import math
from typing import Dict, List, Optional, Tuple

from geo_utils import haversine_distance


def dijkstra(graph: Dict[str, List[Tuple[str, float]]], start: str, goal: str) -> Tuple[Optional[List[str]], Optional[float]]:
    if start not in graph or goal not in graph:
        return None, None

    distances = {node: float("inf") for node in graph}
    previous = {node: None for node in graph}
    distances[start] = 0
    heap = [(0.0, start)]

    while heap:
        current_distance, node = heapq.heappop(heap)
        if node == goal:
            break
        if current_distance > distances[node]:
            continue
        for neighbor, weight in graph[node]:
            tentative = current_distance + weight
            if tentative < distances[neighbor]:
                distances[neighbor] = tentative
                previous[neighbor] = node
                heapq.heappush(heap, (tentative, neighbor))

    if distances[goal] == float("inf"):
        return None, None

    path = []
    pointer = goal
    while pointer is not None:
        path.append(pointer)
        pointer = previous[pointer]
    return list(reversed(path)), distances[goal]


def heuristic(node: str, goal: str, coords: Dict[str, Tuple[float, float]]) -> float:
    if node not in coords or goal not in coords:
        return 0.0
    return haversine_distance(coords[node][0], coords[node][1], coords[goal][0], coords[goal][1])


def a_star(
    graph: Dict[str, List[Tuple[str, float]]],
    start: str,
    goal: str,
    coords: Dict[str, Tuple[float, float]],
) -> Tuple[Optional[List[str]], Optional[float]]:
    if start not in graph or goal not in graph:
        return None, None

    open_set = [(heuristic(start, goal, coords), start)]
    came_from = {}
    g_score = {node: float("inf") for node in graph}
    g_score[start] = 0.0
    f_score = {node: float("inf") for node in graph}
    f_score[start] = heuristic(start, goal, coords)

    while open_set:
        _, current = heapq.heappop(open_set)
        if current == goal:
            break
        for neighbor, weight in graph[current]:
            tentative_g = g_score[current] + weight
            if tentative_g < g_score[neighbor]:
                came_from[neighbor] = current
                g_score[neighbor] = tentative_g
                f_score[neighbor] = tentative_g + heuristic(neighbor, goal, coords)
                heapq.heappush(open_set, (f_score[neighbor], neighbor))

    if g_score[goal] == float("inf"):
        return None, None

    path = []
    node = goal
    while node in came_from:
        path.append(node)
        node = came_from[node]
    path.append(start)
    return list(reversed(path)), g_score[goal]
