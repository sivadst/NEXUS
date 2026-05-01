import heapq

def dijkstra_optimal_path(graph, start, end):
    """
    Computes shortest path using a Min-Heap Priority Queue.
    Returns: (total_weight, [path_nodes])
    """
    # Priority Queue stores tuples of (cumulative_weight, current_node, path_history)
    pq = [(0, start, [start])]
    visited = set()

    while pq:
        # Min-Heap ensures we always pop the lowest weight path next
        current_weight, current_node, path = heapq.heappop(pq)

        # Target reached
        if current_node == end:
            return current_weight, path

        # Skip if already fully evaluated
        if current_node in visited:
            continue
            
        visited.add(current_node)

        # Explore neighbors
        for neighbor in graph.edges[current_node]:
            if neighbor not in visited:
                edge_weight = graph.get_weight(current_node, neighbor)
                
                # Only push to heap if the path is not blocked by severe hazards
                if edge_weight < float('inf'):
                    new_weight = current_weight + edge_weight
                    heapq.heappush(pq, (new_weight, neighbor, path + [neighbor]))

    # Target unreachable (all paths blocked)
    return float('inf'), []