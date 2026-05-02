# NEXUS Backend — Smart Campus Routing Engine

FastAPI + OSMnx + NetworkX backend that powers the NEXUS routing frontend.

---

## Quick Start

```bash
cd backend
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Interactive docs: http://localhost:8000/docs

---

## API Reference

### `GET /health`
Liveness probe.

```json
{ "status": "ok", "cached_graphs": 2, "version": "1.0.0" }
```

---

### `POST /load-map`
Download road network around a point.

**Request**
```json
{
  "lat": 16.4422,
  "lon": 80.6217,
  "radius": 400,
  "network_type": "all"
}
```

**Response** — returns `graph_id` token for subsequent calls.
```json
{
  "graph_id": "a3f9c1d82b4e7f01",
  "node_count": 312,
  "edge_count": 748,
  "cached": false,
  "bbox": { "north": 16.446, "south": 16.438, "east": 80.626, "west": 80.616 },
  "centre": { "lat": 16.4422, "lon": 80.6217 },
  "nodes": [{ "id": 123456789, "lat": 16.4415, "lon": 80.6201 }, "..."],
  "edges": [{ "u": 123456789, "v": 987654321, "weight": 45.2 }, "..."]
}
```

**network_type options**: `drive`, `walk`, `bike`, `all`

---

### `POST /filter-bbox`
Crop a loaded graph to a bounding box drawn by the user.

**Request**
```json
{
  "graph_id": "a3f9c1d82b4e7f01",
  "north": 16.444,
  "south": 16.440,
  "east": 80.623,
  "west": 80.619
}
```

**Response** — returns a new `graph_id` for the sub-graph.
```json
{
  "graph_id": "bbox_9c2a4f117e3d",
  "node_count": 87,
  "edge_count": 203,
  "nodes": [...],
  "edges": [...]
}
```

---

### `POST /route`
Compute shortest path.

**Request**
```json
{
  "graph_id": "bbox_9c2a4f117e3d",
  "start": 123456789,
  "end": 987654321,
  "algorithm": "astar"
}
```

**Response**
```json
{
  "path": [123456789, 234567890, 345678901, 987654321],
  "cost": 312.7,
  "cost_km": 0.3127,
  "steps": 42,
  "exec_time_ms": 1.84,
  "algorithm": "astar",
  "path_coords": [
    { "lat": 16.4415, "lon": 80.6201 },
    "..."
  ]
}
```

---

## Architecture

```
main.py          FastAPI app, routes, CORS, error handling
graph_loader.py  OSMnx download, graph cleaning, serialisation
routing.py       Dijkstra + A* with custom min-heap priority queue
models.py        Pydantic v2 request/response schemas
utils.py         LRU graph cache, timer, haversine, logging
```

### Caching strategy
- **Two-level cache**: OSMnx writes to disk (`~/.cache/osmnx`), backend holds cleaned NetworkX objects in memory.
- LRU eviction with 20-graph capacity and 1-hour TTL.
- Sub-graphs from `/filter-bbox` are cached independently so repeated bbox queries are instant.

### Algorithm notes
- Both algorithms use a **custom min-heap** (`heapq` + lazy deletion) — faster than NetworkX's built-in for small-to-medium graphs because we avoid per-edge attribute dictionary overhead.
- A* uses the **haversine heuristic** (admissible and consistent for road networks).
- Graphs are cleaned to their **largest strongly-connected component** to guarantee every pair of nodes has a valid path.

---

## Frontend Integration

In your existing frontend, replace the Overpass fetch with three calls:

```js
// 1. Load graph on map load / location change
const { graph_id, nodes, edges } = await fetch('/load-map', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ lat: 16.4422, lon: 80.6217, radius: 400 })
}).then(r => r.json());

// 2. (optional) After user draws bbox
const sub = await fetch('/filter-bbox', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ graph_id, north, south, east, west })
}).then(r => r.json());

// 3. Route
const result = await fetch('/route', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ graph_id: sub.graph_id, start, end, algorithm: 'astar' })
}).then(r => r.json());

// result.path_coords → draw polyline on Leaflet
// result.path        → highlight nodes on canvas
```
