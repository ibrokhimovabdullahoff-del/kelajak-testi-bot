"""Inline klaviaturalar. Hamma matn tilga bog'liq."""
from __future__ import annotations

from urllib.parse import quote

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from config import BOT_USERNAME
from locales import LANGS, t, tr
from psytests import AGE_GROUPS, ORDER, REGISTRY


def language_menu() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for code, label in LANGS.items():
        builder.button(text=label, callback_data=f"lang:{code}")
    builder.adjust(2)
    return builder.as_markup()


def main_menu(lang: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for key in ORDER:
        test = REGISTRY[key]
        builder.button(
            text=f"{test.emoji} {tr(test.title, lang)}",
            callback_data=f"test:{key}",
        )
    builder.button(text=t("btn_results", lang), callback_data="nav:history")
    builder.button(text=t("btn_about", lang), callback_data="nav:about")
    builder.button(text=t("btn_language", lang), callback_data="nav:lang")
    builder.adjust(*([1] * len(ORDER)), 2, 1)
    return builder.as_markup()


def test_card(test_key: str, lang: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=t("btn_start_test", lang), callback_data=f"go:{test_key}")
    builder.button(text=t("btn_source", lang), callback_data=f"src:{test_key}")
    builder.button(text=t("btn_back", lang), callback_data="nav:menu")
    builder.adjust(1, 2)
    return builder.as_markup()


def source_card(test_key: str, lang: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=t("btn_start_test", lang), callback_data=f"go:{test_key}")
    builder.button(text=t("btn_back", lang), callback_data=f"test:{test_key}")
    builder.adjust(1, 1)
    return builder.as_markup()


def age_menu(subject: str, lang: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for code, label in AGE_GROUPS[subject]:
        builder.button(text=tr(label, lang), callback_data=f"age:{code}")
    builder.button(text=t("btn_back", lang), callback_data="nav:menu")
    builder.adjust(2, 2, 1)
    return builder.as_markup()


def answer_menu(test_key: str, index: int, lang: str) -> InlineKeyboardMarkup:
    test = REGISTRY[test_key]
    builder = InlineKeyboardBuilder()
    for value, anchor in enumerate(test.anchors):
        builder.button(text=tr(anchor, lang), callback_data=f"ans:{index}:{value}")
    builder.adjust(1)
    row = []
    if index > 0:
        row.append(InlineKeyboardButton(text=t("btn_back", lang), callback_data="back"))
    row.append(InlineKeyboardButton(text=t("btn_cancel", lang), callback_data="nav:cancel"))
    builder.row(*row)
    return builder.as_markup()


def result_menu(test_key: str, lang: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=t("btn_retake", lang), callback_data=f"go:{test_key}")
    builder.button(text=t("btn_other_tests", lang), callback_data="nav:menu")
    if BOT_USERNAME:
        share = quote(t("share_text", lang))
        builder.button(
            text=t("btn_share", lang),
            url=f"https://t.me/share/url?url=https://t.me/{BOT_USERNAME}&text={share}",
        )
    builder.adjust(1)
    return builder.as_markup()


def back_to_menu(lang: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=t("btn_menu", lang), callback_data="nav:menu")
    return builder.as_markup()


# --- Admin (faqat o'zbekcha) ------------------------------------------------


def admin_menu() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="📊 Statistika", callback_data="adm:stats")
    builder.button(text="📣 Xabar yuborish", callback_data="adm:broadcast")
    builder.adjust(1)
    return builder.as_markup()


def broadcast_targets() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🌍 Hammaga", callback_data="admto:all")
    builder.button(text="🇺🇿 Faqat o‘zbekcha", callback_data="admto:uz")
    builder.button(text="🇷🇺 Faqat ruscha", callback_data="admto:ru")
    builder.adjust(1)
    return builder.as_markup()


def broadcast_confirm() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Ha, yuborilsin", callback_data="adm:send")
    builder.button(text="❌ Bekor", callback_data="adm:cancel")
    builder.adjust(2)
    return builder.as_markup()
