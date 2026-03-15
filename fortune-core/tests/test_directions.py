from fortune_core.calendar import EarthlyBranch, branch_to_direction_key
from fortune_core.directions import Direction, bearing_to_direction, get_direction_profile, normalize_bearing
from fortune_core.enums import Bagua, FiveElement


def test_normalize_bearing_wraps_values():
    assert normalize_bearing(361.0) == 1.0
    assert normalize_bearing(-10.0) == 350.0


def test_bearing_to_direction_returns_expected_sector():
    assert bearing_to_direction(0.0) == Direction.NORTH
    assert bearing_to_direction(90.0) == Direction.EAST
    assert bearing_to_direction(180.0) == Direction.SOUTH
    assert bearing_to_direction(270.0) == Direction.WEST


def test_direction_profile_contains_bagua_and_element():
    east = get_direction_profile(Direction.EAST)
    assert east.bagua == Bagua.ZHEN
    assert east.element == FiveElement.WOOD
    assert east.feng_shui_role == "青龍"


def test_earthly_branch_maps_to_direction():
    assert branch_to_direction_key(EarthlyBranch.ZI) == "north"
    assert branch_to_direction_key(EarthlyBranch.WU) == "south"