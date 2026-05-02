# ==============================
# NEXUS - REALISTIC SRM AP DATA
# ==============================

nodes = {
    "Main Gate": (16.44185, 80.62090),
    "Parking": (16.44160, 80.62040),
    "Library": (16.44260, 80.62190),
    "Academic Block": (16.44310, 80.62170),
    "Auditorium": (16.44380, 80.62280),
    "Mess": (16.44220, 80.62080),
    "Basketball Court": (16.44350, 80.62050),
    "Hostel A": (16.44420, 80.62130),
    "Hostel B": (16.44500, 80.62220),
    "Medical Center": (16.44460, 80.62320)
}

edges = [
    ("Main Gate", "Parking", 2),
    ("Parking", "Library", 3),
    ("Library", "Academic Block", 2),
    ("Academic Block", "Auditorium", 3),
    ("Academic Block", "Mess", 2),
    ("Mess", "Basketball Court", 2),
    ("Hostel A", "Academic Block", 3),
    ("Hostel B", "Academic Block", 3),
    ("Hostel A", "Hostel B", 2),
    ("Auditorium", "Medical Center", 2),
    ("Basketball Court", "Medical Center", 3)
]

crowd = {
    "Main Gate": 3,
    "Library": 4,
    "Auditorium": 5,
    "Hostel A": 2,
    "Hostel B": 2,
    "Mess": 5,
    "Basketball Court": 2,
    "Academic Block": 4,
    "Parking": 2,
    "Medical Center": 1
}

hazard = {node: 0 for node in nodes}


# ===== FUNCTIONS =====

def get_nodes():
    return list(nodes.keys())

def get_edges():
    return edges

def get_node_map():
    return nodes

def initial_crowd_levels():
    return crowd.copy()

def initial_edge_hazard_levels():
    return {}

def initial_node_hazard_levels():
    return hazard.copy()

def edge_key(a, b):
    return tuple(sorted([a, b]))