from enum import StrEnum

from fortune_core.directions import Direction
from fortune_core.enums import FiveElement


class EarthlyBranch(StrEnum):
    ZI = "zi"
    CHOU = "chou"
    YIN = "yin"
    MAO = "mao"
    CHEN = "chen"
    SI = "si"
    WU = "wu"
    WEI = "wei"
    SHEN = "shen"
    YOU = "you"
    XU = "xu"
    HAI = "hai"

    @property
    def label_ja(self) -> str:
        return {
            EarthlyBranch.ZI: "子",
            EarthlyBranch.CHOU: "丑",
            EarthlyBranch.YIN: "寅",
            EarthlyBranch.MAO: "卯",
            EarthlyBranch.CHEN: "辰",
            EarthlyBranch.SI: "巳",
            EarthlyBranch.WU: "午",
            EarthlyBranch.WEI: "未",
            EarthlyBranch.SHEN: "申",
            EarthlyBranch.YOU: "酉",
            EarthlyBranch.XU: "戌",
            EarthlyBranch.HAI: "亥",
        }[self]


BRANCH_DIRECTION_MAP: dict[EarthlyBranch, Direction] = {
    EarthlyBranch.ZI: Direction.NORTH,
    EarthlyBranch.CHOU: Direction.NORTH_EAST,
    EarthlyBranch.YIN: Direction.NORTH_EAST,
    EarthlyBranch.MAO: Direction.EAST,
    EarthlyBranch.CHEN: Direction.SOUTH_EAST,
    EarthlyBranch.SI: Direction.SOUTH_EAST,
    EarthlyBranch.WU: Direction.SOUTH,
    EarthlyBranch.WEI: Direction.SOUTH_WEST,
    EarthlyBranch.SHEN: Direction.SOUTH_WEST,
    EarthlyBranch.YOU: Direction.WEST,
    EarthlyBranch.XU: Direction.NORTH_WEST,
    EarthlyBranch.HAI: Direction.NORTH_WEST,
}


BRANCH_ELEMENT_MAP: dict[EarthlyBranch, FiveElement] = {
    EarthlyBranch.ZI: FiveElement.WATER,
    EarthlyBranch.CHOU: FiveElement.EARTH,
    EarthlyBranch.YIN: FiveElement.WOOD,
    EarthlyBranch.MAO: FiveElement.WOOD,
    EarthlyBranch.CHEN: FiveElement.EARTH,
    EarthlyBranch.SI: FiveElement.FIRE,
    EarthlyBranch.WU: FiveElement.FIRE,
    EarthlyBranch.WEI: FiveElement.EARTH,
    EarthlyBranch.SHEN: FiveElement.METAL,
    EarthlyBranch.YOU: FiveElement.METAL,
    EarthlyBranch.XU: FiveElement.EARTH,
    EarthlyBranch.HAI: FiveElement.WATER,
}


def branch_to_direction_key(branch: EarthlyBranch | str) -> str:
    branch_enum = branch if isinstance(branch, EarthlyBranch) else EarthlyBranch(branch)
    return BRANCH_DIRECTION_MAP[branch_enum].value