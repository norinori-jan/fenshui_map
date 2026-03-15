import json
import math
import os
import re
from dataclasses import asdict
from typing import Any
from urllib.parse import urlencode
from urllib.request import urlopen

from google import genai
from google.genai import types

from app.core.registry_a import DIRECTIONS, direction_to_compass_label, get_direction_profile, get_five_element_profile
from app.modules.feng_shui.models import Coordinate, FengShuiAnalysisResult, FengShuiHeuristics, TerrainProfile, TerrainSample
from fortune_core.elevation import ElevationSource, build_terrain_summary


EARTH_RADIUS_METERS = 6_378_137

# ---------------------------------------------------------------------------
# 国土地理院（GSI）設定
# ---------------------------------------------------------------------------

# 標高APIエンドポイント（APIキー不要・CC-BY 4.0）
_GSI_ELEVATION_ENDPOINT = (
    "https://cyberjapandata2.gsi.go.jp/general/dem/scripts/getelevation.php"
    "?lon={lng}&lat={lat}&outtype=JSON"
)

# フロントエンド用 XYZ タイル URL テンプレート
GSI_TILE_URLS: dict[str, str] = {
    "standard": "https://cyberjapandata.gsi.go.jp/xyz/std/{z}/{x}/{y}.png",
    "relief": "https://cyberjapandata.gsi.go.jp/xyz/relief/{z}/{x}/{y}.png",
    "hillshade": "https://cyberjapandata.gsi.go.jp/xyz/hillshademap/{z}/{x}/{y}.png",
}

# Gemini に公開する Function Calling 定義（龍脈・砂の高低を動的取得）
_GSI_ELEVATION_DECLARATION = types.FunctionDeclaration(
    name="get_gsi_elevation",
    description=(
        "国土地理院の標高APIを呼び出し、指定した座標の標高（メートル）を返します。"
        "龍脈の尾根や周囲の砂（さ）の高さを動的に確認するために使用します。"
    ),
    parameters=types.Schema(
        type=types.Type.OBJECT,
        properties={
            "lat": types.Schema(type=types.Type.NUMBER, description="緯度（WGS84、例: 35.6894）"),
            "lng": types.Schema(type=types.Type.NUMBER, description="経度（WGS84、例: 139.6917）"),
        },
        required=["lat", "lng"],
    ),
)


def fetch_gsi_elevation_single(lat: float, lng: float) -> float | None:
    """国土地理院標高APIから単一座標の標高(m)を取得する。失敗時は None を返す。"""
    url = _GSI_ELEVATION_ENDPOINT.format(lat=lat, lng=lng)
    try:
        with urlopen(url, timeout=8) as resp:  # noqa: S310
            data = json.loads(resp.read().decode("utf-8"))
        elev = data.get("elevation")
        # "地表面なし" や "---" など数値以外は無効値として扱う
        return float(elev) if isinstance(elev, (int, float)) else None
    except Exception:
        return None


def fetch_gsi_terrain_profile(
    lat: float,
    lng: float,
    *,
    radius_m: int = 250,
    sample_distance_m: int = 120,
) -> TerrainProfile:
    """国土地理院APIで9点サンプリングした TerrainProfile を構築する（APIキー不要）。"""
    center = Coordinate(lat=lat, lng=lng)
    sample_points = {
        "center": center,
        "north_near": _offset_coordinate(center, north_m=sample_distance_m),
        "north_far": _offset_coordinate(center, north_m=radius_m),
        "south_near": _offset_coordinate(center, north_m=-sample_distance_m),
        "south_far": _offset_coordinate(center, north_m=-radius_m),
        "east_near": _offset_coordinate(center, east_m=sample_distance_m),
        "east_far": _offset_coordinate(center, east_m=radius_m),
        "west_near": _offset_coordinate(center, east_m=-sample_distance_m),
        "west_far": _offset_coordinate(center, east_m=-radius_m),
    }

    elevations: dict[str, float | None] = {
        name: fetch_gsi_elevation_single(point.lat, point.lng)
        for name, point in sample_points.items()
    }

    samples = [
        TerrainSample(
            name=name,
            lat=point.lat,
            lng=point.lng,
            elevation_m=elevations[name],  # type: ignore[arg-type]
            source=ElevationSource.GSI_ELEVATION_API,
        )
        for name, point in sample_points.items()
        if elevations[name] is not None
    ]

    return TerrainProfile(
        center_elevation_m=elevations.get("center"),
        north_avg_elevation_m=_average([elevations["north_near"], elevations["north_far"]]),
        south_avg_elevation_m=_average([elevations["south_near"], elevations["south_far"]]),
        east_avg_elevation_m=_average([elevations["east_near"], elevations["east_far"]]),
        west_avg_elevation_m=_average([elevations["west_near"], elevations["west_far"]]),
        sample_count=len(samples),
        data_source=ElevationSource.GSI_ELEVATION_API,
        samples=samples,
    )


