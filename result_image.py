"""Natija sertifikati — 1080×1920 PNG, Instagram va Telegram Stories uchun.

Ikki qism:
  build_card() — saqlangan natijadan rasmga nima yozilishini tanlaydi;
  render()     — shablon ustiga chizadi va PNG baytlarini qaytaradi.

Ataylab qo'yilgan qoidalar — rasmni odam faxr bilan joylashi kerak:
  * past ball hech qachon asosiy raqam bo'lmaydi: taxminiy IQ faqat 100 va
    undan yuqori bo'lsa, 0–100 indeks faqat 70 va undan yuqori bo'lsa
    ko'rsatiladi; qolgan hollarda eng kuchli tomon nomi yoziladi;
  * rasmda foizlar yo'q, "yana bir kuchli tomon" esa faqat 0 dan katta
    bo'lsa aytiladi — 0 foizli yo'nalish rasmga chiqmaydi;
  * hamma matn avtomatik qatorlarga bo'linadi, sig'masa shrift kichrayadi.

Shriftlar `assets/fonts/` da (SIL Open Font License, o'zgartirilmagan):
Playfair Display — sarlavhalar, Montserrat — qolgan matn. Montserrat
o'zbek lotin va kirill (ў қ ғ ҳ) harflarining hammasini qamraydi, shuning
uchun foydalanuvchi ismi doim shu shriftda yoziladi.
"""
from __future__ import annotations

import io
import threading
from dataclasses import dataclass
from datetime import date
from functools import lru_cache
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

import profiles
from config import IQ_KEY
from locales import t, tr
from psytests import REGISTRY
from psytests.insights import FALLBACK, IQ_LEVELS
from psytests.iq import KINDS, TOTAL as IQ_TOTAL

ROOT = Path(__file__).resolve().parent
TEMPLATE = ROOT / "assets" / "result-image" / "result-image.png"
SERIF = ROOT / "assets" / "fonts" / "PlayfairDisplay.ttf"
SANS = ROOT / "assets" / "fonts" / "Montserrat.ttf"

W, H = 1080, 1920
#: Chap va o'ng chekka — shablon ramkasi va burchak naqshlaridan uzoqroq.
MARGIN = 118
TEXT_W = W - 2 * MARGIN
#: Shablondagi naqshlar: tepadagi 170 px gacha, pastki nur 1650 px dan.
TOP_Y = 236
BOTTOM_Y = 1540

#: Shundan past taxminiy IQ raqam sifatida yozilmaydi.
IQ_NUMBER_MIN = 100
#: Shundan past 0–100 indeks yozilmaydi.
INDEX_NUMBER_MIN = 70
#: Ism shundan uzun bo'lsa qisqartiriladi.
NAME_MAX = 34

#: Rasm bot ishini to'xtatmaslik uchun alohida oqimda chiziladi. Keshdagi
#: shriftlar (FreeType) bir vaqtda ikki oqimdan ishlatilishga mo'ljallanmagan,
#: shuning uchun chizish navbat bilan bo'ladi (bittasi ~0.4 soniya).
_render_lock = threading.Lock()

GOLD = (231, 193, 115)
GOLD_LIGHT = (248, 226, 170)
IVORY = (240, 236, 226)
MUTED = (176, 184, 204)


@dataclass
class Card:
    title: str
    label: str
    headline: str
    lines: list[str]
    pill: str | None = None
    #: Sarlavha raqam (taxminiy IQ) — juda katta yoziladi.
    number: bool = False
    #: Ikkinchi ko'rsatkich (yorliq, qiymat) — masalan, IQ testidagi to'g'ri
    #: javoblar soni. Sarlavha ostida, taxminiy IQ uslubida yoziladi.
    stat: tuple[str, str] | None = None


# --- Nima yoziladi -----------------------------------------------------------


