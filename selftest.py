"""Sifat nazorati: savollar, tarjimalar, ball hisobi va natija matni.

Yangi savol yoki matn qo'shgandan keyin shuni ishlating:
    ./venv/bin/python selftest.py

Tekshiriladi:
  * har bir element ikkala tilda bor va bo'sh emas
  * takrorlangan yoki yo'nalishsiz savol yo'q
  * teskari elementlar yetarli (bir xil javob bosib chiqishni jazolaydi)
  * ball chegaralari to'g'ri: eng past 0 dan, a'lo 100 gacha
  * natija matnida HTML teglar yopilgan va Telegram cheklovidan oshmaydi
  * matnda adashib qolgan boshqa alifbo belgilari yo'q
  * o'zbekcha apostroflar to'g'ri: o va g harflaridan keyin bir xil belgi,
    tutuq belgisi (ma'lumot, e'tibor) esa boshqa belgi bilan yoziladi
"""
import re
import sys

import report
from locales import LANGS, STRINGS
from psytests import AGE_ADVICE, AGE_GROUPS, ORDER, REGISTRY, score
from psytests.base import LANGS as ITEM_LANGS

FAILURES: list[str] = []
FOREIGN = re.compile(r"[　-鿿豈-﫿]")
TAG = re.compile(r"</?([a-z]+)>")
TELEGRAM_LIMIT = 4096


def check(label: str, ok: bool, detail: str = "") -> None:
    print(("  ✅ " if ok else "  ❌ ") + label + ("" if ok else f"  — {detail}"))
    if not ok:
        FAILURES.append(label)


def bilingual_strings():
    """Loyihadagi barcha ikki tilli matnlarni (yo'l, qiymat) ko'rinishida beradi."""
    for key, value in STRINGS.items():
        yield f"locales.{key}", value
    for test in REGISTRY.values():
        for field in ("title", "tagline", "intro", "source", "minutes"):
            yield f"{test.key}.{field}", getattr(test, field)

        for key, scale in test.scales.items():
            yield f"{test.key}.{key}.name", scale.name
            if scale.note:
                yield f"{test.key}.{key}.note", scale.note
            for level, text in scale.levels.items():
                yield f"{test.key}.{key}.{level}", text
        for i, item in enumerate(test.items):
            yield f"{test.key}.item[{i}]", item.text
    for code, label in AGE_GROUPS["self"] + AGE_GROUPS["child"]:
        yield f"age.{code}", label
    for code, text in AGE_ADVICE.items():
        yield f"advice.{code}", text
    for _, _, name, note in report.BANDS:
        yield "band.name", name
        yield "band.note", note


def check_translations() -> None:
    missing, empty, foreign, bad_tags = [], [], [], []
    total = 0
    for path, value in bilingual_strings():
        total += 1
        for lang in ITEM_LANGS:
            text = value.get(lang)
            if text is None:
                missing.append(f"{path}[{lang}]")
                continue
            if not text.strip():
                empty.append(f"{path}[{lang}]")
            if FOREIGN.search(text):
                foreign.append(f"{path}[{lang}]")
            opened = [m for m in TAG.finditer(text)]
            depth = 0
            for m in opened:
                depth += -1 if m.group(0).startswith("</") else 1
            if depth != 0:
                bad_tags.append(f"{path}[{lang}]")

    print(f"  ℹ️  jami {total} ta ikki tilli matn tekshirildi")
    check("hamma matn ikkala tilda bor", not missing, ", ".join(missing[:5]))
    check("bo‘sh matn yo‘q", not empty, ", ".join(empty[:5]))
    check("begona alifbo belgilari yo‘q", not foreign, ", ".join(foreign[:5]))
    check("HTML teglar yopilgan", not bad_tags, ", ".join(bad_tags[:5]))


# Belgilar ataylab \u ko'rinishida yozilgan: matn ustidan avtomatik
# tuzatish yurgizilsa ham bu tekshiruvning o'zi buzilmasin.
OQ = "‘"     # o va g harflaridan keyin keladigani
TUTUQ = "’"  # tutuq belgisi: ma'lumot, e'tibor, mas'uliyat


