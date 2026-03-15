from dataclasses import dataclass, field
from typing import Any


@dataclass
class Coordinate:
    lat: float
    lng: float


@dataclass
class TerrainSample:
    name: str
    lat: float
    lng: float
    elevation_m: float
    source: str = "unknown"   # ElevationSource 値（gsi_elevation_api / google_maps_elevation など）


@dataclass
class TerrainProfile:
    center_elevation_m: float | None
    north_avg_elevation_m: float | None
    south_avg_elevation_m: float | None
    east_avg_elevation_m: float | None
    west_avg_elevation_m: float | None
    sample_count: int
    data_source: str
    samples: list[TerrainSample]


@dataclass
class FengShuiHeuristics:
    shishin_souou: bool | None
    north_support: bool | None
    south_open: bool | None
    east_guard: bool | None
    west_guard: bool | None
    road_collision_risk: bool | None
    confidence: str
    evidence: list[str]
    directional_context: dict[str, Any]


@dataclass
class FengShuiAnalysisResult:
    location: dict[str, float]
    terrain_profile: dict[str, Any] | None
    heuristics: dict[str, Any]
    grounded_advice: str
    model_summary: dict[str, Any]
    gsi_tiles: dict[str, str]  # フロントエンド用 地理院タイル XYZ URL テンプレート