def _plain(name: str) -> str:
    """"Amaliy (Realistic)" → "Amaliy": rasmda qavsdagi inglizcha nom shart emas."""
    return name.split(" (")[0].strip()


def _fallback(title: str, lang: str) -> Card:
    return Card(title, t("card_label_strength", lang), tr(FALLBACK.name, lang),
                [tr(FALLBACK.line, lang), t("card_fallback_line", lang)])


def build_card(test_key: str, total: float | None, details: dict, lang: str, *,
               full: bool = False, show_score: bool = True) -> Card:
    """Saqlangan natijadan sertifikat mazmuni.

    details — `results.scales` JSON: psixologik testlarda yo'nalish → foiz,
    IQ da esa natija lug'ati (iq, kinds, ...).
    full — to'liq tahlil ochiqmi (IQ da taxminiy IQ faqat shunda yoziladi).
    show_score — IQ da to'g'ri javoblar soni ko'rsatilsinmi (foydalanuvchi
    "Ballni yashirish" tugmasi bilan o'chira oladi).

    Farzand testida sertifikatda bolaning hech qanday natijasi bo'lmaydi —
    faqat ota-onaning neytral kartasi.
    """
    if test_key == IQ_KEY:
        return _iq_card(details, lang, full=full, show_score=show_score)

    test = REGISTRY[test_key]
    title = tr(test.title, lang)
    if test.subject == "child":
        return Card(title, t("card_label_parent", lang), t("card_parent_name", lang),
                    [t("card_parent_line", lang), t("card_parent_line2", lang)])

    scores = {key: float(details.get(key) or 0) for key in test.scales}
    if max(scores.values(), default=0) < 0.5:
        return _fallback(title, lang)
    order = profiles.ranked(test_key, scores)
    top = order[0]
    arch = profiles.archetype(test_key, scores)
    lines = [tr(arch.line, lang)]

    def name(key: str) -> str:
        return _plain(tr(test.scales[key].name, lang))

    if test.kind == "interests":
        # Holland kodi — to'liq tahlilda; sertifikatda faqat eng yaqin yo'nalish.
        return Card(title, t("card_label_career", lang), tr(arch.name, lang), lines,
                    pill=name(top) if profiles.is_strong(scores[top]) else None)

    if test.kind == "traits":
        return Card(title, t("card_label_type", lang), tr(arch.name, lang), lines, pill=name(top))

    if total is not None and total >= INDEX_NUMBER_MIN:
        pill = t("card_index", lang, score=round(total))
    else:
        pill = name(top) if profiles.is_strong(scores[top]) else None
    return Card(title, t("card_label_strength", lang), tr(arch.name, lang), lines, pill=pill)


def _iq_card(details: dict, lang: str, *, full: bool, show_score: bool) -> Card:
    title = t("iq_title", lang)
    iq = int(details.get("iq") or 0)
    best = profiles.iq_best(details)
    correct = int(details.get("correct") or 0)
    total = int(details.get("total") or IQ_TOTAL)
    # Yarmidan kam to'g'ri bo'lsa, ball katta raqam bo'lib emas, oddiy qator
    # bo'lib yoziladi — past natija hech qachon sertifikatdagi asosiy raqam emas.
    strong = correct * 2 >= total
    stat = ((t("card_label_correct", lang), t("card_score", lang, correct=correct, total=total))
            if show_score and strong else None)
    if full and show_score and iq >= IQ_NUMBER_MIN:
        # To'liq tahlil ochiq: taxminiy IQ sarlavhada (faqat 100 va undan yuqori).
        _, level, line = next(item for item in IQ_LEVELS if iq >= item[0])
        second = (t("card_iq_best", lang, name=tr(KINDS[best].name, lang)) if best
                  else t("card_iq_generic", lang))
        return Card(title, t("card_label_iq", lang), str(iq), [tr(line, lang), second],
                    pill=tr(level, lang), number=True, stat=stat)
    arch = profiles.archetype(IQ_KEY, details)
    lines = [tr(arch.line, lang)]
    if show_score and not strong:
        lines.append(t("card_score_line", lang, correct=correct, total=total))
    elif not best:
        lines.append(t("card_iq_generic", lang))
    return Card(title, t("card_label_strength", lang), tr(arch.name, lang), lines, stat=stat)


