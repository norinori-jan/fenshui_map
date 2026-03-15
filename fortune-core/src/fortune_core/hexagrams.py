from dataclasses import dataclass
from functools import lru_cache
import json
from importlib.resources import files

from fortune_core.directions import Direction
from fortune_core.enums import Bagua, FiveElement


@dataclass(frozen=True)
class TrigramRecord:
    number: int
    bagua: Bagua
    name: str
    reading: str
    symbol: str
    attribute: str
    family: str
    lines: tuple[int, int, int]
    direction: Direction
    five_element: FiveElement


@dataclass(frozen=True)
class HexagramDirectionBinding:
    lower: Direction
    upper: Direction


@dataclass(frozen=True)
class HexagramElementBinding:
    lower: FiveElement
    upper: FiveElement


@dataclass(frozen=True)
class HexagramRecord:
    number: int
    name: str
    reading: str
    meaning: str
    judgement: str
    lower_trigram_number: int
    upper_trigram_number: int
    lower_bagua: Bagua
    upper_bagua: Bagua
    lines: tuple[int, int, int, int, int, int]
    direction: HexagramDirectionBinding
    five_element: HexagramElementBinding


@lru_cache(maxsize=1)
def _load_resource_payload() -> dict:
    resource = files("fortune_core.data").joinpath("hexagrams.json")
    return json.loads(resource.read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def load_trigrams() -> dict[int, TrigramRecord]:
    payload = _load_resource_payload()
    return {
        entry["number"]: TrigramRecord(
            number=entry["number"],
            bagua=Bagua(entry["bagua"]),
            name=entry["name"],
            reading=entry["reading"],
            symbol=entry["symbol"],
            attribute=entry["attribute"],
            family=entry["family"],
            lines=tuple(entry["lines"]),
            direction=Direction(entry["direction"]),
            five_element=FiveElement(entry["five_element"]),
        )
        for entry in payload["trigrams"]
    }


@lru_cache(maxsize=1)
def load_hexagrams() -> dict[tuple[int, int], HexagramRecord]:
    payload = _load_resource_payload()
    return {
        (entry["lower_trigram_number"], entry["upper_trigram_number"]): HexagramRecord(
            number=entry["number"],
            name=entry["name"],
            reading=entry["reading"],
            meaning=entry["meaning"],
            judgement=entry["judgement"],
            lower_trigram_number=entry["lower_trigram_number"],
            upper_trigram_number=entry["upper_trigram_number"],
            lower_bagua=Bagua(entry["lower_bagua"]),
            upper_bagua=Bagua(entry["upper_bagua"]),
            lines=tuple(entry["lines"]),
            direction=HexagramDirectionBinding(
                lower=Direction(entry["direction"]["lower"]),
                upper=Direction(entry["direction"]["upper"]),
            ),
            five_element=HexagramElementBinding(
                lower=FiveElement(entry["five_element"]["lower"]),
                upper=FiveElement(entry["five_element"]["upper"]),
            ),
        )
        for entry in payload["hexagrams"]
    }


def get_trigram(number: int) -> TrigramRecord:
    trigrams = load_trigrams()
    if number not in trigrams:
        raise ValueError(f"Trigram number must be between 1 and 8: {number}")
    return trigrams[number]


def get_hexagram(lower: int, upper: int) -> HexagramRecord:
    hexagrams = load_hexagrams()
    key = (lower, upper)
    if key not in hexagrams:
        raise ValueError(f"Hexagram combination not found: lower={lower}, upper={upper}")
    return hexagrams[key]


def get_hexagram_by_number(number: int) -> HexagramRecord:
    for hexagram in load_hexagrams().values():
        if hexagram.number == number:
            return hexagram
    raise ValueError(f"Hexagram number not found: {number}")


def get_changing_hexagram(lower: int, upper: int, changing_line: int) -> HexagramRecord:
    if changing_line < 1 or changing_line > 6:
        raise ValueError(f"Changing line must be between 1 and 6: {changing_line}")

    original_lines = list(get_trigram(lower).lines + get_trigram(upper).lines)
    index = changing_line - 1
    original_lines[index] = 1 - original_lines[index]
    new_lower = _lines_to_trigram_number(tuple(original_lines[:3]))
    new_upper = _lines_to_trigram_number(tuple(original_lines[3:]))
    return get_hexagram(new_lower, new_upper)


def _lines_to_trigram_number(lines: tuple[int, int, int] | list[int]) -> int:
    normalized_lines = tuple(lines)
    for number, trigram in load_trigrams().items():
        if trigram.lines == normalized_lines:
            return number
    raise ValueError(f"No trigram matches lines: {lines}")


def get_line_names() -> dict[int, str]:
    return {
        1: "初爻",
        2: "二爻",
        3: "三爻",
        4: "四爻",
        5: "五爻",
        6: "上爻",
    }