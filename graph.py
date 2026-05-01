# ==============================
# NEXUS - GRAPH MODULE
# ==============================

def calculate_weight(node1, node2, base_distance, crowd, hazard):
    """
    Dynamic weight calculation
    weight = distance + crowd + hazard
    """

    # Average crowd of both nodes
    crowd_factor = (crowd[node1] + crowd[node2]) / 2

    # Hazard penalty (if any node is dangerous)
    hazard_factor = hazard[node1] + hazard[node2]

    # Final weight
    weight = base_distance + crowd_factor + (hazard_factor * 10)

    return weight


def build_graph(nodes, edges, crowd, hazard):
    """
    Build adjacency list graph
    """

    graph = {}

    # Initialize graph
    for node in nodes:
        graph[node] = []

    # Add edges
    for node1, node2, distance in edges:
        weight = calculate_weight(node1, node2, distance, crowd, hazard)

        # Undirected graph (two-way)
        graph[node1].append((node2, weight))
        graph[node2].append((node1, weight))

    return graph