# --- Shrift va matn ----------------------------------------------------------


@lru_cache(maxsize=128)
def _font(path: Path, size: int, weight: int) -> ImageFont.FreeTypeFont:
    font = ImageFont.truetype(str(path), size)
    try:
        font.set_variation_by_axes([weight])
    except (OSError, ValueError):
        pass  # eski FreeType: shriftning odatiy qalinligi ishlatiladi
    return font


def _glyph(path: Path, ch: str) -> bytes:
    image = Image.new("L", (64, 64))
    ImageDraw.Draw(image).text((8, 0), ch, font=_font(path, 40, 400), fill=255)
    return image.tobytes()


@lru_cache(maxsize=4096)
def _has_glyph(path: Path, ch: str) -> bool:
    if ch.isspace():
        return True
    # Shriftda yo'q belgi "yo'q" qutisi (.notdef) bo'lib chiziladi —
    # uni aniq yo'q belgi bilan solishtiramiz.
    return _glyph(path, ch) != _glyph(path, "\U000F0000")


def clean_name(name: str | None) -> str | None:
    """Telegram ismidan shrift chiza olmaydigan belgilarni (emoji va h.k.) olib tashlaydi."""
    if not name:
        return None
    kept = "".join(ch for ch in name if _has_glyph(SANS, ch))
    kept = " ".join(kept.split())
    if len(kept) > NAME_MAX:
        kept = kept[:NAME_MAX - 1].rstrip() + "…"
    return kept or None


def _wrap_greedy(text: str, font: ImageFont.FreeTypeFont, width: int) -> list[str]:
    lines: list[str] = []
    current = ""
    # Faqat oddiy probel bo'yicha bo'linadi: "10\u00a0kishidan" kabi bog'langan
    # so'zlar bir qatorda qoladi.
    for word in (w for w in text.split(" ") if w):
        candidate = f"{current} {word}" if current else word
        if font.getlength(candidate) <= width:
            current = candidate
            continue
        if current:
            lines.append(current)
        # Bitta so'zning o'zi qatorga sig'masa — harflab bo'lamiz.
        while font.getlength(word) > width:
            cut = max(1, next(i for i in range(len(word), 0, -1)
                               if font.getlength(word[:i]) <= width))
            lines.append(word[:cut])
            word = word[cut:]
        current = word
    if current:
        lines.append(current)
    return lines


def _wrap(text: str, font: ImageFont.FreeTypeFont, width: int) -> list[str]:
    """Qatorlarga bo'ladi va ularni teng uzunlikka yaqinlashtiradi.

    Oddiy bo'lishda oxirgi qatorda bitta so'z "osilib" qolishi mumkin
    ("тест / личности"). Shuning uchun qatorlar soni o'zgarmaydigan eng tor
    kenglikni topamiz — qatorlar bir-biriga yaqin uzunlikda chiqadi.
    """
    lines = _wrap_greedy(text, font, width)
    if len(lines) < 2:
        return lines
    # Pastki chegara — eng uzun so'z: undan torroq kenglikda so'z harflab
    # bo'linib ketardi ("Qonuniy / at").
    longest = max(font.getlength(word) for word in text.split(" ") if word)
    low, high = min(width, int(longest) + 1), width
    while low < high:
        mid = (low + high) // 2
        if len(_wrap_greedy(text, font, mid)) <= len(lines):
            high = mid
        else:
            low = mid + 1
    return _wrap_greedy(text, font, high)


