from enum import StrEnum


class FiveElement(StrEnum):
    WOOD = "wood"
    FIRE = "fire"
    EARTH = "earth"
    METAL = "metal"
    WATER = "water"

    @property
    def label_ja(self) -> str:
        return {
            FiveElement.WOOD: "木",
            FiveElement.FIRE: "火",
            FiveElement.EARTH: "土",
            FiveElement.METAL: "金",
            FiveElement.WATER: "水",
        }[self]


class Bagua(StrEnum):
    QIAN = "qian"
    DUI = "dui"
    LI = "li"
    ZHEN = "zhen"
    XUN = "xun"
    KAN = "kan"
    GEN = "gen"
    KUN = "kun"

    @property
    def label_ja(self) -> str:
        return {
            Bagua.QIAN: "乾",
            Bagua.DUI: "兌",
            Bagua.LI: "離",
            Bagua.ZHEN: "震",
            Bagua.XUN: "巽",
            Bagua.KAN: "坎",
            Bagua.GEN: "艮",
            Bagua.KUN: "坤",
        }[self]

    @property
    def symbol(self) -> str:
        return {
            Bagua.QIAN: "☰",
            Bagua.DUI: "☱",
            Bagua.LI: "☲",
            Bagua.ZHEN: "☳",
            Bagua.XUN: "☴",
            Bagua.KAN: "☵",
            Bagua.GEN: "☶",
            Bagua.KUN: "☷",
        }[self]

    @property
    def phenomenon_label_ja(self) -> str:
        return {
            Bagua.QIAN: "天",
            Bagua.DUI: "沢",
            Bagua.LI: "火",
            Bagua.ZHEN: "雷",
            Bagua.XUN: "風",
            Bagua.KAN: "水",
            Bagua.GEN: "山",
            Bagua.KUN: "地",
        }[self]