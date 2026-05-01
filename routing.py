# ==============================
# NEXUS - ROUTING MODULE
# ==============================

import heapq


def dijkstra(graph, start, end):
    """
    Dijkstra's Algorithm using Min-Heap (Priority Queue)
    Returns shortest path and total cost
    """

    # Priority queue → (cost, node, path)
    pq = [(0, start, [])]

    # Visited nodes
    visited = set()

    # Minimum cost to each node
    min_cost = {node: float('inf') for node in graph}
    min_cost[start] = 0

    while pq:
        current_cost, current_node, path = heapq.heappop(pq)

        # Skip if already visited
        if current_node in visited:
            continue

        # Mark visited
        visited.add(current_node)

        # Update path
        path = path + [current_node]

        # If destination reached
        if current_node == end:
            return path, current_cost

        # Explore neighbors
        for neighbor, weight in graph[current_node]:
            if neighbor not in visited:
                new_cost = current_cost + weight

                # Relaxation step
                if new_cost < min_cost[neighbor]:
                    min_cost[neighbor] = new_cost
                    heapq.heappush(pq, (new_cost, neighbor, path))

    return None, float('inf')