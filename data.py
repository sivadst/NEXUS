"""
campus_data.py
--------------
Static data model for the NEXUS campus graph.
Nodes represent rooms/locations; edges represent paths between them.

Each NODE has:
  - id: unique string identifier
  - label: human-readable name
  - type: 'room' | 'exit' | 'stairwell' | 'corridor' | 'assembly'
  - floor: integer floor number
  - capacity: max people this node can hold comfortably
  - x, y: layout coordinates for visualization (0–100 scale)

Each EDGE has:
  - from, to: node ids (bidirectional unless noted)
  - base_distance: raw path length in meters
  - width: corridor width (narrow=1, normal=2, wide=3) — affects crowd flow
"""

NODES = {
    # ── GROUND FLOOR ──────────────────────────────────────────────────────────
    "main_entrance":    {"label": "Main Entrance",      "type": "exit",       "floor": 0, "capacity": 80,  "x": 50, "y": 95},
    "lobby":            {"label": "Lobby",              "type": "corridor",   "floor": 0, "capacity": 60,  "x": 50, "y": 82},
    "reception":        {"label": "Reception Desk",     "type": "room",       "floor": 0, "capacity": 20,  "x": 38, "y": 82},
    "cafeteria":        {"label": "Cafeteria",          "type": "room",       "floor": 0, "capacity": 150, "x": 20, "y": 70},
    "g_corridor_w":     {"label": "G West Corridor",   "type": "corridor",   "floor": 0, "capacity": 40,  "x": 30, "y": 70},
    "g_corridor_e":     {"label": "G East Corridor",   "type": "corridor",   "floor": 0, "capacity": 40,  "x": 70, "y": 70},
    "lab_101":          {"label": "Lab 101",            "type": "room",       "floor": 0, "capacity": 30,  "x": 15, "y": 55},
    "lab_102":          {"label": "Lab 102",            "type": "room",       "floor": 0, "capacity": 30,  "x": 85, "y": 55},
    "server_room":      {"label": "Server Room",        "type": "room",       "floor": 0, "capacity": 10,  "x": 85, "y": 70},
    "stair_g_w":        {"label": "Stairwell West G",  "type": "stairwell",  "floor": 0, "capacity": 30,  "x": 10, "y": 70},
    "stair_g_e":        {"label": "Stairwell East G",  "type": "stairwell",  "floor": 0, "capacity": 30,  "x": 90, "y": 70},
    "elevator_g":       {"label": "Elevator (G)",      "type": "corridor",   "floor": 0, "capacity": 8,   "x": 50, "y": 70},
    "exit_west":        {"label": "West Emergency Exit","type": "exit",       "floor": 0, "capacity": 50,  "x": 5,  "y": 55},
    "exit_east":        {"label": "East Emergency Exit","type": "exit",       "floor": 0, "capacity": 50,  "x": 95, "y": 55},
    "assembly_point":   {"label": "Assembly Point",    "type": "assembly",   "floor": 0, "capacity": 500, "x": 50, "y": 100},

    # ── FLOOR 1 ───────────────────────────────────────────────────────────────
    "f1_corridor_main": {"label": "F1 Main Corridor",  "type": "corridor",   "floor": 1, "capacity": 50,  "x": 50, "y": 50},
    "f1_corridor_w":    {"label": "F1 West Corridor",  "type": "corridor",   "floor": 1, "capacity": 40,  "x": 30, "y": 50},
    "f1_corridor_e":    {"label": "F1 East Corridor",  "type": "corridor",   "floor": 1, "capacity": 40,  "x": 70, "y": 50},
    "classroom_201":    {"label": "Classroom 201",     "type": "room",       "floor": 1, "capacity": 40,  "x": 15, "y": 40},
    "classroom_202":    {"label": "Classroom 202",     "type": "room",       "floor": 1, "capacity": 40,  "x": 30, "y": 35},
    "classroom_203":    {"label": "Classroom 203",     "type": "room",       "floor": 1, "capacity": 40,  "x": 50, "y": 35},
    "classroom_204":    {"label": "Classroom 204",     "type": "room",       "floor": 1, "capacity": 40,  "x": 70, "y": 35},
    "classroom_205":    {"label": "Classroom 205",     "type": "room",       "floor": 1, "capacity": 40,  "x": 85, "y": 40},
    "faculty_lounge":   {"label": "Faculty Lounge",    "type": "room",       "floor": 1, "capacity": 25,  "x": 50, "y": 45},
    "restroom_f1":      {"label": "Restrooms F1",      "type": "room",       "floor": 1, "capacity": 15,  "x": 60, "y": 45},
    "stair_f1_w":       {"label": "Stairwell West F1", "type": "stairwell",  "floor": 1, "capacity": 30,  "x": 10, "y": 50},
    "stair_f1_e":       {"label": "Stairwell East F1", "type": "stairwell",  "floor": 1, "capacity": 30,  "x": 90, "y": 50},
    "elevator_f1":      {"label": "Elevator (F1)",     "type": "corridor",   "floor": 1, "capacity": 8,   "x": 50, "y": 57},

    # ── FLOOR 2 ───────────────────────────────────────────────────────────────
    "f2_corridor_main": {"label": "F2 Main Corridor",  "type": "corridor",   "floor": 2, "capacity": 50,  "x": 50, "y": 25},
    "f2_corridor_w":    {"label": "F2 West Corridor",  "type": "corridor",   "floor": 2, "capacity": 40,  "x": 30, "y": 25},
    "f2_corridor_e":    {"label": "F2 East Corridor",  "type": "corridor",   "floor": 2, "capacity": 40,  "x": 70, "y": 25},
    "office_301":       {"label": "Office 301",        "type": "room",       "floor": 2, "capacity": 15,  "x": 15, "y": 15},
    "office_302":       {"label": "Office 302",        "type": "room",       "floor": 2, "capacity": 15,  "x": 30, "y": 12},
    "conference_hall":  {"label": "Conference Hall",   "type": "room",       "floor": 2, "capacity": 80,  "x": 50, "y": 12},
    "office_303":       {"label": "Office 303",        "type": "room",       "floor": 2, "capacity": 15,  "x": 70, "y": 12},
    "office_304":       {"label": "Office 304",        "type": "room",       "floor": 2, "capacity": 15,  "x": 85, "y": 15},
    "library":          {"label": "Library",           "type": "room",       "floor": 2, "capacity": 60,  "x": 20, "y": 22},
    "stair_f2_w":       {"label": "Stairwell West F2", "type": "stairwell",  "floor": 2, "capacity": 30,  "x": 10, "y": 25},
    "stair_f2_e":       {"label": "Stairwell East F2", "type": "stairwell",  "floor": 2, "capacity": 30,  "x": 90, "y": 25},
    "elevator_f2":      {"label": "Elevator (F2)",     "type": "corridor",   "floor": 2, "capacity": 8,   "x": 50, "y": 32},
}

