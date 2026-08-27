"""Inline klaviaturalar. Hamma matn tilga bog'liq."""
from __future__ import annotations

from urllib.parse import quote

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from config import BOT_USERNAME
from locales import LANGS, money, t, tr
from psytests import AGE_GROUPS, ORDER, REGISTRY


def language_menu() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for code, label in LANGS.items():
        builder.button(text=label, callback_data=f"lang:{code}")
    builder.adjust(2)
    return builder.as_markup()


def main_menu(
    lang: str,
    disabled: set[str] | None = None,
    locked: set[str] | None = None,
) -> InlineKeyboardMarkup:
    """Testlar ro'yxati.

    `locked` — hali sotib olinmagan pullik testlar; ular yonida qulf
    belgisi turadi, lekin menyudan yashirilmaydi: odam nima borligini
    ko'rsin, narxni esa kartochkada bilib oladi.
    """
    disabled = disabled or set()
    locked = locked or set()
    shown = [k for k in ORDER if k not in disabled]
    builder = InlineKeyboardBuilder()
    for key in shown:
        test = REGISTRY[key]
        mark = "🔒 " if key in locked else ""
        builder.button(
            text=f"{mark}{test.emoji} {tr(test.title, lang)}",
            callback_data=f"test:{key}",
        )
    builder.button(text=t("btn_results", lang), callback_data="nav:history")
    builder.button(text=t("btn_about", lang), callback_data="nav:about")
    builder.button(text=t("btn_language", lang), callback_data="nav:lang")
    builder.adjust(*([1] * len(shown)), 2, 1)
    return builder.as_markup()


def test_card(test_key: str, lang: str, locked: bool = False) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    if locked:
        builder.button(text=t("btn_pay", lang), callback_data=f"pay:{test_key}")
    else:
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
    """Javob tugmalari — har bir savol o'z variantlarini beradi."""
    item = REGISTRY[test_key].items[index]
    builder = InlineKeyboardBuilder()
    for value, text in enumerate(item.answers(lang)):
        builder.button(text=text, callback_data=f"ans:{index}:{value}")
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
    builder.button(text="📈 Tugatish darajasi", callback_data="adm:funnel")
    builder.button(text="👥 Oxirgi foydalanuvchilar", callback_data="adm:users")
    builder.button(text="🧩 Testlarni boshqarish", callback_data="adm:tests")
    builder.button(text="📥 Natijalarni yuklab olish", callback_data="adm:export")
    builder.button(text="📣 Xabar yuborish", callback_data="adm:broadcast")
    builder.button(text="💳 To‘lovlar", callback_data="adm:pay")
    builder.adjust(2, 2, 1, 1, 1)
    return builder.as_markup()


def admin_back() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="⬅️ Admin panel", callback_data="adm:home")
    return builder.as_markup()


def admin_tests(disabled: set[str]) -> InlineKeyboardMarkup:
    """Har bir test uchun: ko'rish va yoqish/o'chirish."""
    builder = InlineKeyboardBuilder()
    for key in ORDER:
        test = REGISTRY[key]
        mark = "🔴" if key in disabled else "🟢"
        builder.button(
            text=f"{mark} {test.emoji} {tr(test.title, 'uz')}",
            callback_data=f"admtest:{key}",
        )
    builder.button(text="⬅️ Admin panel", callback_data="adm:home")
    builder.adjust(1)
    return builder.as_markup()


def admin_test_one(test_key: str, disabled: bool, page: int = 0) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(
        text="🟢 Yoqish" if disabled else "🔴 O‘chirish",
        callback_data=f"admtoggle:{test_key}",
    )
    builder.button(text="📄 Savollarni ko‘rish", callback_data=f"admq:{test_key}:0")
    builder.button(text="⬅️ Testlar", callback_data="adm:tests")
    builder.adjust(1)
    return builder.as_markup()


