"""
NEXUS Routing Engine — Utilities
Graph cache, structured logging, and shared helpers.
"""

from __future__ import annotations

import hashlib
import logging
import time
from collections import OrderedDict
from dataclasses import dataclass, field
from typing import Any, Optional

import networkx as nx

# ── LOGGING ───────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("nexus")


# ── GRAPH CACHE ───────────────────────────────────────────────────────────────

@dataclass
class CachedGraph:
    graph_id: str
    G: nx.MultiDiGraph          # projected OSMnx graph
    lat: float
    lon: float
    radius: int
    network_type: str
    node_count: int
    edge_count: int
    bbox: dict[str, float]
    created_at: float = field(default_factory=time.time)
    hits: int = 0

    @property
    def age_seconds(self) -> float:
        return time.time() - self.created_at


class GraphCache:
    """
    LRU in-memory cache for OSMnx graphs.
    Keyed by a deterministic hash of (lat, lon, radius, network_type).
    Evicts least-recently-used entries when capacity is exceeded.
    """

    def __init__(self, max_size: int = 20, ttl_seconds: int = 3600):
        self._store: OrderedDict[str, CachedGraph] = OrderedDict()
        self.max_size = max_size
        self.ttl = ttl_seconds

    # ── public API ────────────────────────────────────────────────────────────

    def make_key(self, lat: float, lon: float, radius: int, network_type: str) -> str:
        raw = f"{lat:.5f}:{lon:.5f}:{radius}:{network_type}"
        return hashlib.sha256(raw.encode()).hexdigest()[:16]

    def get(self, graph_id: str) -> Optional[CachedGraph]:
        entry = self._store.get(graph_id)
        if entry is None:
            return None
        if entry.age_seconds > self.ttl:
            logger.info("Cache TTL expired for %s — evicting", graph_id)
            del self._store[graph_id]
            return None
        # Move to end (most recently used)
        self._store.move_to_end(graph_id)
        entry.hits += 1
        return entry

    def put(self, entry: CachedGraph) -> None:
        if entry.graph_id in self._store:
            self._store.move_to_end(entry.graph_id)
            self._store[entry.graph_id] = entry
            return
        if len(self._store) >= self.max_size:
            evicted_key, _ = self._store.popitem(last=False)
            logger.info("Cache full — evicting LRU graph %s", evicted_key)
        self._store[entry.graph_id] = entry
        logger.info(
            "Cached graph %s (%d nodes, %d edges)",
            entry.graph_id, entry.node_count, entry.edge_count,
        )

    def size(self) -> int:
        return len(self._store)

    def stats(self) -> list[dict[str, Any]]:
        return [
            {
                "graph_id": e.graph_id,
                "centre": {"lat": e.lat, "lon": e.lon},
                "radius": e.radius,
                "nodes": e.node_count,
                "edges": e.edge_count,
                "age_s": round(e.age_seconds, 1),
                "hits": e.hits,
            }
            for e in self._store.values()
        ]


# ── SINGLETON CACHE ───────────────────────────────────────────────────────────

graph_cache = GraphCache(max_size=20, ttl_seconds=3600)


# ── GEOMETRY HELPERS ─────────────────────────────────────────────────────────

def haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Return distance in metres between two lat/lon points."""
    import math
    R = 6_371_000
    φ1, φ2 = math.radians(lat1), math.radians(lat2)
    dφ = math.radians(lat2 - lat1)
    dλ = math.radians(lon2 - lon1)
    a = math.sin(dφ / 2) ** 2 + math.cos(φ1) * math.cos(φ2) * math.sin(dλ / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def bbox_of_graph(G: nx.MultiDiGraph) -> dict[str, float]:
    lats = [data["y"] for _, data in G.nodes(data=True)]
    lons = [data["x"] for _, data in G.nodes(data=True)]
    return {
        "north": max(lats),
        "south": min(lats),
        "east": max(lons),
        "west": min(lons),
    }


# ── TIMER CONTEXT MANAGER ────────────────────────────────────────────────────

class Timer:
    def __enter__(self):
        self._start = time.perf_counter()
        return self

    def __exit__(self, *_):
        self.elapsed_ms = (time.perf_counter() - self._start) * 1000

    @property
    def ms(self) -> float:
        return round(self.elapsed_ms, 3)
