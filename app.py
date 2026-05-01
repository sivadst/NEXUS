import streamlit as st
from graph import build_graph
from routing import dijkstra
from simulation import simulate_hazard, simulate_crowd
from data import nodes, edges, crowd, hazard

# ==============================
# PAGE CONFIG
# ==============================
st.set_page_config(page_title="NEXUS - Smart Evacuation", layout="centered")

st.title("🚨 NEXUS: Smart Disaster Evacuation System")

# ==============================
# BUILD GRAPH
# ==============================
graph = build_graph(nodes, edges, crowd, hazard)

# ==============================
# USER INPUT
# ==============================
st.subheader("Select Locations")

start = st.selectbox("Start Location", list(nodes.keys()))
end = st.selectbox("Destination", list(nodes.keys()))

# ==============================
# ACTION BUTTONS
# ==============================
col1, col2, col3 = st.columns(3)

with col1:
    if st.button("🚀 Find Best Route"):
        path, cost = dijkstra(graph, start, end)

        if path:
            st.success(f"Optimal Path: {' → '.join(path)}")
            st.info(f"Total Cost: {cost}")
        else:
            st.error("No path found!")

with col2:
    if st.button("🔥 Simulate Hazard"):
        simulate_hazard(hazard)
        st.warning("Hazard introduced! Routes may change.")

with col3:
    if st.button("👥 Simulate Crowd"):
        simulate_crowd(crowd)
        st.info("Crowd levels updated.")

# ==============================
# SHOW CURRENT STATE
# ==============================
st.subheader("📊 Current System State")

st.write("### Crowd Levels")
st.json(crowd)

st.write("### Hazard Levels")
st.json(hazard)

# ==============================
# FOOTER
# ==============================
st.markdown("---")
st.caption("Built with Graph + Dijkstra + Simulation ⚡")