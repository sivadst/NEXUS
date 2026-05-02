import pickle
import re
from pathlib import Path
from typing import Dict, List, Tuple

import networkx as nx
import osmnx as ox

# ==============================
# CACHE
# ==============================

CACHE_DIR = Path(__file__).parent / "map_cache"
CACHE_DIR.mkdir(exist_ok=True)

# ==============================
# DEFAULT SRM LOCATION
# ==============================

DEFAULT_POINT = (16.442, 80.621)

# ==============================
# HELPERS
# ==============================

def cache_file(key: str) -> Path:
    safe = re.sub(r"[^a-zA-Z0-9]", "_", key)
    return CACHE_DIR / f"{safe}.pkl"


def extract_lat_lon_from_url(url: str):
    match = re.search(r"@(-?\d+\.\d+),(-?\d+\.\d+)", url)
    if match:
        return float(match.group(1)), float(match.group(2))
    return None


def parse_lat_lon(text: str):
    match = re.match(r"^\s*([+-]?\d+(\.\d+)?),\s*([+-]?\d+(\.\d+)?)\s*$", text)
    if match:
        return float(match.group(1)), float(match.group(3))
    return None


# ==============================
# MAIN
# ==============================

def load_map(input_text: str = "") -> Tuple[Dict, List]:

    key = input_text or "default_srm"
    cache_path = cache_file(key)

    # ✅ CACHE
    if cache_path.exists():
        with open(cache_path, "rb") as f:
            return pickle.load(f)

    # ==============================
    # DETECT INPUT TYPE
    # ==============================

    latlon = extract_lat_lon_from_url(input_text)

    if latlon:
        point = latlon

    else:
        latlon = parse_lat_lon(input_text)
        if latlon:
            point = latlon
        else:
            try:
                point = ox.geocode(input_text)
            except:
                point = DEFAULT_POINT  # fallback

    # ==============================
    # LOAD GRAPH (FAST)
    # ==============================

    graph = ox.graph_from_point(
        point,
        dist=400,               # 🔥 small = fast + stable
        network_type="walk"
    )

    graph.remove_nodes_from(list(nx.isolates(graph)))

    # ==============================
    # BUILD NODES
    # ==============================

    nodes = {
        n: {
            "lat": float(data["y"]),
            "lon": float(data["x"])
        }
        for n, data in graph.nodes(data=True)
    }

    # ==============================
    # BUILD EDGES
    # ==============================

    edges = [
        (u, v, float(data.get("length", 1)))
        for u, v, data in graph.edges(data=True)
    ]

    # ==============================
    # SAVE CACHE
    # ==============================

    with open(cache_path, "wb") as f:
        pickle.dump((nodes, edges), f)

    return nodes, edges


# ==============================
# BBOX FILTER
# ==============================

def filter_by_bbox(nodes, edges, north, south, east, west):

    nodes_f = {
        k: v for k, v in nodes.items()
        if south <= v["lat"] <= north and west <= v["lon"] <= east
    }

    edges_f = [
        (u, v, w)
        for (u, v, w) in edges
        if u in nodes_f and v in nodes_f
    ]

    return nodes_f, edges_f