def _offset_coordinate(origin: Coordinate, north_m: float = 0.0, east_m: float = 0.0) -> Coordinate:
    delta_lat = (north_m / EARTH_RADIUS_METERS) * (180 / math.pi)
    delta_lng = (east_m / (EARTH_RADIUS_METERS * math.cos(math.radians(origin.lat)))) * (180 / math.pi)
    return Coordinate(lat=origin.lat + delta_lat, lng=origin.lng + delta_lng)


def _average(values: list[float | None]) -> float | None:
    valid_values = [value for value in values if value is not None]
    if not valid_values:
        return None
    return sum(valid_values) / len(valid_values)


def _extract_text(response: Any) -> str:
    text = getattr(response, "text", None)
    if text:
        return text

    parts: list[str] = []
    for candidate in getattr(response, "candidates", []) or []:
        content = getattr(candidate, "content", None)
        for part in getattr(content, "parts", []) or []:
            part_text = getattr(part, "text", None)
            if part_text:
                parts.append(part_text)
    return "\n".join(parts)


def _parse_json_block(text: str) -> dict[str, Any]:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        if cleaned.startswith("json"):
            cleaned = cleaned[4:]

    stripped = cleaned.strip()
    try:
        return json.loads(stripped)
    except json.JSONDecodeError:
        # 応答に前後テキストが混ざるケースを吸収する
        match = re.search(r"\{[\s\S]*\}", stripped)
        if not match:
            raise
        return json.loads(match.group(0))


def _default_model_payload(reason: str) -> dict[str, Any]:
    return {
        "observations": {
            "terrain": {
                "summary": f"Grounding unavailable: {reason}",
                "north_higher_than_south": None,
                "south_more_open": None,
                "east_west_support": "unknown",
                "confidence": "low",
            },
            "roads": {
                "summary": "Road assessment unavailable",
                "road_collision_risk": None,
                "confidence": "low",
            },
            "water": {
                "summary": "Water assessment unavailable",
                "confidence": "low",
            },
        },
        "advice": {
            "overall_judgement": "外部地図鑑定サービスの応答が不安定なため、地形データ中心の暫定判定です。",
            "recommendations": [
                "周辺道路と開口方向を現地で再確認してください。",
                "時間をおいて再鑑定すると精度が上がる場合があります。",
            ],
            "cautions": ["この結果は簡易モードです。"],
        },
    }


def _grounding_is_sparse(model_payload: dict[str, Any]) -> bool:
    observations = model_payload.get("observations") or {}
    terrain = observations.get("terrain") or {}
    roads = observations.get("roads") or {}
    return not terrain or terrain.get("confidence") == "low" or roads.get("confidence") == "low"


