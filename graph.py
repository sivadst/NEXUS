
import math
from typing import Dict, List, Tuple, Set, Optional
 
# ── Weight tuning constants ────────────────────────────────────────────────────
CROWD_WEIGHT_MULTIPLIER = 50   # max crowd penalty in meters-equivalent
HAZARD_WEIGHT_MULTIPLIER = 30  # per hazard-level-unit penalty
WIDTH_BONUS_FACTOR = 3         # reduction per width unit above 1
INFINITY = float('inf')
 
# ── Type aliases ───────────────────────────────────────────────────────────────
NodeId   = str
Weight   = float
AdjList  = Dict[NodeId, List[Tuple[NodeId, Weight]]]   # node → [(neighbor, weight)]
 
 
class EvacuationGraph:
    """
    Represents the campus as an adjacency-list weighted graph.
 
    Attributes
    ----------
    nodes        : raw node metadata dict
    edges_raw    : list of (from, to, base_dist, width) tuples
    crowd        : {node_id: current_crowd_count}
    hazard_level : {node_id: 0–10 hazard score}
    blocked_nodes: set of node ids completely impassable
    hazard_edges : {(u,v): override_weight}  — direct edge hazard overrides
    adj          : computed adjacency list (rebuilt on each recompute)
    """
 
    def __init__(self, nodes: dict, edges_raw: list, exit_nodes: Set[NodeId]):
        self.nodes         = nodes
        self.edges_raw     = edges_raw
        self.exit_nodes    = exit_nodes
 
        # Dynamic state — updated by simulation
        self.crowd: Dict[NodeId, int]         = {nid: 0 for nid in nodes}
        self.hazard_level: Dict[NodeId, float] = {nid: 0.0 for nid in nodes}
        self.blocked_nodes: Set[NodeId]        = set()
        self.hazard_edges: Dict[Tuple, float]  = {}   # edge-level overrides
 
        # Build initial adjacency list
        self.adj: AdjList = {}
        self._init_adj()
        self.recompute_weights()
 
    # ──────────────────────────────────────────────────────────────────────────
    # Private helpers
    # ──────────────────────────────────────────────────────────────────────────
 
    def _init_adj(self):
        """Create empty adjacency list slots for every node."""
        for nid in self.nodes:
            self.adj[nid] = []
 
    def _crowd_penalty(self, node_id: NodeId) -> float:
        """
        Penalty based on how full a node is.
        Ranges from 0 (empty) to CROWD_WEIGHT_MULTIPLIER (at/over capacity).
        Above capacity → penalty spikes sharply.
        """
        cap   = self.nodes[node_id].get("capacity", 30)
        count = self.crowd.get(node_id, 0)
        ratio = count / max(cap, 1)
 
        if ratio <= 0:
            return 0.0
        elif ratio < 1.0:
            # Smooth quadratic growth up to capacity
            return ratio ** 2 * CROWD_WEIGHT_MULTIPLIER
        else:
            # Beyond capacity: exponential spike — strongly discourages this path
            return CROWD_WEIGHT_MULTIPLIER * math.exp(ratio - 1)
 
    def _hazard_penalty(self, node_id: NodeId) -> float:
        """Linear penalty based on node hazard level (0–10 scale)."""
        return self.hazard_level.get(node_id, 0.0) * HAZARD_WEIGHT_MULTIPLIER
 
    def _width_bonus(self, width_factor: int) -> float:
        """
        Wider paths are faster to traverse.
        width_factor=1 → 0 bonus, =2 → 3 reduction, =3 → 6 reduction.
        """
        return max(0, (width_factor - 1)) * WIDTH_BONUS_FACTOR
 
    def _compute_edge_weight(
        self,
        u: NodeId,
        v: NodeId,
        base_distance: float,
        width_factor: int,
    ) -> float:
        """
        Compute the effective traversal cost for edge u→v.
 
        Steps:
        1. Check if edge is explicitly overridden (hazard_edges)
        2. Check if either endpoint is blocked
        3. Apply crowd + hazard penalties from BOTH endpoints (averaged)
        4. Apply width bonus
        5. Clamp minimum to base_distance (can't be faster than raw distance)
        """
        # Step 1: explicit edge override (e.g., fire directly on a corridor)
        key_uv = (u, v)
        key_vu = (v, u)
        if key_uv in self.hazard_edges:
            return self.hazard_edges[key_uv]
        if key_vu in self.hazard_edges:
            return self.hazard_edges[key_vu]
 
        # Step 2: blocked node → impassable
        if u in self.blocked_nodes or v in self.blocked_nodes:
            return INFINITY
 
        # Step 3: node penalties (average of both endpoints avoids double-counting)
        crowd_pen  = (self._crowd_penalty(u)  + self._crowd_penalty(v))  / 2
        hazard_pen = (self._hazard_penalty(u) + self._hazard_penalty(v)) / 2
 
        # Step 4: width bonus
        width_bon = self._width_bonus(width_factor)
 
        # Step 5: assemble and clamp
        weight = base_distance + crowd_pen + hazard_pen - width_bon
        return max(weight, base_distance)   # never faster than raw distance
 
    # ──────────────────────────────────────────────────────────────────────────
    # Public API
    # ──────────────────────────────────────────────────────────────────────────
 
    def recompute_weights(self):
        """
        Rebuild the entire adjacency list from scratch using current
        crowd, hazard, blocked, and hazard_edge state.
        Call this after ANY state change before running Dijkstra.
        """
        # Reset adjacency list
        for nid in self.adj:
            self.adj[nid] = []
 
        for (u, v, base_dist, width) in self.edges_raw:
            w_uv = self._compute_edge_weight(u, v, base_dist, width)
            w_vu = self._compute_edge_weight(v, u, base_dist, width)
 
            # Only add finite-weight edges
            if w_uv < INFINITY:
                self.adj[u].append((v, w_uv))
            if w_vu < INFINITY:
                self.adj[v].append((u, w_vu))
 
    def apply_hazard_scenario(self, scenario: dict):
        """
        Apply a named hazard scenario dict with keys:
          blocked_nodes : set of node ids
          hazard_edges  : dict {(u,v): weight}
        Recomputes the graph after applying.
        """
        self.blocked_nodes = set(scenario.get("blocked_nodes", set()))
        self.hazard_edges  = dict(scenario.get("hazard_edges", {}))
 
        # Raise hazard_level for blocked nodes to maximum
        for nid in self.nodes:
            if nid in self.blocked_nodes:
                self.hazard_level[nid] = 10.0
            else:
                self.hazard_level[nid] = 0.0
 
        self.recompute_weights()
 
    def update_crowd(self, crowd_snapshot: Dict[NodeId, int]):
        """
        Accept a snapshot of crowd counts per node.
        Recomputes the graph after updating.
        """
        for nid, count in crowd_snapshot.items():
            if nid in self.crowd:
                self.crowd[nid] = count
        self.recompute_weights()
 
    def get_edge_weight(self, u: NodeId, v: NodeId) -> float:
        """Return current effective weight of edge u→v, or INFINITY."""
        for (neighbor, weight) in self.adj.get(u, []):
            if neighbor == v:
                return weight
        return INFINITY
 
    def get_node_status(self, node_id: NodeId) -> dict:
        """Return a human-readable status dict for a node."""
        cap   = self.nodes[node_id].get("capacity", 30)
        count = self.crowd.get(node_id, 0)
        return {
            "label":        self.nodes[node_id]["label"],
            "blocked":      node_id in self.blocked_nodes,
            "crowd":        count,
            "capacity":     cap,
            "occupancy_pct": round(count / max(cap, 1) * 100, 1),
            "hazard_level": self.hazard_level.get(node_id, 0.0),
            "floor":        self.nodes[node_id]["floor"],
            "type":         self.nodes[node_id]["type"],
        }
 
    def all_edges_with_weights(self) -> List[Tuple[NodeId, NodeId, float]]:
        """Return flat list of (u, v, weight) for all current finite edges."""
        result = []
        seen   = set()
        for u, neighbors in self.adj.items():
            for v, w in neighbors:
                key = tuple(sorted([u, v]))
                if key not in seen:
                    result.append((u, v, w))
                    seen.add(key)
        return result
 