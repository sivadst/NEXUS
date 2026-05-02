from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple


@dataclass(frozen=True)
class Node:
    name: str
    lat: float
    lon: float
    capacity: int = 8


@dataclass(frozen=True)
class Edge:
    source: str
    target: str
    distance: Optional[float]
    capacity: int = 6
    highway: str = "road"
    weight: Optional[float] = None


def get_nodes() -> List[Node]:
    return [
        Node("Main Gate", 13.6275, 80.0240),
        Node("Library", 13.6283, 80.0258),
        Node("Lecture Hall A", 13.6290, 80.0235),
        Node("Lecture Hall B", 13.6297, 80.0244),
        Node("Student Center", 13.6288, 80.0266),
        Node("Dormitory", 13.6281, 80.0275),
        Node("Gym", 13.6294, 80.0267),
        Node("Science Block", 13.6301, 80.0249),
        Node("Cafeteria", 13.6279, 80.0262),
        Node("Administration", 13.6302, 80.0271),
        Node("Parking Lot", 13.6310, 80.0230),
        Node("Medical Center", 13.6308, 80.0259),
        Node("Park", 13.6265, 80.0280),
    ]


def get_edges() -> List[Edge]:
    return [
        Edge("Main Gate", "Library", None, capacity=8),
        Edge("Main Gate", "Lecture Hall A", None, capacity=6),
        Edge("Main Gate", "Parking Lot", None, capacity=12),
        Edge("Library", "Lecture Hall A", None, capacity=8),
        Edge("Library", "Student Center", None, capacity=10),
        Edge("Lecture Hall A", "Lecture Hall B", None, capacity=7),
        Edge("Lecture Hall B", "Science Block", None, capacity=7),
        Edge("Student Center", "Gym", None, capacity=9),
        Edge("Student Center", "Cafeteria", None, capacity=8),
        Edge("Dormitory", "Cafeteria", None, capacity=6),
        Edge("Dormitory", "Park", None, capacity=5),
        Edge("Gym", "Medical Center", None, capacity=8),
        Edge("Science Block", "Administration", None, capacity=8),
        Edge("Administration", "Parking Lot", None, capacity=10),
        Edge("Cafeteria", "Parking Lot", None, capacity=8),
        Edge("Medical Center", "Parking Lot", None, capacity=9),
        Edge("Park", "Main Gate", None, capacity=6),
        Edge("Park", "Administration", None, capacity=7),
    ]


def get_node_map() -> Dict[str, Node]:
    return {node.name: node for node in get_nodes()}


def initial_crowd_levels() -> Dict[str, int]:
    return {node.name: 0 for node in get_nodes()}


def initial_node_hazard_levels() -> Dict[str, int]:
    return {node.name: 0 for node in get_nodes()}


def initial_edge_hazard_levels() -> Dict[Tuple[str, str], int]:
    return {edge_key(edge.source, edge.target): 0 for edge in get_edges()}


def edge_key(source: str, target: str) -> Tuple[str, str]:
    return tuple(sorted([source, target]))
OBJECTIVE_WEIGHTS = {
    "distance": 1.0,
    "time": 1.0,
    "cost": 1.0
}