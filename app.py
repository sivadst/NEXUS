import streamlit as st
import plotly.graph_objects as go

# ===== IMPORTS =====
from map_loader import load_map, filter_by_bbox

try:
    from routing import dijkstra, a_star
except:
    def dijkstra(graph, start, end):
        return [start, end], 0

    def a_star(graph, start, end, pos):
        return [start, end], 0


# ===== STATE =====
def init_state():
    if "nodes" not in st.session_state:
        st.session_state.nodes = {}
    if "edges" not in st.session_state:
        st.session_state.edges = []
    if "route" not in st.session_state:
        st.session_state.route = None
    if "use_astar" not in st.session_state:
        st.session_state.use_astar = False


# ===== GRAPH =====
def build_graph(nodes, edges):
    graph = {node: [] for node in nodes}
    for u, v, w in edges:
        graph[u].append((v, w))
        graph[v].append((u, w))
    return graph


# ===== ROUTE =====
def compute_route(start, end):
    graph = build_graph(st.session_state.nodes.keys(), st.session_state.edges)

    if st.session_state.use_astar:
        path, cost = a_star(graph, start, end, {})
    else:
        path, cost = dijkstra(graph, start, end)

    st.session_state.route = (path, cost)


# ===== MAP =====
def draw_map(nodes, edges, path=None):
    fig = go.Figure()

    # Nodes
    fig.add_trace(go.Scattermapbox(
        lat=[nodes[n]["lat"] for n in nodes],
        lon=[nodes[n]["lon"] for n in nodes],
        mode='markers',
        marker=dict(size=6, color='blue'),
    ))

    # Edges
    for u, v, _ in edges:
        fig.add_trace(go.Scattermapbox(
            lat=[nodes[u]["lat"], nodes[v]["lat"]],
            lon=[nodes[u]["lon"], nodes[v]["lon"]],
            mode='lines',
            line=dict(width=1, color='gray'),
            showlegend=False
        ))

    # Path
    if path:
        for i in range(len(path)-1):
            u, v = path[i], path[i+1]
            fig.add_trace(go.Scattermapbox(
                lat=[nodes[u]["lat"], nodes[v]["lat"]],
                lon=[nodes[u]["lon"], nodes[v]["lon"]],
                mode='lines',
                line=dict(width=4, color='red'),
                showlegend=False
            ))

    fig.update_layout(
        mapbox_style="open-street-map",
        mapbox_zoom=15,
        height=600,
        margin=dict(l=0, r=0, t=0, b=0)
    )

    return fig


# ===== MAIN =====
def main():
    st.set_page_config(page_title="NEXUS", layout="wide")
    init_state()

    st.title("⚡ NEXUS — Real Map Routing Engine")

    # ===== SIDEBAR =====
    st.sidebar.title("Map Controls")

    map_input = st.sidebar.text_input(
        "Paste Google Maps URL / Place / lat,lon",
        "https://maps.google.com/@16.442,80.621,15z"
    )

    if st.sidebar.button("Load Map"):
     with st.spinner("Loading map... please wait ⏳"):
        nodes, edges = load_map(map_input)
        st.session_state.nodes = nodes
        st.session_state.edges = edges
        st.success("Map Loaded")

    st.sidebar.subheader("Bounding Box")

    north = st.sidebar.number_input("North", value=16.445)
    south = st.sidebar.number_input("South", value=16.440)
    east = st.sidebar.number_input("East", value=80.625)
    west = st.sidebar.number_input("West", value=80.620)

    if st.sidebar.button("Apply Area Filter"):
        nodes, edges = filter_by_bbox(
            st.session_state.nodes,
            st.session_state.edges,
            north, south, east, west
        )
        st.session_state.nodes = nodes
        st.session_state.edges = edges

    # ===== ROUTING CONTROLS =====
    if st.session_state.nodes:
        node_ids = list(st.session_state.nodes.keys())

        start = st.sidebar.selectbox("Start Node", node_ids)
        end = st.sidebar.selectbox("End Node", node_ids)

        st.session_state.use_astar = st.sidebar.checkbox("Use A*", value=False)

        if st.sidebar.button("Compute Route"):
            compute_route(start, end)

    # ===== MAP VIEW =====
    st.subheader("Map")

    if st.session_state.nodes:
        path = st.session_state.route[0] if st.session_state.route else None
        fig = draw_map(st.session_state.nodes, st.session_state.edges, path)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Load a map first")

    # ===== RESULT =====
    st.subheader("Result")

    if st.session_state.route:
        path, cost = st.session_state.route
        st.success(f"Path: {' → '.join(map(str, path))}")
        st.write(f"Cost: {cost}")
    else:
        st.info("Run routing to see result")


if __name__ == "__main__":
    main()