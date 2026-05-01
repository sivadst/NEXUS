# Sample campus dataset
# Format: (Source, Destination, Base Distance)

CAMPUS_EDGES = [
    ("Main_Entrance", "Lobby", 10),
    ("Lobby", "Hallway_A", 15),
    ("Lobby", "Hallway_B", 20),
    ("Hallway_A", "Cafeteria", 25),
    ("Hallway_A", "Library", 30),
    ("Hallway_B", "Lab_1", 15),
    ("Hallway_B", "Stairwell", 10),
    ("Library", "Emergency_Exit_West", 40),
    ("Cafeteria", "Stairwell", 20),
    ("Lab_1", "Stairwell", 5),
    ("Stairwell", "Emergency_Exit_East", 50)
]

NODES = list(set([u for u, v, d in CAMPUS_EDGES] + [v for u, v, d in CAMPUS_EDGES]))