"""
NEXUS Routing Engine — Graph Loader
Fetches road networks via OSMnx, cleans them, and serialises
them to the wire format consumed by the frontend.
"""

from __future__ import annotations

import hashlib
import logging
from typing import Tuple

import networkx as nx
import osmnx as ox

from models import EdgeOut, FilterBBoxResponse, LoadMapResponse, NodeOut
from utils import CachedGraph, Timer, bbox_of_graph, graph_cache, haversine_m, logger

# ── OSMnx global settings ────────────────────────────────────────────────────
ox.settings.log_console = False
ox.settings.use_cache = True          # OSMnx's own disk cache (separate layer)
ox.settings.timeout = 30


# ── INTERNAL HELPERS ─────────────────────────────────────────────────────────

def _clean_graph(G: nx.MultiDiGraph) -> nx.MultiDiGraph:
    """
    Pipeline:
    1. Keep only the largest strongly-connected component so every node
       is reachable from every other node (guarantees routing works).
    2. Add 'length' attribute to any edge missing it (rare but possible).
    3. Remove self-loops.
    """
    # Largest strongly connected component
    if nx.is_empty(G):
        raise ValueError("Graph has no edges after download")

    components = [c for c in nx.strongly_connected_components(G)]
    if not components:
        raise ValueError("No strongly connected components found")

    largest = max(components, key=len)
    G = G.subgraph(largest).copy()

    # Ensure all edges have a numeric 'length' (metres)
    for u, v, data in G.edges(data=True):
        if "length" not in data or data["length"] is None:
            nu = G.nodes[u]
            nv = G.nodes[v]
            data["length"] = haversine_m(nu["y"], nu["x"], nv["y"], nv["x"])

    # Remove self-loops
    G.remove_edges_from(list(nx.selfloop_edges(G)))

    return G


def _serialise_graph(G: nx.MultiDiGraph) -> Tuple[list[NodeOut], list[EdgeOut]]:
    """Convert NetworkX graph to JSON-serialisable node/edge lists."""
    nodes: list[NodeOut] = [
        NodeOut(id=node_id, lat=data["y"], lon=data["x"])
        for node_id, data in G.nodes(data=True)
    ]

    seen_edges: set[tuple[int, int]] = set()
    edges: list[EdgeOut] = []

    for u, v, data in G.edges(data=True):
        key = (min(u, v), max(u, v))
        if key in seen_edges:
            continue
        seen_edges.add(key)
        length = float(data.get("length", 1.0))
        edges.append(EdgeOut(u=u, v=v, weight=round(length, 3)))

    return nodes, edges


# ── PUBLIC API ────────────────────────────────────────────────────────────────

def load_graph(lat: float, lon: float, radius: int, network_type: str) -> LoadMapResponse:
    """
    Download (or retrieve from cache) the road network around the given point.
    Returns a fully populated LoadMapResponse.
    """
    graph_id = graph_cache.make_key(lat, lon, radius, network_type)

    # ── Cache hit ────────────────────────────────────────────────────────────
    cached = graph_cache.get(graph_id)
    if cached is not None:
        logger.info("Cache hit for graph %s (hits=%d)", graph_id, cached.hits)
        nodes, edges = _serialise_graph(cached.G)
        return LoadMapResponse(
            graph_id=graph_id,
            node_count=cached.node_count,
            edge_count=cached.edge_count,
            nodes=nodes,
            edges=edges,
            bbox=cached.bbox,
            centre={"lat": lat, "lon": lon},
            cached=True,
        )

    # ── Cache miss — download via OSMnx ──────────────────────────────────────
    logger.info(
        "Downloading OSM graph: centre=(%.5f,%.5f) radius=%dm type=%s",
        lat, lon, radius, network_type,
    )

    with Timer() as t:
        try:
            G_raw: nx.MultiDiGraph = ox.graph_from_point(
                (lat, lon),
                dist=radius,
                network_type=network_type,
                simplify=True,
                retain_all=False,
            )
        except Exception as exc:
            logger.error("OSMnx download failed: %s", exc)
            raise RuntimeError(f"Failed to fetch road network: {exc}") from exc

    logger.info("OSMnx download finished in %.0f ms", t.ms)

    # Clean & validate
    G = _clean_graph(G_raw)

    node_count = G.number_of_nodes()
    edge_count = G.number_of_edges()
    bbox = bbox_of_graph(G)

    # Store in cache
    entry = CachedGraph(
        graph_id=graph_id,
        G=G,
        lat=lat,
        lon=lon,
        radius=radius,
        network_type=network_type,
        node_count=node_count,
        edge_count=edge_count,
        bbox=bbox,
    )
    graph_cache.put(entry)

    nodes, edges = _serialise_graph(G)

    return LoadMapResponse(
        graph_id=graph_id,
        node_count=node_count,
        edge_count=edge_count,
        nodes=nodes,
        edges=edges,
        bbox=bbox,
        centre={"lat": lat, "lon": lon},
        cached=False,
    )


def filter_bbox(
    graph_id: str,
    north: float,
    south: float,
    east: float,
    west: float,
) -> FilterBBoxResponse:
    """
    Extract the sub-graph that lies within the given bounding box.
    Returns a new graph_id for the sub-graph (also cached).
    """
    cached = graph_cache.get(graph_id)
    if cached is None:
        raise KeyError(f"Graph '{graph_id}' not found in cache. Reload the map first.")

    G = cached.G

    # Filter nodes within bbox
    nodes_in_bbox = [
        n for n, data in G.nodes(data=True)
        if south <= data["y"] <= north and west <= data["x"] <= east
    ]

    if len(nodes_in_bbox) < 2:
        raise ValueError("Bounding box contains fewer than 2 nodes — expand the selection.")

    sub_G: nx.MultiDiGraph = G.subgraph(nodes_in_bbox).copy()

    # Derive a stable sub-graph id
    raw = f"{graph_id}:{north:.5f}:{south:.5f}:{east:.5f}:{west:.5f}"
    sub_id = "bbox_" + hashlib.sha256(raw.encode()).hexdigest()[:12]

    node_count = sub_G.number_of_nodes()
    edge_count = sub_G.number_of_edges()

    # Cache the sub-graph so /route can use it
    sub_entry = CachedGraph(
        graph_id=sub_id,
        G=sub_G,
        lat=(north + south) / 2,
        lon=(east + west) / 2,
        radius=0,
        network_type=cached.network_type,
        node_count=node_count,
        edge_count=edge_count,
        bbox={"north": north, "south": south, "east": east, "west": west},
    )
    graph_cache.put(sub_entry)

    nodes, edges = _serialise_graph(sub_G)

    logger.info(
        "BBox filter: %d → %d nodes, %d edges → sub_id=%s",
        G.number_of_nodes(), node_count, edge_count, sub_id,
    )

    return FilterBBoxResponse(
        graph_id=sub_id,
        node_count=node_count,
        edge_count=edge_count,
        nodes=nodes,
        edges=edges,
    )