def fetch_elevation_profile(
    lat: float,
    lng: float,
    *,
    api_key: str | None = None,
    radius_m: int = 250,
    sample_distance_m: int = 120,
) -> TerrainProfile:
    api_key = api_key or os.getenv("GOOGLE_MAPS_API_KEY")
    if not api_key:
        raise RuntimeError("GOOGLE_MAPS_API_KEY is required to call the Elevation API.")

    center = Coordinate(lat=lat, lng=lng)
    sample_points = {
        "center": center,
        "north_near": _offset_coordinate(center, north_m=sample_distance_m),
        "north_far": _offset_coordinate(center, north_m=radius_m),
        "south_near": _offset_coordinate(center, north_m=-sample_distance_m),
        "south_far": _offset_coordinate(center, north_m=-radius_m),
        "east_near": _offset_coordinate(center, east_m=sample_distance_m),
        "east_far": _offset_coordinate(center, east_m=radius_m),
        "west_near": _offset_coordinate(center, east_m=-sample_distance_m),
        "west_far": _offset_coordinate(center, east_m=-radius_m),
    }

    locations = "|".join(f"{point.lat},{point.lng}" for point in sample_points.values())
    params = urlencode({"locations": locations, "key": api_key})
    url = f"https://maps.googleapis.com/maps/api/elevation/json?{params}"

    with urlopen(url) as response:
        payload = json.loads(response.read().decode("utf-8"))

    if payload.get("status") != "OK":
        raise RuntimeError(f"Elevation API error: {payload.get('status')} - {payload.get('error_message', '')}")

    elevations = {name: item["elevation"] for name, item in zip(sample_points.keys(), payload.get("results", []), strict=True)}
    samples = [
        TerrainSample(
            name=name,
            lat=point.lat,
            lng=point.lng,
            elevation_m=elevations[name],
            source=ElevationSource.GOOGLE_MAPS_ELEVATION,
        )
        for name, point in sample_points.items()
    ]

    return TerrainProfile(
        center_elevation_m=elevations["center"],
        north_avg_elevation_m=_average([elevations["north_near"], elevations["north_far"]]),
        south_avg_elevation_m=_average([elevations["south_near"], elevations["south_far"]]),
        east_avg_elevation_m=_average([elevations["east_near"], elevations["east_far"]]),
        west_avg_elevation_m=_average([elevations["west_near"], elevations["west_far"]]),
        sample_count=len(samples),
        data_source=ElevationSource.GOOGLE_MAPS_ELEVATION,
        samples=samples,
    )


def _build_directional_context() -> dict[str, Any]:
    return {
        "north": {
            "label": direction_to_compass_label("north"),
            "feng_shui_role": get_direction_profile("north").feng_shui_role,
            "element": get_five_element_profile(get_direction_profile("north").element).label_ja,
        },
        "south": {
            "label": direction_to_compass_label("south"),
            "feng_shui_role": get_direction_profile("south").feng_shui_role,
            "element": get_five_element_profile(get_direction_profile("south").element).label_ja,
        },
        "east": {
            "label": direction_to_compass_label("east"),
            "feng_shui_role": get_direction_profile("east").feng_shui_role,
            "element": get_five_element_profile(get_direction_profile("east").element).label_ja,
        },
        "west": {
            "label": direction_to_compass_label("west"),
            "feng_shui_role": get_direction_profile("west").feng_shui_role,
            "element": get_five_element_profile(get_direction_profile("west").element).label_ja,
        },
    }


def evaluate_lantou_heuristics(
    terrain_profile: TerrainProfile | None,
    model_payload: dict[str, Any] | None = None,
) -> FengShuiHeuristics:
    evidence: list[str] = []
    observations = (model_payload or {}).get("observations") or {}
    terrain = observations.get("terrain") or {}
    roads = observations.get("roads") or {}
    directional_context = _build_directional_context()

    north_support = None
    south_open = None
    east_guard = None
    west_guard = None
    shishin_souou = None

    if terrain_profile and terrain_profile.center_elevation_m is not None:
        center = terrain_profile.center_elevation_m
        north_delta = (terrain_profile.north_avg_elevation_m or center) - center
        south_delta = (terrain_profile.south_avg_elevation_m or center) - center
        east_delta = (terrain_profile.east_avg_elevation_m or center) - center
        west_delta = (terrain_profile.west_avg_elevation_m or center) - center

        north_support = north_delta >= 3
        south_open = south_delta <= 1.5
        east_guard = east_delta >= -1
        west_guard = west_delta >= -1
        shishin_souou = north_support and south_open and east_guard and west_guard

        evidence.append(
            f"Elevation deltas around the point: north={north_delta:.1f}m, south={south_delta:.1f}m, east={east_delta:.1f}m, west={west_delta:.1f}m."
        )
        evidence.append(
            f"Directional roles from Registry A: north={directional_context['north']['feng_shui_role']}, south={directional_context['south']['feng_shui_role']}, east={directional_context['east']['feng_shui_role']}, west={directional_context['west']['feng_shui_role']}."
        )

    road_collision_risk = roads.get("road_collision_risk")
    if road_collision_risk is not None:
        evidence.append(f"Maps-grounded road assessment: road_collision_risk={road_collision_risk}.")

    terrain_note = terrain.get("summary")
    if terrain_note:
        evidence.append(f"Maps-grounded terrain summary: {terrain_note}")

    confidence = "low"
    if terrain_profile and road_collision_risk is not None:
        confidence = "medium"
    if terrain_profile and road_collision_risk is not None and terrain.get("confidence") == "high":
        confidence = "high"

    return FengShuiHeuristics(
        shishin_souou=shishin_souou,
        north_support=north_support,
        south_open=south_open,
        east_guard=east_guard,
        west_guard=west_guard,
        road_collision_risk=road_collision_risk,
        confidence=confidence,
        evidence=evidence,
        directional_context=directional_context,
    )