def _fit(text: str, path: Path, weight: int, size: int, min_size: int, max_lines: int,
         width: int = TEXT_W) -> tuple[ImageFont.FreeTypeFont, list[str]]:
    """Matn max_lines qatorga sig'guncha shriftni kichraytiradi.

    Eng uzun so'z ham bir qatorga sig'ishi shart: so'zni harflab bo'lishdan
    ko'ra shriftni kichraytirgan yaxshi ("Целеустремлённый" butun qolsin).
    Harflab bo'lish faqat eng kichik o'lchamda ham sig'masa ishlatiladi.
    """
    words = [word for word in text.split(" ") if word]
    while True:
        font = _font(path, size, weight)
        lines = _wrap(text, font, width)
        words_fit = all(font.getlength(word) <= width for word in words)
        if (len(lines) <= max_lines and words_fit) or size <= min_size:
            return font, lines
        size -= 2


def _line_height(font: ImageFont.FreeTypeFont, spacing: float) -> int:
    ascent, descent = font.getmetrics()
    return round((ascent + descent) * spacing)


# --- Chizish -----------------------------------------------------------------


@lru_cache(maxsize=1)
def _background() -> Image.Image:
    """Shablon 1080×1920 ga "cover" usulida moslanadi (nisbat buzilmaydi)."""
    source = Image.open(TEMPLATE).convert("RGB")
    scale = max(W / source.width, H / source.height)
    size = (round(source.width * scale), round(source.height * scale))
    resized = source.resize(size, Image.LANCZOS)
    left, top = (size[0] - W) // 2, (size[1] - H) // 2
    return resized.crop((left, top, left + W, top + H))


class _Canvas:
    """Matnni ikki marta chizadi: avval xira soya, keyin rangli matn."""

    def __init__(self) -> None:
        self.ops: list[tuple] = []

    def text(self, y: int, line: str, font, fill, tracking: int = 0, glow: bool = False) -> None:
        self.ops.append(("text", y, line, font, fill, tracking, glow))

    def divider(self, y: int, half: int = 130) -> None:
        self.ops.append(("divider", y, half))

    def pill(self, y: int, line: str, font) -> int:
        pad_x, pad_y = 32, 16
        width = font.getlength(line) + 2 * pad_x
        height = _line_height(font, 1.0) + 2 * pad_y
        self.ops.append(("pill", y, line, font, width, height, pad_y))
        return height

    @staticmethod
    def _tracked_width(line: str, font, tracking: int) -> float:
        return sum(font.getlength(ch) for ch in line) + tracking * max(0, len(line) - 1)

    def _draw_text(self, draw, y, line, font, fill, tracking, dy=0) -> None:
        if not tracking:
            draw.text((W / 2, y + dy), line, font=font, fill=fill, anchor="ma")
            return
        x = (W - self._tracked_width(line, font, tracking)) / 2
        for ch in line:
            draw.text((x, y + dy), ch, font=font, fill=fill, anchor="la")
            x += font.getlength(ch) + tracking

    def paint(self, base: Image.Image) -> Image.Image:
        base = base.convert("RGBA")
        # 1) Soya: matn fonga "botib" ketmasin, pastki nur ustida ham o'qilsin.
        shadow = Image.new("RGBA", base.size, (0, 0, 0, 0))
        sdraw = ImageDraw.Draw(shadow)
        # 2) Sarlavha atrofidagi oltin nur.
        glow = Image.new("RGBA", base.size, (0, 0, 0, 0))
        gdraw = ImageDraw.Draw(glow)
        for op in self.ops:
            if op[0] == "text":
                _, y, line, font, _fill, tracking, is_glow = op
                self._draw_text(sdraw, y, line, font, (0, 0, 0, 200), tracking, dy=4)
                if is_glow:
                    self._draw_text(gdraw, y, line, font, GOLD + (150,), tracking)
        base = Image.alpha_composite(base, shadow.filter(ImageFilter.GaussianBlur(6)))
        base = Image.alpha_composite(base, glow.filter(ImageFilter.GaussianBlur(24)))

        draw = ImageDraw.Draw(base)
        for op in self.ops:
            kind = op[0]
            if kind == "text":
                _, y, line, font, fill, tracking, _ = op
                self._draw_text(draw, y, line, font, fill, tracking)
            elif kind == "divider":
                _, y, half = op
                cx = W // 2
                draw.line((cx - half, y, cx - 16, y), fill=GOLD, width=2)
                draw.line((cx + 16, y, cx + half, y), fill=GOLD, width=2)
                draw.polygon([(cx, y - 8), (cx + 8, y), (cx, y + 8), (cx - 8, y)], fill=GOLD)
            elif kind == "pill":
                _, y, line, font, width, height, pad_y = op
                x0 = (W - width) / 2
                draw.rounded_rectangle((x0, y, x0 + width, y + height), radius=height / 2,
                                       outline=GOLD, width=3, fill=(10, 18, 44, 150))
                draw.text((W / 2, y + pad_y), line, font=font, fill=GOLD_LIGHT, anchor="ma")
        return base


