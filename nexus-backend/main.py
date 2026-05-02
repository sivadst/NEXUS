"""
NEXUS Routing Engine — FastAPI Application
Run with: uvicorn main:app --reload --host 0.0.0.0 --port 8000
"""

from __future__ import annotations

import logging
import traceback
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from graph_loader import filter_bbox as _filter_bbox
from graph_loader import load_graph as _load_graph
from models import (
    FilterBBoxRequest,
    FilterBBoxResponse,
    HealthResponse,
    LoadMapRequest,
    LoadMapResponse,
    RouteRequest,
    RouteResponse,
)
from routing import compute_route as _compute_route
from utils import graph_cache, logger

# ── LIFESPAN ──────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("NEXUS backend starting up")
    yield
    logger.info("NEXUS backend shutting down — cached graphs: %d", graph_cache.size())


# ── APP ───────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="NEXUS — Smart Campus Routing Engine",
    description=(
        "Backend API for the NEXUS routing engine. "
        "Loads real-world road graphs via OSMnx and computes "
        "shortest paths using Dijkstra and A*."
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Allow the NEXUS frontend (any origin during development)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── GLOBAL EXCEPTION HANDLER ──────────────────────────────────────────────────

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error("Unhandled exception on %s: %s", request.url.path, exc)
    logger.debug(traceback.format_exc())
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": f"Internal server error: {exc}"},
    )


# ── ROUTES ────────────────────────────────────────────────────────────────────

@app.get("/health", response_model=HealthResponse, tags=["System"])
def health() -> HealthResponse:
    """Liveness / readiness probe."""
    return HealthResponse(
        status="ok",
        cached_graphs=graph_cache.size(),
        version="1.0.0",
    )


@app.get("/cache/stats", tags=["System"])
def cache_stats() -> dict:
    """Inspect what graphs are currently held in memory."""
    return {"entries": graph_cache.stats(), "total": graph_cache.size()}


@app.post(
    "/load-map",
    response_model=LoadMapResponse,
    status_code=status.HTTP_200_OK,
    tags=["Graph"],
    summary="Download road network around a point",
)
async def load_map(req: LoadMapRequest) -> LoadMapResponse:
    """
    Fetch the OSM road network around the given coordinate within `radius` metres.

    - Returns a **graph_id** token to be used in subsequent `/filter-bbox` and `/route` calls.
    - Repeated calls with the same parameters are served from the in-memory cache.
    """
    try:
        result = _load_graph(req.lat, req.lon, req.radius, req.network_type)
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))

    return result


@app.post(
    "/filter-bbox",
    response_model=FilterBBoxResponse,
    status_code=status.HTTP_200_OK,
    tags=["Graph"],
    summary="Crop a loaded graph to a bounding box",
)
async def filter_bbox(req: FilterBBoxRequest) -> FilterBBoxResponse:
    """
    Extract the sub-graph of a previously loaded graph that falls within the
    specified bounding box.

    Returns a **new graph_id** for the cropped sub-graph.
    Both the parent and sub-graph remain cached independently.
    """
    try:
        result = _filter_bbox(req.graph_id, req.north, req.south, req.east, req.west)
    except KeyError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))

    return result


@app.post(
    "/route",
    response_model=RouteResponse,
    status_code=status.HTTP_200_OK,
    tags=["Routing"],
    summary="Compute shortest path between two nodes",
)
async def route(req: RouteRequest) -> RouteResponse:
    """
    Compute the shortest path between `start` and `end` nodes using the
    selected algorithm (`dijkstra` or `astar`).

    - `graph_id` must reference a graph previously loaded via `/load-map`
      or `/filter-bbox`.
    - Returns the **path** (ordered node IDs), **cost** (metres), execution
      **steps**, timing, and per-node lat/lon coordinates for frontend rendering.
    """
    try:
        result = _compute_route(req.graph_id, req.start, req.end, req.algorithm)
    except KeyError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))

    return result


# ── DEV ENTRYPOINT ────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
