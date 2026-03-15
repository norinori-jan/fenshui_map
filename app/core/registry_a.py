from dataclasses import dataclass


@dataclass(frozen=True)
class DirectionProfile:
    key: str
    label_ja: str
    degrees: tuple[float, float]
    trigram: str
    element: str
    season: str
    feng_shui_role: str


@dataclass(frozen=True)
class FiveElementProfile:
    key: str
    label_ja: str
    generates: str
    controls: str


@dataclass(frozen=True)
class EarthlyBranchProfile:
    key: str
    label_ja: str
    direction: str
    element: str


FIVE_ELEMENTS: dict[str, FiveElementProfile] = {
    "wood": FiveElementProfile(key="wood", label_ja="木", generates="fire", controls="earth"),
    "fire": FiveElementProfile(key="fire", label_ja="火", generates="earth", controls="metal"),
    "earth": FiveElementProfile(key="earth", label_ja="土", generates="metal", controls="water"),
    "metal": FiveElementProfile(key="metal", label_ja="金", generates="water", controls="wood"),
    "water": FiveElementProfile(key="water", label_ja="水", generates="wood", controls="fire"),
}


DIRECTIONS: dict[str, DirectionProfile] = {
    "north": DirectionProfile(
        key="north",
        label_ja="北",
        degrees=(337.5, 22.5),
        trigram="坎",
        element="water",
        season="winter",
        feng_shui_role="玄武",
    ),
    "north_east": DirectionProfile(
        key="north_east",
        label_ja="北東",
        degrees=(22.5, 67.5),
        trigram="艮",
        element="earth",
        season="late_winter",
        feng_shui_role="鬼門",
    ),
    "east": DirectionProfile(
        key="east",
        label_ja="東",
        degrees=(67.5, 112.5),
        trigram="震",
        element="wood",
        season="spring",
        feng_shui_role="青龍",
    ),
    "south_east": DirectionProfile(
        key="south_east",
        label_ja="南東",
        degrees=(112.5, 157.5),
        trigram="巽",
        element="wood",
        season="late_spring",
        feng_shui_role="風門",
    ),
    "south": DirectionProfile(
        key="south",
        label_ja="南",
        degrees=(157.5, 202.5),
        trigram="離",
        element="fire",
        season="summer",
        feng_shui_role="朱雀",
    ),
    "south_west": DirectionProfile(
        key="south_west",
        label_ja="南西",
        degrees=(202.5, 247.5),
        trigram="坤",
        element="earth",
        season="late_summer",
        feng_shui_role="裏鬼門",
    ),
    "west": DirectionProfile(
        key="west",
        label_ja="西",
        degrees=(247.5, 292.5),
        trigram="兌",
        element="metal",
        season="autumn",
        feng_shui_role="白虎",
    ),
    "north_west": DirectionProfile(
        key="north_west",
        label_ja="北西",
        degrees=(292.5, 337.5),
        trigram="乾",
        element="metal",
        season="early_winter",
        feng_shui_role="天門",
    ),
}


EARTHLY_BRANCHES: dict[str, EarthlyBranchProfile] = {
    "zi": EarthlyBranchProfile(key="zi", label_ja="子", direction="north", element="water"),
    "chou": EarthlyBranchProfile(key="chou", label_ja="丑", direction="north_east", element="earth"),
    "yin": EarthlyBranchProfile(key="yin", label_ja="寅", direction="north_east", element="wood"),
    "mao": EarthlyBranchProfile(key="mao", label_ja="卯", direction="east", element="wood"),
    "chen": EarthlyBranchProfile(key="chen", label_ja="辰", direction="south_east", element="earth"),
    "si": EarthlyBranchProfile(key="si", label_ja="巳", direction="south_east", element="fire"),
    "wu": EarthlyBranchProfile(key="wu", label_ja="午", direction="south", element="fire"),
    "wei": EarthlyBranchProfile(key="wei", label_ja="未", direction="south_west", element="earth"),
    "shen": EarthlyBranchProfile(key="shen", label_ja="申", direction="south_west", element="metal"),
    "you": EarthlyBranchProfile(key="you", label_ja="酉", direction="west", element="metal"),
    "xu": EarthlyBranchProfile(key="xu", label_ja="戌", direction="north_west", element="earth"),
    "hai": EarthlyBranchProfile(key="hai", label_ja="亥", direction="north_west", element="water"),
}


def get_direction_profile(direction_key: str) -> DirectionProfile:
    return DIRECTIONS[direction_key]


def get_five_element_profile(element_key: str) -> FiveElementProfile:
    return FIVE_ELEMENTS[element_key]


def direction_to_compass_label(direction_key: str) -> str:
    return get_direction_profile(direction_key).label_ja