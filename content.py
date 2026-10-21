"""To'liq tahlil matnlari: `content/reports.toml` dan o'qiladi.

Egasi matnni kodga tegmasdan shu faylda tahrirlaydi. Bot ishga tushganda
fayl bir marta o'qiladi; `check()` hamma kerakli matn borligini tekshiradi
(selftest.py va phase1test.py chaqiradi).

    content.text("bigfive", "action", "C", "low")   -> {"uz": ..., "ru": ...}
    content.get("bigfive", "action", "C", "low", lang="ru")
"""
from __future__ import annotations

import tomllib
from pathlib import Path

PATH = Path(__file__).resolve().parent / "content" / "reports.toml"
LEVELS = ("high", "mid", "low")

with open(PATH, "rb") as _f:
    DATA: dict = tomllib.load(_f)


def text(*path: str) -> dict[str, str]:
    node = DATA
    for key in path:
        node = node[key]
    if not (isinstance(node, dict) and "uz" in node and "ru" in node):
        raise KeyError("/".join(path))
    return node


def get(*path: str, lang: str) -> str:
    value = text(*path)
    return value.get(lang) or value["uz"]


def items(*path: str) -> list[dict[str, str]]:
    node = DATA
    for key in path:
        node = node[key]
    return list(node)


def is_reviewed() -> bool:
    return bool(DATA.get("meta", {}).get("reviewed"))


def all_texts():
    """(yo'l, ikki tilli matn) — selftest shu orqali apostrof va uzunlikni tekshiradi."""
    def walk(node, path):
        if isinstance(node, dict):
            if "uz" in node and "ru" in node and all(isinstance(v, str) for v in node.values()):
                yield "content." + ".".join(path), node
                return
            for key, value in node.items():
                yield from walk(value, path + [str(key)])
        elif isinstance(node, list):
            for i, value in enumerate(node):
                yield from walk(value, path + [str(i)])
    for key, value in DATA.items():
        if key != "meta":
            yield from walk(value, [key])


def check() -> list[str]:
    """Yetishmayotgan matnlar ro'yxati (bo'sh — hammasi joyida)."""
    from psytests import ORDER, REGISTRY
    from psytests.iq import KINDS

    missing: list[str] = []

    def need(*path: str) -> None:
        try:
            value = text(*path)
            if not value["uz"].strip() or not value["ru"].strip():
                missing.append("/".join(path) + " (bo‘sh)")
        except (KeyError, TypeError):
            missing.append("/".join(path))

    for test_key in ["iq", *ORDER]:
        need("tests", test_key, "free")
        need("tests", test_key, "paid")
        try:
            if not items("tests", test_key, "bullets"):
                missing.append(f"tests/{test_key}/bullets")
        except KeyError:
            missing.append(f"tests/{test_key}/bullets")
    for kind in KINDS:
        need("iq", "kinds", kind, "meaning")
        need("iq", "kinds", kind, "train")

    traits = list(REGISTRY["bigfive"].scales)
    canonical = "EACSO"
    for i, a in enumerate(canonical):
        for b in canonical[i + 1:]:
            need("bigfive", "pairs", a + b, "name")
            need("bigfive", "pairs", a + b, "line")
    need("bigfive", "balanced", "name")
    need("bigfive", "balanced", "line")
    for trait in traits:
        for level in LEVELS:
            need("bigfive", "action", trait, level)
        need("bigfive", "risk", trait, "high")
        need("bigfive", "risk", trait, "low")
        need("bigfive", "environment", trait)
        need("bigfive", "habit", trait)

    for kind in REGISTRY["career"].scales:
        for part in ("jobs", "study", "next"):
            need("career", part, kind)

    for scale in REGISTRY["future"].scales:
        need("future", scale, "research")
        for level in LEVELS:
            need("future", scale, level)

    for scale in REGISTRY["child"].scales:
        for level in LEVELS:
            need("child", scale, level)
    return missing
