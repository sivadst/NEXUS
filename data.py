# ==============================
# NEXUS - DATA MODULE
# ==============================

# Nodes (locations in campus)
# Format: "Location_Name": (x, y)  → coordinates just for reference/visual later

nodes = {
    "Main Gate": (0, 0),
    "Library": (2, 3),
    "Auditorium": (5, 5),
    "Hostel A": (1, 6),
    "Hostel B": (3, 7),
    "Mess": (4, 2),
    "Basketball Court": (6, 3),
    "Academic Block": (3, 4),
    "Parking": (1, 1),
    "Medical Center": (6, 6)
}


# Edges (connections between locations)
# Format: (node1, node2, distance)

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


# Crowd levels (initial values)
# Scale: 1 (low) → 5 (very high)

crowd = {
    "Main Gate": 2,
    "Library": 3,
    "Auditorium": 4,
    "Hostel A": 2,
    "Hostel B": 2,
    "Mess": 5,
    "Basketball Court": 2,
    "Academic Block": 4,
    "Parking": 1,
    "Medical Center": 1
}


# Hazard levels (0 = safe, higher = dangerous)
# Can be updated dynamically during simulation

hazard = {
    "Main Gate": 0,
    "Library": 0,
    "Auditorium": 0,
    "Hostel A": 0,
    "Hostel B": 0,
    "Mess": 0,
    "Basketball Court": 0,
    "Academic Block": 0,
    "Parking": 0,
    "Medical Center": 0
}


# ==============================
# CONFIG VALUES
# ==============================

# Weight multipliers (tune these later for behavior)
DISTANCE_WEIGHT = 1
CROWD_WEIGHT = 2
HAZARD_WEIGHT = 10