from fortune_core.directions import Direction
from fortune_core.enums import Bagua, FiveElement
from fortune_core.hexagrams import get_changing_hexagram, get_hexagram, get_hexagram_by_number, get_line_names, get_trigram, load_hexagrams, load_trigrams


def test_trigrams_and_hexagrams_are_loaded_from_resource():
    assert len(load_trigrams()) == 8
    assert len(load_hexagrams()) == 64


def test_get_trigram_returns_registry_bound_metadata():
    trigram = get_trigram(1)
    assert trigram.bagua == Bagua.QIAN
    assert trigram.direction == Direction.NORTH_WEST
    assert trigram.five_element == FiveElement.METAL


def test_get_hexagram_contains_shape_and_bindings():
    hexagram = get_hexagram(1, 1)
    assert hexagram.number == 1
    assert hexagram.name == "乾為天"
    assert hexagram.lines == (1, 1, 1, 1, 1, 1)
    assert hexagram.direction.lower == Direction.NORTH_WEST
    assert hexagram.five_element.upper == FiveElement.METAL


def test_get_hexagram_by_number_finds_existing_record():
    hexagram = get_hexagram_by_number(2)
    assert hexagram.name == "坤為地"
    assert hexagram.lines == (0, 0, 0, 0, 0, 0)


def test_get_changing_hexagram_flips_a_line():
    changed = get_changing_hexagram(1, 1, 1)
    assert changed.number == 10
    assert changed.name == "天沢履"


def test_line_names_are_exposed():
    assert get_line_names()[1] == "初爻"
    assert get_line_names()[6] == "上爻"