def admin_questions(test_key: str, page: int, pages: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    row = []
    if page > 0:
        row.append(InlineKeyboardButton(
            text="⬅️", callback_data=f"admq:{test_key}:{page - 1}"))
    if page + 1 < pages:
        row.append(InlineKeyboardButton(
            text="➡️", callback_data=f"admq:{test_key}:{page + 1}"))
    if row:
        builder.row(*row)
    builder.row(InlineKeyboardButton(
        text="⬅️ Testga qaytish", callback_data=f"admtest:{test_key}"))
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


# --- To'lov -----------------------------------------------------------------


def paywall(
    test_key: str, lang: str, price_all: int | None = None
) -> InlineKeyboardMarkup:
    """Pullik test ochilishidan oldingi ekran."""
    builder = InlineKeyboardBuilder()
    builder.button(text=t("btn_pay", lang), callback_data=f"pay:{test_key}")
    if price_all:
        builder.button(
            text=t("btn_pay_all", lang, price=money(price_all)),
            callback_data="pay:all",
        )
    builder.button(text=t("btn_source", lang), callback_data=f"src:{test_key}")
    builder.button(text=t("btn_back", lang), callback_data="nav:menu")
    builder.adjust(1, 1, 2)
    return builder.as_markup()


def pay_links(
    payment_id: int, url: str, lang: str, invoice: bool = False
) -> InlineKeyboardMarkup:
    """To'lov havolasi va uni tekshirish tugmalari.

    "To'ladim" tugmasi zaxira yo'l: odatda huquqni Click'ning Complete
    so'rovi ochadi, lekin u kechiksa odam kutib qolmasligi kerak.
    """
    builder = InlineKeyboardBuilder()
    builder.button(text=t("btn_pay_open", lang), url=url)
    if invoice:
        builder.button(
            text=t("btn_pay_invoice", lang), callback_data=f"payinv:{payment_id}"
        )
    builder.button(text=t("btn_pay_check", lang), callback_data=f"paychk:{payment_id}")
    builder.button(text=t("btn_back", lang), callback_data="nav:menu")
    builder.adjust(1)
    return builder.as_markup()


def unlocked(test_key: str, lang: str) -> InlineKeyboardMarkup:
    """To'lov o'tgandan keyin — to'g'ridan-to'g'ri testga kirish."""
    builder = InlineKeyboardBuilder()
    if test_key and test_key != "all":
        builder.button(text=t("btn_open_test", lang), callback_data=f"go:{test_key}")
    builder.button(text=t("btn_menu", lang), callback_data="nav:menu")
    builder.adjust(1)
    return builder.as_markup()


# --- Admin: to'lovlar -------------------------------------------------------


def admin_payments(admin_pays: bool = False) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(
        text="🧪 Sinov rejimi: YOQIQ" if admin_pays else "🧪 Sinov rejimi: o‘chiq",
        callback_data="adm:testmode",
    )
    builder.button(text="🧾 Oxirgi to‘lovlar", callback_data="adm:paylist")
    builder.button(text="💰 Narxlarni o‘zgartirish", callback_data="adm:prices")
    builder.button(text="🎁 Pullik / bepul testlar", callback_data="adm:freetests")
    builder.button(text="🔓 Qo‘lda ochish", callback_data="adm:grant")
    builder.button(text="⬅️ Admin panel", callback_data="adm:home")
    builder.adjust(1)
    return builder.as_markup()


def admin_prices(products: list[tuple[str, str, int]]) -> InlineKeyboardMarkup:
    """products: (kalit, ko'rinadigan nom, joriy narx)."""
    builder = InlineKeyboardBuilder()
    for key, title, price in products:
        builder.button(
            text=f"{title} — {money(price)} so‘m", callback_data=f"admprice:{key}"
        )
    builder.button(text="⬅️ To‘lovlar", callback_data="adm:pay")
    builder.adjust(1)
    return builder.as_markup()


def admin_paid_tests(free: set[str]) -> InlineKeyboardMarkup:
    """Qaysi test pullik, qaysi biri bepul."""
    builder = InlineKeyboardBuilder()
    for key in ORDER:
        test = REGISTRY[key]
        mark = "🎁" if key in free else "💳"
        builder.button(
            text=f"{mark} {test.emoji} {tr(test.title, 'uz')}",
            callback_data=f"admfree:{key}",
        )
    builder.button(text="⬅️ To‘lovlar", callback_data="adm:pay")
    builder.adjust(1)
    return builder.as_markup()
