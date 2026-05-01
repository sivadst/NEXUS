"""
routing.py
----------
Dijkstra's algorithm implemented from scratch using Python's heapq
(a binary min-heap). No networkx shortcuts — pure algorithmic implementation.

The algorithm answers:
    "What is the lowest-cost path from source S to destination D,
     given the current graph weights?"

Time complexity:  O((V + E) log V)  — standard Dijkstra with a binary heap
Space complexity: O(V + E)

Key design decisions
---------------------
1.  Min-heap stores (cost, node_id) tuples. Python's heapq is a min-heap
    by default, so smallest cost is always at index 0.

2.  Lazy deletion: we never remove stale entries from the heap.
    Instead, we track `visited` and skip entries for already-settled nodes.
    This is standard practice because heap removal is O(n) while insertion
    is O(log n).

3.  Multi-exit support: the destination can be ANY exit node, not just one.
    We add a virtual "SAFE_ZONE" super-node connected to all exit nodes
    with 0-cost edges, then route to SAFE_ZONE. The actual exit node
    on the optimal path is reported.

4.  Path reconstruction uses a `came_from` dict that records, for each
    settled node, which node we arrived from. We trace back from destination
    to source to build the full path list.
"""

import heapq
from typing import Dict, List, Optional, Set, Tuple

from core.graph import EvacuationGraph, NodeId, INFINITY

# Virtual super-node identifier for multi-exit routing
SAFE_ZONE = "__SAFE_ZONE__"


# ─────────────────────────────────────────────────────────────────────────────
# Core Dijkstra implementation
# ─────────────────────────────────────────────────────────────────────────────

def dijkstra(
    adj: Dict[NodeId, List[Tuple[NodeId, float]]],
    source: NodeId,
    destination: NodeId,
) -> Tuple[float, List[NodeId]]:
    """
    Run Dijkstra's algorithm on an adjacency list.

    Parameters
    ----------
    adj         : adjacency list — {node: [(neighbor, weight), ...]}
    source      : starting node id
    destination : target node id

    Returns
    -------
    (total_cost, path)
        total_cost : float — sum of edge weights along optimal path
                     Returns INFINITY if no path exists.
        path       : list of node ids from source to destination (inclusive)
                     Returns [] if no path exists.
    """
    # ── Step 1: Initialize data structures ────────────────────────────────────

    # dist[v] = best known cost to reach v from source
    # Start with INFINITY for everything; source costs 0
    dist: Dict[NodeId, float] = {node: INFINITY for node in adj}
    dist[source] = 0.0

    # came_from[v] = which node we settled v from (for path reconstruction)
    came_from: Dict[NodeId, Optional[NodeId]] = {node: None for node in adj}

    # visited = set of nodes whose shortest path is finalized
    visited: Set[NodeId] = set()

    # Min-heap priority queue: entries are (cost, node_id)
    # We use a list and maintain heap property via heapq functions.
    heap: List[Tuple[float, NodeId]] = []
    heapq.heappush(heap, (0.0, source))

    # ── Step 2: Main Dijkstra loop ─────────────────────────────────────────────
    while heap:

        # Extract the node with minimum cost (O(log n) heap operation)
        current_cost, current_node = heapq.heappop(heap)

        # Lazy deletion check: if we've already finalized this node, skip
        if current_node in visited:
            continue

        # Mark current node as settled — its shortest distance is final
        visited.add(current_node)

        # Early exit: once we settle the destination, we're done
        if current_node == destination:
            break

        # ── Step 3: Relax all outgoing edges from current_node ────────────────
        for neighbor, edge_weight in adj.get(current_node, []):

            # Skip already-settled neighbors
            if neighbor in visited:
                continue

            # Skip infinite-weight edges (blocked paths)
            if edge_weight >= INFINITY:
                continue

            # Compute candidate cost via current_node
            candidate_cost = current_cost + edge_weight

            # Relaxation: update if we found a cheaper path to neighbor
            if candidate_cost < dist.get(neighbor, INFINITY):
                dist[neighbor]      = candidate_cost
                came_from[neighbor] = current_node
                # Push updated entry to heap (old entry becomes stale, lazy-deleted)
                heapq.heappush(heap, (candidate_cost, neighbor))

    # ── Step 4: Check reachability ────────────────────────────────────────────
    final_cost = dist.get(destination, INFINITY)
    if final_cost == INFINITY:
        return INFINITY, []   # No path exists

    # ── Step 5: Reconstruct path by tracing came_from backwards ───────────────
    path: List[NodeId] = []
    node = destination
    while node is not None:
        path.append(node)
        node = came_from.get(node)
    path.reverse()   # came_from gives us destination→source; flip it

    return final_cost, path


# ─────────────────────────────────────────────────────────────────────────────
# High-level routing API
# ─────────────────────────────────────────────────────────────────────────────