# Edges: (from_node, to_node, base_distance_meters, width_factor)
# All edges are bidirectional. Width factor: 1=narrow, 2=normal, 3=wide.
EDGES_RAW = [
    # ── GROUND FLOOR internal ─────────────────────────────────────────────────
    ("main_entrance",   "lobby",            8,   3),
    ("main_entrance",   "assembly_point",   5,   3),
    ("lobby",           "reception",       10,   2),
    ("lobby",           "g_corridor_w",    12,   3),
    ("lobby",           "g_corridor_e",    12,   3),
    ("lobby",           "elevator_g",       5,   2),
    ("g_corridor_w",    "cafeteria",       15,   2),
    ("g_corridor_w",    "lab_101",         20,   2),
    ("g_corridor_w",    "stair_g_w",       10,   2),
    ("g_corridor_e",    "lab_102",         20,   2),
    ("g_corridor_e",    "server_room",     10,   2),
    ("g_corridor_e",    "stair_g_e",       10,   2),
    ("stair_g_w",       "exit_west",       15,   2),
    ("stair_g_e",       "exit_east",       15,   2),
    ("exit_west",       "assembly_point",  30,   3),
    ("exit_east",       "assembly_point",  30,   3),
    ("cafeteria",       "stair_g_w",       12,   2),

    # ── VERTICAL connections G→F1 ─────────────────────────────────────────────
    ("stair_g_w",       "stair_f1_w",      14,   2),
    ("stair_g_e",       "stair_f1_e",      14,   2),
    ("elevator_g",      "elevator_f1",      5,   1),   # elevator: narrow=slow

    # ── FLOOR 1 internal ──────────────────────────────────────────────────────
    ("stair_f1_w",      "f1_corridor_w",    8,   2),
    ("stair_f1_e",      "f1_corridor_e",    8,   2),
    ("elevator_f1",     "f1_corridor_main", 5,   2),
    ("f1_corridor_main","f1_corridor_w",   15,   3),
    ("f1_corridor_main","f1_corridor_e",   15,   3),
    ("f1_corridor_main","faculty_lounge",   8,   2),
    ("f1_corridor_main","restroom_f1",      6,   1),
    ("f1_corridor_main","classroom_203",   10,   2),
    ("f1_corridor_w",   "classroom_201",   18,   2),
    ("f1_corridor_w",   "classroom_202",   10,   2),
    ("f1_corridor_e",   "classroom_204",   10,   2),
    ("f1_corridor_e",   "classroom_205",   18,   2),

    # ── VERTICAL connections F1→F2 ────────────────────────────────────────────
    ("stair_f1_w",      "stair_f2_w",      14,   2),
    ("stair_f1_e",      "stair_f2_e",      14,   2),
    ("elevator_f1",     "elevator_f2",      5,   1),

    # ── FLOOR 2 internal ──────────────────────────────────────────────────────
    ("stair_f2_w",      "f2_corridor_w",    8,   2),
    ("stair_f2_e",      "f2_corridor_e",    8,   2),
    ("elevator_f2",     "f2_corridor_main", 5,   2),
    ("f2_corridor_main","f2_corridor_w",   15,   3),
    ("f2_corridor_main","f2_corridor_e",   15,   3),
    ("f2_corridor_main","conference_hall", 10,   3),
    ("f2_corridor_w",   "library",         12,   2),
    ("f2_corridor_w",   "office_301",      18,   1),
    ("f2_corridor_w",   "office_302",      10,   1),
    ("f2_corridor_e",   "office_303",      10,   1),
    ("f2_corridor_e",   "office_304",      18,   1),
]