def _middle(card: Card, challenge: str, scale: float):
    """O'rta qism: yorliq, sarlavha, daraja, izohlar, chaqiriq. (balandlik, chizuvchi)."""
    def size(value: int) -> int:
        return max(12, round(value * scale))

    label = card.label.upper()
    label_size, label_track = size(29), size(5)
    label_font = _font(SANS, label_size, 600)
    while _Canvas._tracked_width(label, label_font, label_track) > TEXT_W and label_size > 16:
        label_track = max(1, label_track - 1)
        label_size -= 1
        label_font = _font(SANS, label_size, 600)
    if card.number:
        head_font = _font(SERIF, size(250), 800)
        head_lines = [card.headline]
    else:
        head_font, head_lines = _fit(card.headline, SERIF, 800, size(112), size(60), 3)
    pill_font = _font(SANS, size(31), 600)
    body_font = _font(SANS, size(38), 500)
    body = [_wrap(line, body_font, TEXT_W - 20) for line in card.lines]
    chal_font, chal_lines = _fit(challenge, SERIF, 700, size(48), size(34), 2)

    parts: list[tuple[int, callable]] = []

    def add(height: int, painter) -> None:
        parts.append((height, painter))

    lh = _line_height(label_font, 1.0)
    add(lh + size(22), lambda c, y: c.text(y, label, label_font, GOLD, tracking=label_track))

    if card.number:
        # Katta raqamda shrift tepasida bo'sh joy ko'p — raqamning o'zini
        # yorliq ostiga tortamiz, aks holda ular orasida katta bo'shliq qoladi.
        head_top, head_bottom = head_font.getbbox(card.headline, anchor="ma")[1::2]
        # Qiymatlar lambda'ga hozir bog'lanadi: chizish keyinroq bo'ladi va
        # shu funksiyadagi boshqa o'zgaruvchilar unga ta'sir qilmasligi kerak.
        add(head_bottom - head_top + size(40), lambda c, y, offset=head_top: c.text(
            y - offset, card.headline, head_font, GOLD_LIGHT, glow=True))
    else:
        hl = _line_height(head_font, 1.08)
        add(hl * len(head_lines) + size(26), lambda c, y: [
            c.text(y + i * hl, line, head_font, GOLD_LIGHT, glow=True)
            for i, line in enumerate(head_lines)])

    if card.pill:
        ph = _line_height(pill_font, 1.0) + 32
        add(ph + size(50 if not card.stat else 40), lambda c, y: c.pill(y, card.pill, pill_font))
    else:
        add(size(24), lambda c, y: None)

    if card.stat:
        # Taxminiy IQ bilan bir xil uslub: kichik yorliq, ostida katta raqam.
        stat_label, stat_value = card.stat[0].upper(), card.stat[1]
        stat_label_font = _font(SANS, size(25), 600)
        stat_font = _font(SERIF, size(96), 800)
        stat_top, stat_bottom = stat_font.getbbox(stat_value, anchor="ma")[1::2]
        stat_gap = _line_height(stat_label_font, 1.0) + size(12)
        stat_track = size(4)

        def paint_stat(c, y, offset=stat_top, gap=stat_gap, track=stat_track):
            c.text(y, stat_label, stat_label_font, GOLD, tracking=track)
            c.text(y + gap - offset, stat_value, stat_font, GOLD_LIGHT, glow=True)

        add(stat_gap + (stat_bottom - stat_top) + size(48), paint_stat)

    bl = _line_height(body_font, 1.28)
    for block in body:
        add(bl * len(block) + size(18), lambda c, y, block=block: [
            c.text(y + i * bl, line, body_font, IVORY) for i, line in enumerate(block)])

    add(size(40), lambda c, y: c.divider(y + size(10), half=70))
    cl = _line_height(chal_font, 1.15)
    add(cl * len(chal_lines), lambda c, y: [
        c.text(y + i * cl, line, chal_font, GOLD) for i, line in enumerate(chal_lines)])

    return sum(height for height, _ in parts), parts


