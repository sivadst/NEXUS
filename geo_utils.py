import math
from typing import Dict, List, Optional, Tuple

from data import Edge, Node


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    radius = 6371000.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lon2 - lon1)

    a = math.sin(d_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return radius * c


def normalize_edge_weight(edge: Dict[str, object]) -> float:
    base = float(edge.get("length", 1.0))
    highway = str(edge.get("highway", "road")).lower()
    penalty = 0.0

    if highway in {"footway", "path", "pedestrian", "living_street", "track", "steps"}:
        penalty = 2.0
    elif highway in {"residential", "service", "unclassified", "tertiary"}:
        penalty = 12.0
    elif highway in {"primary", "secondary", "trunk", "motorway"}:
        penalty = 28.0
    else:
        penalty = 10.0

    return base + penalty


def convert_osm_to_internal(
    nodes: Dict[int, Dict[str, float]],
    edges: List[Dict[str, object]],
) -> Tuple[List[Node], List[Edge]]:
    internal_nodes = [
        Node(str(node_id), values["lat"], values["lon"], capacity=50)
        for node_id, values in nodes.items()
    ]

    node_map = {node.name: node for node in internal_nodes}
    internal_edges: List[Edge] = []
    for edge in edges:
        source = str(edge.get("source"))
        target = str(edge.get("target"))
        source_node = node_map.get(source)
        target_node = node_map.get(target)
        if source_node is None or target_node is None:
            continue

        distance = haversine_distance(
            source_node.lat,
            source_node.lon,
            target_node.lat,
            target_node.lon,
        )
        normalized_weight = normalize_edge_weight(edge)
        lanes = edge.get("lanes", 1)
        try:
            capacity = max(4, min(20, int(lanes) * 3))
        except (TypeError, ValueError):
            capacity = 8

        internal_edges.append(
            Edge(
                source,
                target,
                distance,
                capacity=capacity,
                highway=str(edge.get("highway", "road")),
                weight=normalized_weight,
            )
        )

    return internal_nodes, internal_edges


convert_to_internal = convert_osm_to_internal