def _build_maps_prompt(lat: float, lng: float, *, gsi_profile: TerrainProfile | None = None) -> str:
    north = DIRECTIONS["north"]
    south = DIRECTIONS["south"]
    east = DIRECTIONS["east"]
    west = DIRECTIONS["west"]

    # 国土地理院標高データを fortune-core の TerrainSummary に変換して注入（RAG的コンテキスト）
    # 生の標高リストではなく意味のある傾斜角・地勢特徴に要約してトークン数を削減
    gsi_block = ""
    if gsi_profile and gsi_profile.center_elevation_m is not None:
        source = ElevationSource(gsi_profile.data_source) if gsi_profile.data_source in ElevationSource._value2member_map_ else ElevationSource.UNKNOWN  # type: ignore[attr-defined]
        summary = build_terrain_summary(
            center_elevation_m=gsi_profile.center_elevation_m,
            north_avg_m=gsi_profile.north_avg_elevation_m,
            south_avg_m=gsi_profile.south_avg_elevation_m,
            east_avg_m=gsi_profile.east_avg_elevation_m,
            west_avg_m=gsi_profile.west_avg_elevation_m,
            source=source,
        )
        gsi_block = summary.to_llm_context()

    return f"""
You are a feng shui analyst using Google Maps grounding and GSI (Japan Geospatial Information Authority) elevation data.

Target coordinate (WGS84 / JGD2011):
- latitude: {lat}
- longitude: {lng}

{gsi_block + chr(10) if gsi_block else ""}Interpret the environment using these Registry A roles:
- north ({north.label_ja}) = {north.feng_shui_role}, trigram={north.trigram}, element={north.element}
- south ({south.label_ja}) = {south.feng_shui_role}, trigram={south.trigram}, element={south.element}
- east ({east.label_ja}) = {east.feng_shui_role}, trigram={east.trigram}, element={east.element}
- west ({west.label_ja}) = {west.feng_shui_role}, trigram={west.trigram}, element={west.element}

Inspect the surrounding environment within roughly 300 meters and answer in JSON.
Focus on:
1. Terrain shape relevant to lantou feng shui: whether the north side is relatively higher, whether the south side is more open, and whether east/west have protective mass.
2. Road pattern: whether any road points directly into the target point or appears to terminate toward it, which may indicate road collision risk.
3. Nearby water, slopes, ridgelines, embankments, parks, cut-and-fill terrain, or major artificial structures that materially affect form.

Return valid JSON only using this schema:
{{
  "observations": {{
    "terrain": {{
      "summary": "string",
      "north_higher_than_south": true,
      "south_more_open": true,
      "east_west_support": "balanced|east_only|west_only|weak|unknown",
      "confidence": "low|medium|high"
    }},
    "roads": {{
      "summary": "string",
      "road_collision_risk": false,
      "confidence": "low|medium|high"
    }},
    "water": {{
      "summary": "string",
      "confidence": "low|medium|high"
    }}
  }},
  "advice": {{
    "overall_judgement": "string",
    "recommendations": ["string", "string"],
    "cautions": ["string"]
  }}
}}
If a fact is not observable, set it to null or "unknown" instead of guessing.
If you need elevation for specific additional points to refine the feng shui analysis, call get_gsi_elevation (WGS84 coords, no API key needed).
""".strip()