def find_evacuation_route(
    graph: EvacuationGraph,
    source: NodeId,
    destination: NodeId,
) -> dict:
    """
    Find the optimal evacuation route from source to destination
    using the current graph state (crowd + hazards applied).

    If destination is a specific room, routes directly to it.
    If destination is "nearest_exit", routes to the cheapest exit.

    Parameters
    ----------
    graph       : EvacuationGraph instance with current weights
    source      : starting node
    destination : target node OR "nearest_exit"

    Returns
    -------
    dict with keys:
        found        : bool — whether a path was found
        path         : list of node ids
        total_cost   : float
        path_labels  : list of human-readable node names
        hops         : number of intermediate nodes
        blocked_on_path : list of blocked nodes that were avoided
        edge_details : list of dicts with per-edge breakdown
    """
    if source not in graph.nodes:
        return _no_route_result(f"Source node '{source}' not found in graph.")

    if destination not in graph.nodes and destination != "nearest_exit":
        return _no_route_result(f"Destination node '{destination}' not found.")

    if source in graph.blocked_nodes:
        return _no_route_result(f"Source node '{source}' is currently blocked/hazardous.")

    # ── Build augmented adjacency list with SAFE_ZONE super-node ─────────────
    # We copy the current adj and add SAFE_ZONE → 0-cost edges from all exits
    aug_adj: Dict[NodeId, List[Tuple[NodeId, float]]] = {}
    for node, neighbors in graph.adj.items():
        aug_adj[node] = list(neighbors)

    if destination == "nearest_exit":
        # Add virtual SAFE_ZONE node connected to all unblocked exits
        aug_adj[SAFE_ZONE] = []
        for exit_node in graph.exit_nodes:
            if exit_node not in graph.blocked_nodes:
                aug_adj.setdefault(exit_node, []).append((SAFE_ZONE, 0.0))
        actual_destination = SAFE_ZONE
    else:
        actual_destination = destination

    # ── Run Dijkstra ──────────────────────────────────────────────────────────
    total_cost, path = dijkstra(aug_adj, source, actual_destination)

    if not path or total_cost == INFINITY:
        return _no_route_result(
            f"No viable route from '{source}' to '{destination}'. "
            "All paths may be blocked or hazardous."
        )

    # Remove the virtual SAFE_ZONE node from reported path
    if path and path[-1] == SAFE_ZONE:
        path = path[:-1]

    # ── Build detailed result ─────────────────────────────────────────────────
    path_labels = [graph.nodes[nid]["label"] for nid in path if nid in graph.nodes]

    # Per-edge breakdown for display
    edge_details = []
    for i in range(len(path) - 1):
        u, v = path[i], path[i + 1]
        w    = graph.get_edge_weight(u, v)

        # Find base distance from raw edges (for breakdown display)
        base_dist = _get_base_distance(graph, u, v)
        crowd_pen = (graph._crowd_penalty(u) + graph._crowd_penalty(v)) / 2
        haz_pen   = (graph._hazard_penalty(u) + graph._hazard_penalty(v)) / 2

        edge_details.append({
            "from":         u,
            "to":           v,
            "from_label":   graph.nodes.get(u, {}).get("label", u),
            "to_label":     graph.nodes.get(v, {}).get("label", v),
            "weight":       round(w, 2),
            "base_dist":    base_dist,
            "crowd_pen":    round(crowd_pen, 2),
            "hazard_pen":   round(haz_pen, 2),
            "is_stairwell": graph.nodes.get(v, {}).get("type") == "stairwell",
        })

    return {
        "found":            True,
        "path":             path,
        "total_cost":       round(total_cost, 2),
        "path_labels":      path_labels,
        "hops":             len(path) - 1,
        "edge_details":     edge_details,
        "error":            None,
    }


def find_all_routes(
    graph: EvacuationGraph,
    source: NodeId,
    top_k: int = 3,
) -> List[dict]:
    """
    Find the top-k cheapest routes from source to ANY exit.
    Uses Yen's k-shortest-paths concept simplified:
    we iteratively find shortest path, block it, and repeat.

    Parameters
    ----------
    graph  : current graph state
    source : starting node
    top_k  : how many alternative routes to return

    Returns
    -------
    List of route dicts (same format as find_evacuation_route), ranked by cost.
    """
    results = []
    blocked_backup = set(graph.blocked_nodes)

    # Temporarily block previously found paths to force alternatives
    found_paths: List[List[NodeId]] = []

    for k in range(top_k):
        # Temporarily block intermediate nodes of previously found paths
        temp_blocked: Set[NodeId] = set()
        if k > 0 and found_paths:
            # Block the second-to-last node of the best path found so far
            # (this forces the algorithm to diverge earlier)
            for prev_path in found_paths:
                if len(prev_path) > 2:
                    temp_blocked.add(prev_path[1])   # first junction

        original_blocked = graph.blocked_nodes
        graph.blocked_nodes = blocked_backup | temp_blocked
        graph.recompute_weights()

        route = find_evacuation_route(graph, source, "nearest_exit")

        # Restore
        graph.blocked_nodes = original_blocked
        graph.recompute_weights()

        if route["found"] and route["path"] not in found_paths:
            route["rank"] = k + 1
            results.append(route)
            found_paths.append(route["path"])

    return results


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _no_route_result(error_message: str) -> dict:
    return {
        "found":        False,
        "path":         [],
        "total_cost":   INFINITY,
        "path_labels":  [],
        "hops":         0,
        "edge_details": [],
        "error":        error_message,
    }


def _get_base_distance(graph: EvacuationGraph, u: NodeId, v: NodeId) -> float:
    """Look up the raw base distance for edge u-v from EDGES_RAW."""
    for (eu, ev, dist, _) in graph.edges_raw:
        if (eu == u and ev == v) or (eu == v and ev == u):
            return dist
    return 0.0