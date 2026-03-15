"""標高データの共通抽象レイヤー。

このモジュールは複数のデータソース（国土地理院 / Google Maps Elevation API など）
を透過的に扱うための型定義と変換ユーティリティを提供します。

座標系: このモジュール内で扱う全ての座標は WGS84 (EPSG:4326) に統一します。
        国土地理院の最新データ (JGD2011) は WGS84 と実用上同一（差異 < 1cm）で
        あるため変換は不要ですが、ソース識別のため coordinate_system フィールドを
        保持します。

タイル方式: 国土地理院の「標高タイル (DEM)」は XYZ 形式の PNG 画像であり、
            RGB チャンネルに標高値が埋め込まれています。フロントエンドでの
            表示にはそのまま使えますが、数値として fortune-core に渡す場合は
            decode_gsi_elevation_tile_rgb() でデコードが必要です。
            $$Elevation = (R \\cdot 2^{16} + G \\cdot 2^8 + B) \\cdot 0.01$$
            無効値 (R=128, G=0, B=0) は海・データ欠損を示します。

優先順位 (ELEVATION_SOURCE_PRIORITY):
    1. gsi_elevation_api    -- APIキー不要、CC-BY 4.0、リアルタイム取得
    2. google_maps_elevation -- 広域カバレッジ、APIキー要
    3. gsi_elevation_tile   -- タイル RGB デコード（オフライン/フロントエンド用）
    4. unknown              -- フォールバック
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import StrEnum


# ---------------------------------------------------------------------------
# データソース識別と優先順位
# ---------------------------------------------------------------------------

class ElevationSource(StrEnum):
    """標高データの取得元を識別するタグ。

    service.py / TerrainSample.source として設定し、後の
    デバッグ・品質集計で「どのソースのデータか」を追跡します。
    """
    GSI_ELEVATION_API = "gsi_elevation_api"          # 国土地理院 標高API（テキスト）
    GSI_ELEVATION_TILE = "gsi_elevation_tile"        # 国土地理院 標高タイル（RGB デコード）
    GOOGLE_MAPS_ELEVATION = "google_maps_elevation"  # Google Maps Elevation API
    UNKNOWN = "unknown"


# 優先度: インデックスが小さいほど信頼度が高い
ELEVATION_SOURCE_PRIORITY: list[ElevationSource] = [
    ElevationSource.GSI_ELEVATION_API,
    ElevationSource.GOOGLE_MAPS_ELEVATION,
    ElevationSource.GSI_ELEVATION_TILE,
    ElevationSource.UNKNOWN,
]

# 座標系タグ（将来の旧測地系データ混入に備えた識別子）
COORDINATE_SYSTEM_WGS84 = "WGS84/JGD2011"  # 国土地理院最新データも実用上同一


# ---------------------------------------------------------------------------
# 共通値型: ElevationResult
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ElevationResult:
    """単一地点の標高取得結果（データソース非依存の共通型）。

    elevation_fetcher が Google か GSI かに関わらずこの型を返すことで、
    呼び出し元は source フィールドで出自を確認しつつ同一インターフェースで扱えます。
    """

    lat: float
    lng: float
    elevation_m: float | None
    source: ElevationSource
    coordinate_system: str = COORDINATE_SYSTEM_WGS84
    is_valid: bool = True   # False = 海・欠損・無効値（RGBデコード時の 0x800000 など）

    def __post_init__(self) -> None:
        if not (-90.0 <= self.lat <= 90.0):
            raise ValueError(f"lat must be in [-90, 90], got {self.lat}")
        if not (-180.0 <= self.lng <= 180.0):
            raise ValueError(f"lng must be in [-180, 180], got {self.lng}")


def preferred_elevation(results: list[ElevationResult]) -> ElevationResult | None:
    """複数ソースの結果から優先順位に従い最良の有効値を返す。"""
    priority_map = {src: i for i, src in enumerate(ELEVATION_SOURCE_PRIORITY)}
    valid = [r for r in results if r.is_valid and r.elevation_m is not None]
    if not valid:
        return None
    return min(valid, key=lambda r: priority_map.get(r.source, 999))


# ---------------------------------------------------------------------------
# 国土地理院 標高タイル RGB デコード
# ---------------------------------------------------------------------------

# RGB=(128, 0, 0) が無効値（地表面なし・海域）を示す
_GSI_TILE_INVALID_RGB = (128, 0, 0)

# 無効値かどうかを判定する生ピクセル値（16進）
_GSI_TILE_INVALID_RAW = 0x800000


def decode_gsi_elevation_tile_rgb(r: int, g: int, b: int) -> ElevationResult | None:
    """国土地理院の標高タイル PNG 1ピクセル (R, G, B) を標高 (m) に変換する。

    変換式:
        raw = R * 65536 + G * 256 + B
        elevation_m = raw * 0.01   (ただし raw < 8388608)
        elevation_m = (raw - 16777216) * 0.01   (raw >= 8388608、負の標高)
        無効値 (R=128, G=0, B=0 = 0x800000) は None を返す。

    Args:
        r: 赤チャンネル (0–255)
        g: 緑チャンネル (0–255)
        b: 青チャンネル (0–255)

    Returns:
        float (m) または None（無効値）
    """
    if not (0 <= r <= 255 and 0 <= g <= 255 and 0 <= b <= 255):
        raise ValueError(f"RGB values must be 0–255, got ({r}, {g}, {b})")

    raw = r * 65536 + g * 256 + b
    if raw == _GSI_TILE_INVALID_RAW:
        return None

    # 負の標高（地下、海底など）は 2 の補数表現
    if raw >= 8_388_608:
        elevation_m = (raw - 16_777_216) * 0.01
    else:
        elevation_m = raw * 0.01

    return elevation_m  # type: ignore[return-value]


def decode_gsi_elevation_tile_rgb_result(
    r: int,
    g: int,
    b: int,
    *,
    lat: float,
    lng: float,
) -> ElevationResult:
    """decode_gsi_elevation_tile_rgb の ElevationResult ラッパー。

    タイルのピクセル座標から逆算した地理座標 (lat, lng) と組み合わせて
    ElevationResult を組み立てます。
    """
    elevation_m = decode_gsi_elevation_tile_rgb(r, g, b)
    return ElevationResult(
        lat=lat,
        lng=lng,
        elevation_m=elevation_m,
        source=ElevationSource.GSI_ELEVATION_TILE,
        is_valid=elevation_m is not None,
    )


# ---------------------------------------------------------------------------
# 地勢サマリ（LLM への要約変換・トークン削減）
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class DirectionalDelta:
    """中心点と各方位との標高差および地勢特徴。"""

    direction: str         # "north" / "south" / "east" / "west"
    delta_m: float         # 中心点との標高差（正=高い、負=低い）
    slope_deg: float       # 傾斜角 (°)
    feature: str           # "ridge" / "valley" / "flat" / "gentle_slope"


@dataclass(frozen=True)
class TerrainSummary:
    """LLM への注入用に要約された地勢情報（生の標高値より意味のある形式）。

    raw の標高リストをそのまま渡すのではなく fortune-core でこの型に変換し、
    Gemini への入力トークンを削減しながら推論精度を向上させます。

    source_priority: 'gsi_elevation_api' のように最も信頼性の高いソースを示す。
    coordinate_system: 常に 'WGS84/JGD2011' を期待。
    gsi_attribution: GSI データ利用時の帰属表記文字列（UI 表示必須）。
    """

    center_elevation_m: float | None
    directional_deltas: list[DirectionalDelta]
    dominant_slope_direction: str | None  # 最急勾配の方位（龍脈の流れ）
    dominant_slope_deg: float | None      # 最急傾斜角 (°)
    source_priority: str                  # 採用されたデータソースの識別子
    coordinate_system: str = COORDINATE_SYSTEM_WGS84
    gsi_attribution: str = "出典：国土地理院"  # 利用規約必須クレジット

    def to_llm_context(self) -> str:
        """Gemini プロンプトに埋め込む最小限のテキストブロックを生成する。"""
        lines: list[str] = [
            f"地勢サマリ（{self.source_priority} / {self.coordinate_system}）:",
            f"  中心標高: {self.center_elevation_m:.1f} m" if self.center_elevation_m is not None else "  中心標高: 不明",
        ]
        for d in self.directional_deltas:
            sign = "+" if d.delta_m >= 0 else ""
            lines.append(
                f"  {d.direction}: {sign}{d.delta_m:.1f} m, 傾斜 {d.slope_deg:.1f}°, 特徴={d.feature}"
            )
        if self.dominant_slope_direction:
            lines.append(
                f"  龍脈方向（最急勾配）: {self.dominant_slope_direction} ({self.dominant_slope_deg:.1f}°)"
            )
        lines.append(f"  {self.gsi_attribution}")
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# TerrainSummary 変換ユーティリティ
# ---------------------------------------------------------------------------

_SLOPE_THRESHOLDS = [
    (0.5, "flat"),
    (3.0, "gentle_slope"),
    (10.0, "ridge"),
]


def _classify_slope(slope_deg: float) -> str:
    for threshold, label in _SLOPE_THRESHOLDS:
        if slope_deg < threshold:
            return label
    return "valley"  # 急斜面 / 谷


def _slope_deg(delta_m: float, horizontal_m: float) -> float:
    """水平距離 horizontal_m に対する標高差 delta_m から傾斜角（度）を返す。"""
    if horizontal_m <= 0:
        return 0.0
    return math.degrees(math.atan(abs(delta_m) / horizontal_m))


def build_terrain_summary(
    center_elevation_m: float | None,
    north_avg_m: float | None,
    south_avg_m: float | None,
    east_avg_m: float | None,
    west_avg_m: float | None,
    *,
    horizontal_m: float = 185.0,   # 標高サンプル間の水平距離の目安（デフォルト: near+far の中央値）
    source: ElevationSource = ElevationSource.GSI_ELEVATION_API,
) -> TerrainSummary:
    """標高プロファイルの数値から TerrainSummary（意味ある要約）を生成する。

    Args:
        center_elevation_m: 中心点の標高 (m)
        north_avg_m / south_avg_m / east_avg_m / west_avg_m: 各方位の平均標高 (m)
        horizontal_m: サンプリング半径の代表水平距離 (m)。傾斜角計算に使用。
        source: 採用されたデータソース。
    """
    center = center_elevation_m or 0.0

    dir_data = [
        ("north", north_avg_m),
        ("south", south_avg_m),
        ("east", east_avg_m),
        ("west", west_avg_m),
    ]

    deltas: list[DirectionalDelta] = []
    for direction, avg_m in dir_data:
        if avg_m is None:
            continue
        delta = avg_m - center
        slope = _slope_deg(delta, horizontal_m)
        deltas.append(DirectionalDelta(
            direction=direction,
            delta_m=round(delta, 2),
            slope_deg=round(slope, 2),
            feature=_classify_slope(slope),
        ))

    # 龍脈方向 = 最も大きな下り勾配の方位（気の流れ込む方向）
    dominant: DirectionalDelta | None = None
    if deltas:
        # 最急降下（最も負のデルタ）を龍脈の流入方向とする
        dominant = min(deltas, key=lambda d: d.delta_m)

    return TerrainSummary(
        center_elevation_m=center_elevation_m,
        directional_deltas=deltas,
        dominant_slope_direction=dominant.direction if dominant else None,
        dominant_slope_deg=dominant.slope_deg if dominant else None,
        source_priority=str(source),
    )