def analyze_feng_shui_location(
    lat: float,
    lng: float,
    *,
    model: str = "gemini-2.5-pro",
    gemini_api_key: str | None = None,
    maps_api_key: str | None = None,
) -> FengShuiAnalysisResult:
    gemini_api_key = gemini_api_key or os.getenv("GEMINI_API_KEY")

    # --- A. 国土地理院APIで標高プロファイルを事前取得（APIキー不要、RAG的注入）---
    try:
        gsi_profile = fetch_gsi_terrain_profile(lat, lng)
    except Exception:
        gsi_profile = TerrainProfile(
            center_elevation_m=None,
            north_avg_elevation_m=None,
            south_avg_elevation_m=None,
            east_avg_elevation_m=None,
            west_avg_elevation_m=None,
            sample_count=0,
            data_source=ElevationSource.UNKNOWN,
            samples=[],
        )

    model_payload = _default_model_payload("gemini disabled")
    if gemini_api_key:
        try:
            client = genai.Client(api_key=gemini_api_key)

            # --- A. Google Maps Grounding（動的・施設情報）---
            maps_tool = types.Tool(google_maps=types.GoogleMaps())
            # --- B. 国土地理院 Function Calling（追加標高の動的取得）---
            gsi_tool = types.Tool(function_declarations=[_GSI_ELEVATION_DECLARATION])
            tools = [maps_tool, gsi_tool]

            prompt = _build_maps_prompt(lat, lng, gsi_profile=gsi_profile)

            response = client.models.generate_content(
                model=model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    tools=tools,
                    temperature=0.2,
                    response_mime_type="application/json",
                ),
            )

            # --- Function Calling ハンドリング（最大1ラウンドトリップ）---
            first_candidate = (getattr(response, "candidates", None) or [None])[0]
            first_content = getattr(first_candidate, "content", None)
            if first_content:
                fn_response_parts: list[Any] = []
                for part in getattr(first_content, "parts", []) or []:
                    fc = getattr(part, "function_call", None)
                    if fc and fc.name == "get_gsi_elevation":
                        args = fc.args or {}
                        pt_lat = float(args.get("lat", lat))
                        pt_lng = float(args.get("lng", lng))
                        elevation = fetch_gsi_elevation_single(pt_lat, pt_lng)
                        fn_response_parts.append(
                            types.Part(
                                function_response=types.FunctionResponse(
                                    name="get_gsi_elevation",
                                    response={"elevation_m": elevation, "data_source": "gsi_elevation_api"},
                                )
                            )
                        )
                if fn_response_parts:
                    response = client.models.generate_content(
                        model=model,
                        contents=[
                            types.Content(role="user", parts=[types.Part(text=prompt)]),
                            first_content,
                            types.Content(role="user", parts=fn_response_parts),
                        ],
                        config=types.GenerateContentConfig(
                            tools=tools,
                            temperature=0.2,
                            response_mime_type="application/json",
                        ),
                    )

            raw_text = _extract_text(response)
            model_payload = _parse_json_block(raw_text)
        except Exception as exc:
            model_payload = _default_model_payload(str(exc))
    else:
        model_payload = _default_model_payload("GEMINI_API_KEY missing")

    # 地形プロファイル確定：GSIを優先、GSI失敗かつグラウンディング疎の場合のみ
    # Google Maps Elevation API にフォールバック（APIキー必要）
    terrain_profile: TerrainProfile | None = (
        gsi_profile if gsi_profile.center_elevation_m is not None else None
    )
    if terrain_profile is None and _grounding_is_sparse(model_payload):
        resolved_maps_api_key = maps_api_key or os.getenv("GOOGLE_MAPS_API_KEY")
        if resolved_maps_api_key:
            terrain_profile = fetch_elevation_profile(lat, lng, api_key=resolved_maps_api_key)

    heuristics = evaluate_lantou_heuristics(terrain_profile, model_payload)

    overall_judgement = (model_payload.get("advice") or {}).get("overall_judgement", "")
    recommendations = (model_payload.get("advice") or {}).get("recommendations") or []
    cautions = (model_payload.get("advice") or {}).get("cautions") or []

    extra_notes = []
    if heuristics.shishin_souou is True:
        extra_notes.append("標高補完では四神相応に近い地勢です。")
    elif heuristics.shishin_souou is False:
        extra_notes.append("標高補完では四神相応の条件を十分には満たしていません。")

    if heuristics.road_collision_risk is True:
        extra_notes.append("路衝の可能性があるため、玄関位置や植栽・塀による緩衝を検討してください。")

    grounded_advice_parts = [part for part in [overall_judgement, *recommendations, *cautions, *extra_notes] if part]
    grounded_advice = "\n".join(f"- {part}" for part in grounded_advice_parts)

    return FengShuiAnalysisResult(
        location={"lat": lat, "lng": lng},
        terrain_profile=asdict(terrain_profile) if terrain_profile else None,
        heuristics=asdict(heuristics),
        grounded_advice=grounded_advice,
        model_summary=model_payload,
        gsi_tiles=GSI_TILE_URLS,
    )