def check_apostrophes() -> None:
    """o‘/g‘ dan keyin U+2018, boshqa joyda tutuq belgisi U+2019 bo‘lishi kerak."""
    wrong = []
    pattern = re.compile(f"(.)([{OQ}{TUTUQ}])")
    for path, value in bilingual_strings():
        text = value.get("uz", "")
        for m in pattern.finditer(text):
            prev, mark = m.group(1), m.group(2)
            expected = OQ if prev in "oOgG" else TUTUQ
            if mark != expected:
                wrong.append(f"{path}: …{text[max(0, m.start() - 8):m.end() + 8]}…")
    check("o‘zbekcha apostroflar to‘g‘ri", not wrong, " | ".join(wrong[:3]))


# Kitobiy yoki noto'g'ri ishlatiladigan so'zlar. Bot matni oddiy odam
# gapiradigan tilda bo'lishi kerak — bu ro'yxat shuni ushlab turadi.
BANNED_UZ = {
    "izchil": "«to‘xtamay», «doim», «bir tekis» deng",
    "izchillik": "«doimiylik» yoki «bir xillik» deng",
    "bashoratchi": "o‘zbekchada bu «folbin» degani — «ko‘rsatadigan omil» deng",
    "kechinma": "«his-tuyg‘u» deng",
    "o‘zgalar": "«boshqalar» deng",
    "mulohaza": "«fikr yuritish» deng",
    "salohiyatli": "«qobiliyatli» deng",
}

#: Bitta daraja izohi shundan uzun bo'lmasin (belgi).
MAX_LEVEL_LEN = 300
#: Butun natija shundan uzun bo'lmasin (belgi) — bitta ekranga sig'sin.
MAX_RESULT_LEN = 1900


def check_plain_language() -> None:
    hits = []
    for path, value in bilingual_strings():
        text = value.get("uz", "").lower()
        for word, hint in BANNED_UZ.items():
            if re.search(rf"\b{re.escape(word)}", text):
                hits.append(f"{path}: «{word}» — {hint}")
    check("kitobiy so‘zlar ishlatilmagan", not hits, " | ".join(hits[:3]))


def check_lengths() -> None:
    long_ones = []
    for test in REGISTRY.values():
        for key, scale in test.scales.items():
            for level, text in scale.levels.items():
                for lang in ITEM_LANGS:
                    if len(text[lang]) > MAX_LEVEL_LEN:
                        long_ones.append(
                            f"{test.key}.{key}.{level}[{lang}]={len(text[lang])}"
                        )
    check(f"daraja izohlari {MAX_LEVEL_LEN} belgidan qisqa", not long_ones,
          ", ".join(long_ones[:4]))


def check_answers() -> None:
    """Har bir savolning javob variantlari to'g'ri yig'ilganini tekshiradi."""
    problems, samples = [], []
    for key in ORDER:
        test = REGISTRY[key]
        for i, item in enumerate(test.items):
            for lang in ITEM_LANGS:
                opts = item.answers(lang)
                if len(opts) != 5:
                    problems.append(f"{key}.item[{i}][{lang}]: {len(opts)} variant")
                for opt in opts:
                    body = opt.split(" ", 1)[1] if " " in opt else ""
                    if not body.strip():
                        problems.append(f"{key}.item[{i}][{lang}]: bo‘sh variant")
                    if "{" in opt or "}" in opt:
                        problems.append(f"{key}.item[{i}][{lang}]: shablon to‘lmagan")
                    if "  " in opt:
                        problems.append(f"{key}.item[{i}][{lang}]: qo‘sh probel")
                    if len(opt) > 60:
                        problems.append(
                            f"{key}.item[{i}][{lang}]: juda uzun ({len(opt)})")
                if len(set(opts)) != len(opts):
                    problems.append(f"{key}.item[{i}][{lang}]: takroriy variant")
            # fe'l shakli kerak bo'lgan turlarda u berilganmi
            if item.kind in ("freq", "deg") and not (item.yes and item.no):
                problems.append(f"{key}.item[{i}]: yes/no shakli yo‘q")
        samples.append(f"{key}: «{tr_uz(test.items[0].text)}» → "
                       + " / ".join(a.split(" ", 1)[1] for a in test.items[0].answers("uz")))

    for line in samples:
        print(f"  ℹ️  {line}")
    check("javob variantlari to‘g‘ri yig‘ildi", not problems, " | ".join(problems[:4]))


def tr_uz(value: dict) -> str:
    return value.get("uz", "")


