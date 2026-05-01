class CampusGraph:
    def __init__(self):
        # Adjacency list: {node: {neighbor: {distance, crowd, hazard}}}
        self.edges = {}

    def add_node(self, node):
        if node not in self.edges:
            self.edges[node] = {}

    def add_edge(self, u, v, distance):
        self.add_node(u)
        self.add_node(v)
        # Undirected graph: add edge in both directions
        self.edges[u][v] = {'distance': distance, 'crowd': 0, 'hazard': 0}
        self.edges[v][u] = {'distance': distance, 'crowd': 0, 'hazard': 0}

    def get_weight(self, u, v):
        """
        Calculates dynamic weight. 
        If hazard is severe (>= 10), the path is completely blocked.
        W = Distance + (Crowd * 2) + (Hazard * 10)
        """
        edge_data = self.edges[u][v]
        
        if edge_data['hazard'] >= 10:
            return float('inf') # Impassable
            
        weight = edge_data['distance'] + (edge_data['crowd'] * 2) + (edge_data['hazard'] * 10)
        return weight

    def update_edge_state(self, u, v, state_type, value):
        if u in self.edges and v in self.edges[u]:
            self.edges[u][v][state_type] = value
            self.edges[v][u][state_type] = value # Keep undirected sync