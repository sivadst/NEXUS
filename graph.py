import math
from collections import defaultdict
from typing import Dict, List, Optional, Tuple

import plotly.graph_objects as go

from config import BLOCK_HAZARD_THRESHOLD, OBJECTIVE_WEIGHTS
from data import Edge, Node, edge_key, get_nodes
from geo_utils import haversine_distance


def build_adjacency_list(edges: List[Edge]) -> Dict[str, List[Edge]]:
    graph: Dict[str, List[Edge]] = defaultdict(list)
    for edge in edges:
        graph[edge.source].append(edge)
        graph[edge.target].append(edge)
    return graph


def geo_distance(edge: Edge, node_map: Dict[str, Node]) -> float:
    if edge.distance is not None:
        return edge.distance
    source_node = node_map[edge.source]
    target_node = node_map[edge.target]
    return haversine_distance(source_node.lat, source_node.lon, target_node.lat, target_node.lon)


def compute_edge_cost(
    edge: Edge,
    current: str,
    neighbor: str,
    node_map: Dict[str, Node],
    crowd_levels: Dict[str, int],
    node_hazard_levels: Dict[str, int],
    edge_hazard_levels: Dict[Tuple[str, str], int],
    weights: Dict[str, float],
) -> Optional[float]:
    neighbor_hazard = node_hazard_levels.get(neighbor, 0)
    edge_hazard = edge_hazard_levels.get(edge_key(current, neighbor), 0)
    if neighbor_hazard >= BLOCK_HAZARD_THRESHOLD or edge_hazard >= BLOCK_HAZARD_THRESHOLD:
        return None

    distance = edge.weight if edge.weight is not None else geo_distance(edge, node_map)
    crowd_penalty = crowd_levels.get(neighbor, 0) * weights["crowd"]
    hazard_penalty = neighbor_hazard * weights["node_hazard"]
    edge_penalty = edge_hazard * weights["edge_hazard"]
    capacity_pressure = max(
        0,
        ((crowd_levels.get(current, 0) + crowd_levels.get(neighbor, 0)) / max(edge.capacity, 1)) - 1,
    ) * weights["capacity"]

    return distance * weights["distance"] + crowd_penalty + hazard_penalty + edge_penalty + capacity_pressure


def build_dynamic_graph(
    nodes: List[Node],
    edges: List[Edge],
    crowd_levels: Dict[str, int],
    node_hazard_levels: Dict[str, int],
    edge_hazard_levels: Dict[Tuple[str, str], int],
    objective: str = "Safest",
) -> Dict[str, List[Tuple[str, float]]]:
    node_map = {node.name: node for node in nodes}
    graph: Dict[str, List[Tuple[str, float]]] = {}
    base_graph = build_adjacency_list(edges)
    weights = OBJECTIVE_WEIGHTS.get(objective, OBJECTIVE_WEIGHTS["Safest"])

    for node in node_map:
        neighbors = []
        for edge in base_graph[node]:
            neighbor = edge.target if edge.source == node else edge.source
            weight = compute_edge_cost(
                edge,
                node,
                neighbor,
                node_map,
                crowd_levels,
                node_hazard_levels,
                edge_hazard_levels,
                weights,
            )
            if weight is not None:
                neighbors.append((neighbor, weight))
        graph[node] = neighbors
    return graph


def format_edge_summary(
    edges: List[Edge],
    crowd_levels: Dict[str, int],
    node_hazard_levels: Dict[str, int],
    edge_hazard_levels: Dict[Tuple[str, str], int],
) -> List[Dict[str, object]]:
    node_map = {node.name: node for node in get_nodes()}
    rows: List[Dict[str, object]] = []
    for edge in edges:
        distance = geo_distance(edge, node_map)
        rows.append(
            {
                "Edge": f"{edge.source} ↔ {edge.target}",
                "Distance": round(distance, 1),
                "Capacity": edge.capacity,
                "Hazard": edge_hazard_levels.get(edge_key(edge.source, edge.target), 0),
                "Node hazard source": node_hazard_levels.get(edge.source, 0),
                "Node hazard target": node_hazard_levels.get(edge.target, 0),
            }
        )
    return rows


def find_edge(source: str, target: str, edges: List[Edge]) -> Optional[Edge]:
    for edge in edges:
        if edge_key(edge.source, edge.target) == edge_key(source, target):
            return edge
    return None