# Exit nodes — the algorithm treats reaching any of these as "safe"
EXIT_NODES = {"main_entrance", "exit_west", "exit_east", "assembly_point"}

# Nodes that are elevators — disabled during fire emergencies
ELEVATOR_NODES = {"elevator_g", "elevator_f1", "elevator_f2"}

# Preset hazard scenarios for the UI
HAZARD_SCENARIOS = {
    "Fire in Cafeteria": {
        "blocked_nodes": {"cafeteria"},
        "hazard_edges":  {("g_corridor_w", "cafeteria"): 999,
                          ("cafeteria", "stair_g_w"): 999},
        "description": "🔥 Fire detected in Cafeteria. West ground corridor impacted.",
    },
    "Smoke in West Stairwell (All Floors)": {
        "blocked_nodes": {"stair_g_w", "stair_f1_w", "stair_f2_w"},
        "hazard_edges":  {},
        "description": "💨 Smoke fills west stairwells on all floors. Use east stairs.",
    },
    "Structural Damage – East Corridor F1": {
        "blocked_nodes": {"f1_corridor_e"},
        "hazard_edges":  {("f1_corridor_main", "f1_corridor_e"): 999},
        "description": "⚠️ Structural damage. East F1 corridor blocked.",
    },
    "Elevator Failure + Server Room Fire": {
        "blocked_nodes": {"elevator_g", "elevator_f1", "elevator_f2", "server_room"},
        "hazard_edges":  {("g_corridor_e", "server_room"): 999},
        "description": "🚨 Elevators offline. Server room fire spreading east side.",
    },
    "Mass Casualty – Conference Hall": {
        "blocked_nodes": {"conference_hall"},
        "hazard_edges":  {("f2_corridor_main", "conference_hall"): 999},
        "description": "🚑 Medical emergency in Conference Hall. F2 central area congested.",
    },
    "No Active Hazards": {
        "blocked_nodes": set(),
        "hazard_edges":  {},
        "description": "✅ All clear. Normal evacuation routing.",
    },
}