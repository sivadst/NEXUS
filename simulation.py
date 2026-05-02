import random
from collections import defaultdict
from typing import Dict, List, Tuple

from config import MAX_HAZARD_LEVEL
from data import Edge, Node, edge_key
from geo_utils import haversine_distance


def build_adjacency(edges: List[Edge]) -> Dict[str, List[Tuple[str, Edge]]]:
    adjacency: Dict[str, List[Tuple[str, Edge]]] = defaultdict(list)
    for edge in edges:
        adjacency[edge.source].append((edge.target, edge))
        adjacency[edge.target].append((edge.source, edge))
    return adjacency


def simulate_crowd_step(
    crowd_levels: Dict[str, int],
    nodes: List[Node],
    edges: List[Edge],
    node_hazard_levels: Dict[str, int],
    steps: int = 3,
) -> Dict[str, int]:
    updated = crowd_levels.copy()
    adjacency = build_adjacency(edges)

    for _ in range(steps):
        hotspots = sorted(updated, key=updated.get, reverse=True)[:3]
        for node in hotspots:
            if updated[node] <= 1:
                continue
            safe_neighbors = [neighbor for neighbor, _ in adjacency[node] if node_hazard_levels.get(neighbor, 0) < MAX_HAZARD_LEVEL]
            if not safe_neighbors:
                continue
            target = random.choice(safe_neighbors)
            transfer = min(2, updated[node])
            updated[node] -= transfer
            updated[target] += transfer

    low_pressure_nodes = [node_obj for node_obj in nodes if updated[node_obj.name] < 6]
    if not low_pressure_nodes:
        low_pressure_nodes = nodes

    for node_obj in random.sample(low_pressure_nodes, min(3, len(low_pressure_nodes))):
        updated[node_obj.name] = min(updated[node_obj.name] + random.choice([0, 1, 2]), 12)

    return {node: max(0, min(value, 12)) for node, value in updated.items()}


def apply_hazard_zone(
    node_hazard_levels: Dict[str, int],
    nodes: List[Node],
    center: Tuple[float, float],
    radius_m: float,
    severity: int,
) -> Dict[str, int]:
    updated = node_hazard_levels.copy()
    for node in nodes:
        distance = haversine_distance(node.lat, node.lon, center[0], center[1])
        if distance <= radius_m:
            updated[node.name] = min(MAX_HAZARD_LEVEL, updated.get(node.name, 0) + severity)
    return updated


def simulate_hazard_step(
    node_hazard_levels: Dict[str, int],
    edge_hazard_levels: Dict[Tuple[str, str], int],
    nodes: List[Node],
    edges: List[Edge],
) -> Tuple[Dict[str, int], Dict[Tuple[str, str], int]]:
    updated_node = node_hazard_levels.copy()
    updated_edge = edge_hazard_levels.copy()
    adjacency = build_adjacency(edges)
    active_nodes = [node for node, severity in updated_node.items() if severity >= 2]

    if not active_nodes:
        starter = random.choice(nodes)
        updated_node = apply_hazard_zone(updated_node, nodes, (starter.lat, starter.lon), radius_m=250.0, severity=4)
        active_nodes = [starter.name]

    propagated = False
    for node in active_nodes:
        neighbors = adjacency[node]
        for neighbor, edge in neighbors:
            key = edge_key(node, neighbor)
            if random.random() < 0.45:
                updated_node[neighbor] = max(updated_node.get(neighbor, 0), min(MAX_HAZARD_LEVEL, updated_node[node] - 1))
                updated_edge[key] = max(updated_edge.get(key, 0), min(MAX_HAZARD_LEVEL, updated_node[node]))
                propagated = True

    if active_nodes and not propagated:
        chosen = random.choice(active_nodes)
        neighbors = adjacency[chosen]
        if neighbors:
            neighbor, edge = random.choice(neighbors)
            key = edge_key(chosen, neighbor)
            updated_node[neighbor] = max(updated_node.get(neighbor, 0), min(MAX_HAZARD_LEVEL, updated_node[chosen] - 1))
            updated_edge[key] = max(updated_edge.get(key, 0), min(MAX_HAZARD_LEVEL, updated_node[chosen]))

    for node in updated_node:
        if updated_node[node] > 0 and random.random() < 0.20:
            updated_node[node] = max(1, updated_node[node] - 1)

    return updated_node, updated_edge


def apply_scenario(
    scenario_name: str,
    nodes: List[Node],
    edges: List[Edge],
) -> Tuple[Dict[str, int], Dict[str, int], Dict[Tuple[str, str], int]]:
    crowd = {node.name: 0 for node in nodes}
    node_hazard = {node.name: 0 for node in nodes}
    edge_hazard = {edge_key(edge.source, edge.target): 0 for edge in edges}
    adjacency = build_adjacency(edges)
    node_names = [node.name for node in nodes]

    def top_degree_nodes(count: int) -> List[str]:
        sorted_nodes = sorted(node_names, key=lambda n: len(adjacency.get(n, [])), reverse=True)
        return sorted_nodes[: min(count, len(sorted_nodes))]

    if scenario_name == "Hazard Active":
        hotspots = [name for name in ["Science Block", "Gym", "Parking Lot"] if name in node_names]
        if not hotspots:
            hotspots = top_degree_nodes(3)
        for hotspot in hotspots:
            node_hazard[hotspot] = 4
        for source in hotspots:
            for neighbor, edge in adjacency.get(source, []):
                edge_hazard[edge_key(source, neighbor)] = 3
    elif scenario_name == "High Crowd":
        hotspots = [name for name in ["Student Center", "Cafeteria", "Lecture Hall A"] if name in node_names]
        if not hotspots:
            hotspots = top_degree_nodes(3)
        for congested in hotspots:
            crowd[congested] = 8
        extra = [name for name in ["Library", "Dormitory"] if name in node_names]
        for node_name in extra:
            crowd[node_name] = max(crowd[node_name], 5)
    else:
        entries = [name for name in ["Main Gate", "Library", "Cafeteria"] if name in node_names]
        if not entries:
            entries = top_degree_nodes(3)
        for entry in entries:
            crowd[entry] = 2

    return crowd, node_hazard, edge_hazard


def reset_simulation_state():
    from streamlit import session_state

    session_state.crowd_levels = {node: 0 for node in session_state.crowd_levels}
    session_state.node_hazard_levels = {node: 0 for node in session_state.node_hazard_levels}
    session_state.edge_hazard_levels = {edge: 0 for edge in session_state.edge_hazard_levels}
    session_state.route_info = None
    session_state.route_alternatives = {}