def render(card: Card, lang: str, bot_username: str, name: str | None = None,
           when: date | None = None) -> bytes:
    """Sertifikatni chizadi va PNG baytlarini qaytaradi."""
    with _render_lock:
        return _render(card, lang, bot_username, name, when)


def _render(card: Card, lang: str, bot_username: str, name: str | None,
            when: date | None) -> bytes:
    canvas = _Canvas()

    # --- Tepa: sertifikat yorlig'i, test nomi, ism va sana ---------------
    y = TOP_Y
    kicker_font = _font(SANS, 27, 600)
    canvas.text(y, t("card_kicker", lang), kicker_font, GOLD, tracking=7)
    y += _line_height(kicker_font, 1.0) + 26
    title_font, title_lines = _fit(card.title, SERIF, 700, 72, 48, 2)
    tl = _line_height(title_font, 1.1)
    for i, line in enumerate(title_lines):
        canvas.text(y + i * tl, line, title_font, IVORY)
    y += tl * len(title_lines) + 22
    canvas.divider(y)
    y += 30
    who = " · ".join(part for part in (clean_name(name), (when or date.today()).strftime("%d.%m.%Y")) if part)
    who_font, who_lines = _fit(who, SANS, 500, 31, 24, 1)
    canvas.text(y, who_lines[0], who_font, MUTED)
    top_end = y + _line_height(who_font, 1.0)

    # --- Past: chaqiruv va bot manzili (shablondagi nurdan yuqorida) -----
    cta_font = _font(SANS, 31, 500)
    user_font, user_lines = _fit(f"@{bot_username.lstrip('@')}", SANS, 700, 46, 32, 1)
    canvas.text(BOTTOM_Y + 38, t("card_cta", lang), cta_font, IVORY)
    canvas.text(BOTTOM_Y + 38 + _line_height(cta_font, 1.25), user_lines[0], user_font, GOLD_LIGHT)

    # --- O'rta: sig'maguncha kichraytirib, bo'sh joy o'rtasiga qo'yamiz --
    area_top, area_bottom = top_end + 56, BOTTOM_Y - 20
    available = area_bottom - area_top
    scale = 1.0
    height, parts = _middle(card, t("card_challenge", lang), scale)
    while height > available and scale > 0.6:
        scale -= 0.04
        height, parts = _middle(card, t("card_challenge", lang), scale)
    y = area_top + max(0, (available - height) // 2)
    for part_height, painter in parts:
        painter(canvas, y)
        y += part_height

    image = canvas.paint(_background()).convert("RGB")
    buffer = io.BytesIO()
    image.save(buffer, format="PNG", compress_level=6)
    return buffer.getvalue()