def calculate_path_metrics(
    path: List[str],
    nodes: List[Node],
    edges: List[Edge],
    crowd_levels: Dict[str, int],
    node_hazard_levels: Dict[str, int],
    edge_hazard_levels: Dict[Tuple[str, str], int],
) -> Optional[Dict[str, object]]:
    if not path:
        return None

    node_map = {node.name: node for node in nodes}
    total_distance = 0.0
    total_hazard = 0
    total_crowd = 0
    for index in range(len(path) - 1):
        edge = find_edge(path[index], path[index + 1], edges)
        if edge is None:
            continue
        total_distance += geo_distance(edge, node_map)
        total_hazard += node_hazard_levels.get(path[index + 1], 0)
        total_crowd += crowd_levels.get(path[index + 1], 0)

    total_hazard += node_hazard_levels.get(path[0], 0)
    total_crowd += crowd_levels.get(path[0], 0)
    risk_score = total_hazard * 18 + total_crowd * 6 + total_distance * 0.5

    return {
        "distance": round(total_distance, 1),
        "hazard_exposure": total_hazard,
        "crowd_exposure": total_crowd,
        "risk_score": round(risk_score, 1),
        "steps": len(path) - 1,
    }


def build_mapbox_figure(
    nodes: List[Node],
    edges: List[Edge],
    crowd_levels: Dict[str, int],
    node_hazard_levels: Dict[str, int],
    edge_hazard_levels: Dict[Tuple[str, str], int],
    highlighted_path: Optional[List[str]] = None,
) -> go.Figure:
    node_map = {node.name: node for node in nodes}
    path_edges = set()
    if highlighted_path:
        path_edges = {
            edge_key(highlighted_path[i], highlighted_path[i + 1])
            for i in range(len(highlighted_path) - 1)
        }

    fig = go.Figure()
    for edge in edges:
        source = node_map[edge.source]
        target = node_map[edge.target]
        edge_id = edge_key(edge.source, edge.target)
        is_route = edge_id in path_edges
        color = "firebrick" if is_route else ("crimson" if edge_hazard_levels.get(edge_id, 0) >= 3 else "lightgray")
        width = 4 if is_route else 1.5
        fig.add_trace(
            go.Scattermapbox(
                lat=[source.lat, target.lat],
                lon=[source.lon, target.lon],
                mode="lines",
                line=dict(color=color, width=width),
                hoverinfo="text",
                text=[
                    f"{edge.source} ↔ {edge.target}<br>Capacity {edge.capacity}<br>Edge hazard {edge_hazard_levels.get(edge_id, 0)}"
                ],
                showlegend=False,
            )
        )

    node_lats = [node.lat for node in nodes]
    node_lons = [node.lon for node in nodes]
    node_colors = []
    node_sizes = []
    hover_text = []
    for node in nodes:
        hazard = node_hazard_levels.get(node.name, 0)
        crowd = crowd_levels.get(node.name, 0)
        if hazard >= 3:
            node_colors.append("darkred")
        elif hazard > 0:
            node_colors.append("orange")
        elif crowd >= 6:
            node_colors.append("darkblue")
        elif crowd > 0:
            node_colors.append("royalblue")
        else:
            node_colors.append("green")
        node_sizes.append(8 + crowd * 3)
        hover_text.append(
            f"{node.name}<br>Crowd {crowd}<br>Hazard {hazard}<br>Capacity {node.capacity}"
        )

    fig.add_trace(
        go.Scattermapbox(
            lat=node_lats,
            lon=node_lons,
            mode="markers+text",
            marker=dict(size=node_sizes, color=node_colors, opacity=0.8),
            text=[node.name for node in nodes],
            textposition="top center",
            hoverinfo="text",
            hovertext=hover_text,
            showlegend=False,
        )
    )

    center_lat = sum(node_lats) / len(node_lats) if nodes else 0
    center_lon = sum(node_lons) / len(node_lons) if nodes else 0
    fig.update_layout(
        mapbox_style="open-street-map",
        mapbox_zoom=13,
        mapbox_center={"lat": center_lat, "lon": center_lon},
        margin=dict(l=20, r=20, t=40, b=20),
        height=650,
    )
    return fig
