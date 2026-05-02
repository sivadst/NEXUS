"""
NEXUS Routing Engine — Data Models
Pydantic schemas for all API request/response contracts.
"""

from __future__ import annotations
from typing import Literal, Optional
from pydantic import BaseModel, Field, field_validator


# ── REQUEST MODELS ────────────────────────────────────────────────────────────

class LoadMapRequest(BaseModel):
    lat: float = Field(..., ge=-90, le=90, description="Centre latitude")
    lon: float = Field(..., ge=-180, le=180, description="Centre longitude")
    radius: int = Field(400, ge=50, le=5000, description="Radius in metres")
    network_type: Literal["drive", "walk", "bike", "all"] = Field(
        "all", description="OSMnx network type"
    )

    @field_validator("radius")
    @classmethod
    def radius_cap(cls, v: int) -> int:
        # Guard against absurdly large requests that would hang OSMnx
        if v > 5000:
            raise ValueError("radius must not exceed 5000 m")
        return v


class FilterBBoxRequest(BaseModel):
    north: float = Field(..., ge=-90, le=90)
    south: float = Field(..., ge=-90, le=90)
    east: float = Field(..., ge=-180, le=180)
    west: float = Field(..., ge=-180, le=180)
    graph_id: str = Field(..., description="Graph cache key returned by /load-map")

    @field_validator("north")
    @classmethod
    def north_gt_south(cls, v: float, info) -> float:
        if "south" in (info.data or {}) and v <= info.data["south"]:
            raise ValueError("north must be greater than south")
        return v


class RouteRequest(BaseModel):
    graph_id: str = Field(..., description="Graph cache key")
    start: int = Field(..., description="Start node OSM ID")
    end: int = Field(..., description="End node OSM ID")
    algorithm: Literal["dijkstra", "astar"] = Field("dijkstra")


# ── RESPONSE MODELS ───────────────────────────────────────────────────────────

class NodeOut(BaseModel):
    id: int
    lat: float
    lon: float


class EdgeOut(BaseModel):
    u: int
    v: int
    weight: float  # metres


class LoadMapResponse(BaseModel):
    graph_id: str
    node_count: int
    edge_count: int
    nodes: list[NodeOut]
    edges: list[EdgeOut]
    bbox: dict[str, float]          # north/south/east/west of actual graph
    centre: dict[str, float]        # lat/lon of request centre
    cached: bool = False


class FilterBBoxResponse(BaseModel):
    graph_id: str                   # NEW graph id for the sub-graph
    node_count: int
    edge_count: int
    nodes: list[NodeOut]
    edges: list[EdgeOut]


class RouteStep(BaseModel):
    node: int
    dist: float                     # cumulative distance from start (m)
    action: Literal["visit", "relax"]


class RouteResponse(BaseModel):
    path: list[int]
    cost: float                     # total path length in metres
    cost_km: float
    steps: int                      # nodes visited during search
    exec_time_ms: float
    algorithm: str
    path_coords: list[dict[str, float]]   # [{lat, lon}, ...] for the frontend


class HealthResponse(BaseModel):
    status: str
    cached_graphs: int
    version: str
