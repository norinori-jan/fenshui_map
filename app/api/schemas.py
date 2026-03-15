from typing import Any

from pydantic import BaseModel, Field


class AnalyzeLocationRequest(BaseModel):
    lat: float = Field(..., ge=-90, le=90)
    lng: float = Field(..., ge=-180, le=180)


class AnalyzeLocationResponse(BaseModel):
    location: dict[str, float]
    terrain_profile: dict[str, Any] | None
    heuristics: dict[str, Any]
    grounded_advice: str
    model_summary: dict[str, Any]
    gsi_tiles: dict[str, str]  # フロントエンド用 地理院タイル XYZ URL テンプレート