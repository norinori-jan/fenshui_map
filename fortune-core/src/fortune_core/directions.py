from dataclasses import dataclass
from enum import StrEnum

from fortune_core.enums import Bagua, FiveElement


class Direction(StrEnum):
    NORTH = "north"
    NORTH_EAST = "north_east"
    EAST = "east"
    SOUTH_EAST = "south_east"
    SOUTH = "south"
    SOUTH_WEST = "south_west"
    WEST = "west"
    NORTH_WEST = "north_west"

    @property
    def label_ja(self) -> str:
        return get_direction_profile(self).label_ja


@dataclass(frozen=True)
class DirectionProfile:
    key: Direction
    label_ja: str
    start_deg: float
    end_deg: float
    bagua: Bagua
    element: FiveElement
    feng_shui_role: str

    def contains(self, bearing: float) -> bool:
        normalized = normalize_bearing(bearing)
        if self.start_deg <= self.end_deg:
            return self.start_deg <= normalized < self.end_deg
        return normalized >= self.start_deg or normalized < self.end_deg


DIRECTION_PROFILES: dict[Direction, DirectionProfile] = {
    Direction.NORTH: DirectionProfile(
        key=Direction.NORTH,
        label_ja="北",
        start_deg=337.5,
        end_deg=22.5,
        bagua=Bagua.KAN,
        element=FiveElement.WATER,
        feng_shui_role="玄武",
    ),
    Direction.NORTH_EAST: DirectionProfile(
        key=Direction.NORTH_EAST,
        label_ja="北東",
        start_deg=22.5,
        end_deg=67.5,
        bagua=Bagua.GEN,
        element=FiveElement.EARTH,
        feng_shui_role="鬼門",
    ),
    Direction.EAST: DirectionProfile(
        key=Direction.EAST,
        label_ja="東",
        start_deg=67.5,
        end_deg=112.5,
        bagua=Bagua.ZHEN,
        element=FiveElement.WOOD,
        feng_shui_role="青龍",
    ),
    Direction.SOUTH_EAST: DirectionProfile(
        key=Direction.SOUTH_EAST,
        label_ja="南東",
        start_deg=112.5,
        end_deg=157.5,
        bagua=Bagua.XUN,
        element=FiveElement.WOOD,
        feng_shui_role="風門",
    ),
    Direction.SOUTH: DirectionProfile(
        key=Direction.SOUTH,
        label_ja="南",
        start_deg=157.5,
        end_deg=202.5,
        bagua=Bagua.LI,
        element=FiveElement.FIRE,
        feng_shui_role="朱雀",
    ),
    Direction.SOUTH_WEST: DirectionProfile(
        key=Direction.SOUTH_WEST,
        label_ja="南西",
        start_deg=202.5,
        end_deg=247.5,
        bagua=Bagua.KUN,
        element=FiveElement.EARTH,
        feng_shui_role="裏鬼門",
    ),
    Direction.WEST: DirectionProfile(
        key=Direction.WEST,
        label_ja="西",
        start_deg=247.5,
        end_deg=292.5,
        bagua=Bagua.DUI,
        element=FiveElement.METAL,
        feng_shui_role="白虎",
    ),
    Direction.NORTH_WEST: DirectionProfile(
        key=Direction.NORTH_WEST,
        label_ja="北西",
        start_deg=292.5,
        end_deg=337.5,
        bagua=Bagua.QIAN,
        element=FiveElement.METAL,
        feng_shui_role="天門",
    ),
}


def normalize_bearing(bearing: float) -> float:
    normalized = bearing % 360.0
    return normalized if normalized >= 0 else normalized + 360.0


def bearing_to_direction(bearing: float) -> Direction:
    normalized = normalize_bearing(bearing)
    for direction, profile in DIRECTION_PROFILES.items():
        if profile.contains(normalized):
            return direction
    raise ValueError(f"No direction profile found for bearing: {bearing}")


def get_direction_profile(direction: Direction | str) -> DirectionProfile:
    direction_enum = direction if isinstance(direction, Direction) else Direction(direction)
    return DIRECTION_PROFILES[direction_enum]