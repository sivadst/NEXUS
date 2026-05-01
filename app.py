import streamlit as st
import networkx as nx
import matplotlib.pyplot as plt

from data import CAMPUS_EDGES, NODES
from graph import CampusGraph
from routing import dijkstra_optimal_path
from simulation import EventSimulator

st.set_page_config(page_title="NEXUS Evacuation Routing", layout="wide")

# --- System Initialization (Session State) ---
if 'graph' not in st.session_state:
    g = CampusGraph()
    for u, v, d in CAMPUS_EDGES:
        g.add_edge(u, v, d)
    st.session_state.graph = g
    st.session_state.sim = EventSimulator()

graph = st.session_state.graph
sim = st.session_state.sim

# --- UI Sidebar: Controls ---
st.sidebar.title("NEXUS Control Panel")

st.sidebar.subheader("1. Routing")
start_node = st.sidebar.selectbox("Source (Current Location)", NODES, index=NODES.index("Main_Entrance"))
end_node = st.sidebar.selectbox("Destination (Safe Zone)", NODES, index=NODES.index("Emergency_Exit_East"))

st.sidebar.subheader("2. Inject Live Events")
event_type = st.sidebar.selectbox("Event Type", ["hazard", "crowd"])
edge_select = st.sidebar.selectbox("Target Edge", [f"{u} - {v}" for u, v, d in CAMPUS_EDGES])
intensity = st.sidebar.slider("Intensity (10 = Complete Blockage for Hazards)", 0, 10, 5)

if st.sidebar.button("Inject Event"):
    u, v = edge_select.split(" - ")
    sim.enqueue_event(event_type, u, v, intensity)
    sim.process_events(graph)
    st.sidebar.success(f"Processed: {event_type.upper()} level {intensity} on {u}-{v}")

if st.sidebar.button("Reset Graph State"):
    for u, v, d in CAMPUS_EDGES:
        graph.update_edge_state(u, v, 'hazard', 0)
        graph.update_edge_state(u, v, 'crowd', 0)
    st.sidebar.info("System normalized.")

# --- Core Logic: Compute Route ---
total_weight, optimal_path = dijkstra_optimal_path(graph, start_node, end_node)

# --- Main UI ---
st.title("NEXUS: Adaptive Disaster Routing")

if total_weight == float('inf'):
    st.error(f"CRITICAL ALERT: No safe route available from {start_node} to {end_node}. All paths blocked.")
else:
    st.success(f"Optimal Evacuation Route Calculated (Path Cost: {total_weight})")
    st.markdown(f"**Path:** {' ➔ '.join(optimal_path)}")

# --- Visualization Render ---
# We use NetworkX purely for drawing the mathematical structure we built in graph.py
G_vis = nx.Graph()
for u in graph.edges:
    for v in graph.edges[u]:
        G_vis.add_edge(u, v)

# Determine colors
node_colors = []
for node in G_vis.nodes():
    if node == start_node: node_colors.append('lightgreen')
    elif node == end_node: node_colors.append('lightblue')
    elif node in optimal_path: node_colors.append('gold')
    else: node_colors.append('lightgray')

edge_colors = []
edge_widths = []
for u, v in G_vis.edges():
    # Check graph state
    h_val = graph.edges[u][v]['hazard']
    if h_val >= 10:
        edge_colors.append('red') # Blocked path
        edge_widths.append(3)
    elif h_val > 0:
        edge_colors.append('orange') # Hazardous
        edge_widths.append(2)
    elif u in optimal_path and v in optimal_path and abs(optimal_path.index(u) - optimal_path.index(v)) == 1:
        edge_colors.append('blue') # Optimal path
        edge_widths.append(4)
    else:
        edge_colors.append('gray') # Normal
        edge_widths.append(1)

# Plot
fig, ax = plt.subplots(figsize=(10, 6))
pos = nx.spring_layout(G_vis, seed=42) # Seeded for consistent layout
nx.draw(G_vis, pos, with_labels=True, node_color=node_colors, node_size=2000, 
        edge_color=edge_colors, width=edge_widths, font_size=10, ax=ax)

# Draw dynamic weights on edges
edge_labels = {(u, v): f"W:{graph.get_weight(u, v)}" for u, v in G_vis.edges() if graph.get_weight(u,v) != float('inf')}
nx.draw_networkx_edge_labels(G_vis, pos, edge_labels=edge_labels, font_size=8, ax=ax)

st.pyplot(fig)