def check_structure() -> None:
    check("menyu tartibi reyestrga mos", set(ORDER) == set(REGISTRY),
          f"{set(ORDER) ^ set(REGISTRY)}")

    for key in ORDER:
        test = REGISTRY[key]
        counts: dict[str, int] = {}
        for item in test.items:
            counts[item.scale] = counts.get(item.scale, 0) + 1

        texts = [item.text["uz"] for item in test.items]
        reversed_n = sum(1 for i in test.items if i.reverse)
        missing_scales = set(test.scales) - set(counts)
        missing_levels = [
            f"{s}.{lvl}"
            for s, scale in test.scales.items()
            for lvl in (("high", "mid", "low") if test.kind == "traits" else
                        ("high",) if test.kind == "interests" else
                        ("high", "low"))
            if lvl not in scale.levels
        ]

        print(f"  ℹ️  {key}: {test.size} savol · {len(test.scales)} shkala · "
              f"{reversed_n} teskari · shkala bo‘yicha {sorted(counts.values())}")
        check(f"{key}: savollar yetarli (20+)", test.size >= 20, str(test.size))
        check(f"{key}: har bir shkalada savol bor", not missing_scales,
              str(missing_scales))
        check(f"{key}: takrorlangan savol yo‘q", len(texts) == len(set(texts)))
        check(f"{key}: kerakli darajalar yozilgan", not missing_levels,
              str(missing_levels[:5]))
        if test.kind != "interests":
            check(f"{key}: teskari savollar bor", reversed_n >= 3, str(reversed_n))


def check_scoring() -> None:
    for key in ORDER:
        test = REGISTRY[key]
        n, mx = test.size, test.max_answer

        perfect = score(test, [0 if i.reverse else mx for i in test.items])
        worst = score(test, [mx if i.reverse else 0 for i in test.items])
        mid = score(test, [mx // 2] * n)
        naive = score(test, [mx] * n)

        check(f"{key}: a’lo javobda shkalalar 100%",
              all(abs(v - 100) < 0.01 for v in perfect["scales"].values()))
        check(f"{key}: eng past javobda shkalalar 0%",
              all(abs(v) < 0.01 for v in worst["scales"].values()))
        check(f"{key}: o‘rta javobda 50%",
              all(abs(v - 50) < 0.01 for v in mid["scales"].values()))

        if test.kind == "index":
            check(f"{key}: umumiy ball 100", abs(perfect["total"] - 100) < 0.01,
                  str(perfect["total"]))
            check(f"{key}: hammasiga-5 jazolanadi",
                  naive["total"] < perfect["total"] - 5,
                  f"{naive['total']} vs {perfect['total']}")
            print(f"  ℹ️  {key}: eng past {worst['total']:.1f} · "
                  f"o‘rta {mid['total']:.1f} · hammasiga-5 {naive['total']:.1f} · "
                  f"maksimal {perfect['total']:.1f}")
        else:
            check(f"{key}: umumiy ball chiqarilmaydi", "total" not in perfect)


def check_reports() -> None:
    for key in ORDER:
        test = REGISTRY[key]
        age = None
        if test.ask_age:
            age = AGE_GROUPS[test.subject][1][0]

        for pattern_name, answers in (
            ("a’lo", [0 if i.reverse else test.max_answer for i in test.items]),
            ("o‘rta", [test.max_answer // 2] * test.size),
            ("past", [test.max_answer if i.reverse else 0 for i in test.items]),
        ):
            result = score(test, answers)
            for lang in LANGS:
                text = report.render(test, result, lang, age)
                depth = 0
                for m in TAG.finditer(text):
                    depth += -1 if m.group(0).startswith("</") else 1
                check(
                    f"{key}/{lang}/{pattern_name}: HTML butun",
                    depth == 0, f"depth={depth}",
                )
                check(
                    f"{key}/{lang}/{pattern_name}: natija qisqa "
                    f"({MAX_RESULT_LEN} belgidan kam)",
                    len(text) <= MAX_RESULT_LEN, f"{len(text)} belgi",
                )
                if pattern_name == "o‘rta":
                    print(f"  ℹ️  {key}/{lang}: natija {len(text)} belgi")


if __name__ == "__main__":
    print("Tarjimalar:")
    check_translations()
    print("Apostroflar:")
    check_apostrophes()
    print("Oddiy til:")
    check_plain_language()
    print("Uzunlik:")
    check_lengths()
    print("Javob variantlari:")
    check_answers()
    print("Tuzilma:")
    check_structure()
    print("Ball hisobi:")
    check_scoring()
    print("Natija matni:")
    check_reports()

    print()
    if FAILURES:
        print(f"❌ {len(FAILURES)} ta muammo")
        sys.exit(1)
    print("✅ Hammasi joyida.")
