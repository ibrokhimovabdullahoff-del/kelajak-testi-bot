"""Inline keyboards for the bot."""
from __future__ import annotations

from urllib.parse import quote

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from config import BOT_USERNAME, IQ_EMOJI, IQ_KEY, MENU_ORDER
from locales import LANGS, money, t, tr
from psytests import AGE_GROUPS, ORDER, REGISTRY
from report import next_test_title


def language_menu() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for code, label in LANGS.items():
        builder.button(text=label, callback_data=f"lang:{code}")
    builder.adjust(2)
    return builder.as_markup()


def test_size(test_key: str) -> int:
    if test_key == IQ_KEY:
        from psytests.iq import TOTAL
        return TOTAL
    return REGISTRY[test_key].size


def main_menu(lang: str, disabled: set[str] | None = None, resume: dict | None = None) -> InlineKeyboardMarkup:
    """Bosh menyu: tugallanmagan test (bo'lsa) tepada, keyin testlar — har biri alohida qatorda."""
    disabled = disabled or set()
    builder = InlineKeyboardBuilder()
    rows: list[int] = []
    if resume and resume.get("test_key") in [*MENU_ORDER] and resume["test_key"] not in disabled:
        key = resume["test_key"]
        builder.button(text=t("btn_resume", lang, done=len(resume["answers"]), total=test_size(key)),
                       callback_data=f"resume:{key}")
        rows.append(1)
    for key in MENU_ORDER:
        if key in disabled:
            continue
        builder.button(text=t(f"menu_{key}", lang), callback_data="iq:card" if key == IQ_KEY else f"test:{key}")
        rows.append(1)
    builder.button(text=t("btn_results", lang), callback_data="nav:history")
    builder.button(text=t("btn_invite", lang), callback_data="ref:menu")
    builder.button(text=t("btn_language", lang), callback_data="nav:lang")
    builder.button(text=t("btn_about", lang), callback_data="nav:about")
    builder.adjust(*rows, 2, 2)
    return builder.as_markup()


def test_card(test_key: str, lang: str, progress: dict | None = None) -> InlineKeyboardMarkup:
    """Test oldidan ekran: boshlash (yoki davom ettirish), manba, orqaga."""
    builder = InlineKeyboardBuilder()
    start = "iq:start" if test_key == IQ_KEY else f"go:{test_key}"
    if progress and progress.get("answers"):
        builder.button(text=t("btn_resume", lang, done=len(progress["answers"]), total=test_size(test_key)),
                       callback_data=f"resume:{test_key}")
        builder.button(text=t("btn_restart", lang), callback_data=start)
    else:
        builder.button(text=t("btn_start_test", lang), callback_data=start)
    if test_key != IQ_KEY:
        builder.button(text=t("btn_source", lang), callback_data=f"src:{test_key}")
    builder.button(text=t("btn_back", lang), callback_data="nav:menu")
    builder.adjust(1)
    return builder.as_markup()


def quit_menu(test_key: str, lang: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=t("btn_quit_yes", lang), callback_data=f"quit:yes:{test_key}")
    builder.button(text=t("btn_quit_no", lang), callback_data=f"quit:no:{test_key}")
    builder.adjust(1)
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
    """Javob tugmalari. Test kaliti tugmaning o'zida — bot qayta ishga tushsa ham
    eski savol tugmasi qaysi testga tegishli ekani aniq bo'ladi."""
    item = REGISTRY[test_key].items[index]
    builder = InlineKeyboardBuilder()
    for value, text in enumerate(item.answers(lang)):
        builder.button(text=text, callback_data=f"ans:{test_key}:{index}:{value}")
    builder.adjust(1)
    row = []
    if index > 0:
        row.append(InlineKeyboardButton(text=t("btn_back", lang), callback_data=f"back:{test_key}"))
    row.append(InlineKeyboardButton(text=t("btn_cancel", lang), callback_data=f"nav:cancel:{test_key}"))
    builder.row(*row)
    return builder.as_markup()


def next_test_button(builder: InlineKeyboardBuilder, test_key: str, lang: str) -> None:
    """Hisobot oxirida taklif qilingan boshqa test (report.next_step bilan bir xil)."""
    other = next_test_title(test_key, lang)
    if other:
        key, title = other
        data = "iq:card" if key == IQ_KEY else f"test:{key}"
        builder.button(text=t("btn_next_test", lang, title=title), callback_data=data)


def result_menu(test_key: str, lang: str, share_url: str | None = None) -> InlineKeyboardMarkup:
    """To'liq tahlil ostidagi tugmalar. share_url — foydalanuvchining taklif havolasi bilan."""
    import compare

    builder = InlineKeyboardBuilder()
    if share_url:
        builder.button(text=t("btn_share", lang), url=share_url)
    elif BOT_USERNAME:
        share = quote(t("share_text", lang))
        builder.button(text=t("btn_share", lang), url=f"https://t.me/share/url?url=https://t.me/{BOT_USERNAME}&text={share}")
    compare.add_button(builder, test_key, lang)
    next_test_button(builder, test_key, lang)
    builder.button(text=t("btn_retake", lang), callback_data=f"go:{test_key}")
    builder.button(text=t("btn_other_tests", lang), callback_data="nav:menu")
    builder.adjust(1)
    return builder.as_markup()


def back_to_menu(lang: str, other_tests: bool = False) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=t("btn_other_tests" if other_tests else "btn_menu", lang), callback_data="nav:menu")
    return builder.as_markup()


def start_test(test_key: str, lang: str) -> InlineKeyboardMarkup:
    """Test oldidan ekranga olib boradigan tugma."""
    builder = InlineKeyboardBuilder()
    builder.button(text=t("btn_start_test", lang), callback_data="iq:card" if test_key == IQ_KEY else f"test:{test_key}")
    builder.button(text=t("btn_menu", lang), callback_data="nav:menu")
    builder.adjust(1)
    return builder.as_markup()


def admin_menu() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for text, data in [
        ("📊 Statistika", "adm:stats"),
        ("⚡️ Tezlik", "perf:show"),
        ("📈 Tugatish darajasi", "adm:funnel"),
        ("👥 Oxirgi foydalanuvchilar", "adm:users"),
        ("🧩 Testlarni boshqarish", "adm:tests"),
        ("📥 Natijalarni yuklab olish", "adm:export"),
        ("📣 Xabar yuborish", "adm:broadcast"),
        ("💳 To‘lovlar", "adm:pay"),
        ("💰 Wallet / manual to‘lovlar", "adm:wallet"),
        ("👤 User / wallet boshqaruvi", "admuser:home"),
        ("🧠 IQ / premium sozlamalari", "admiq:home"),
        ("🚀 O‘sish: taklif, promo, eslatma", "grow:home"),
    ]:
        builder.button(text=text, callback_data=data)
    builder.adjust(2, 2, 2, 1, 1, 1, 1, 1, 1)
    return builder.as_markup()


def admin_back() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="⬅️ Admin panel", callback_data="adm:home")
    return builder.as_markup()


def admin_tests(disabled: set[str]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for key in ORDER:
        test = REGISTRY[key]
        mark = "🔴" if key in disabled else "🟢"
        builder.button(text=f"{mark} {test.emoji} {tr(test.title, 'uz')}", callback_data=f"admtest:{key}")
    builder.button(text="⬅️ Admin panel", callback_data="adm:home")
    builder.adjust(1)
    return builder.as_markup()


def admin_test_one(test_key: str, disabled: bool, page: int = 0) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🟢 Yoqish" if disabled else "🔴 O‘chirish", callback_data=f"admtoggle:{test_key}")
    builder.button(text="📄 Savollarni ko‘rish", callback_data=f"admq:{test_key}:0")
    builder.button(text="⬅️ Testlar", callback_data="adm:tests")
    builder.adjust(1)
    return builder.as_markup()


def admin_questions(test_key: str, page: int, pages: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    row = []
    if page > 0:
        row.append(InlineKeyboardButton(text="⬅️", callback_data=f"admq:{test_key}:{page - 1}"))
    if page + 1 < pages:
        row.append(InlineKeyboardButton(text="➡️", callback_data=f"admq:{test_key}:{page + 1}"))
    if row:
        builder.row(*row)
    builder.row(InlineKeyboardButton(text="⬅️ Testga qaytish", callback_data=f"admtest:{test_key}"))
    return builder.as_markup()


def broadcast_targets() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for text, data in [("🌍 Hammaga", "admto:all"), ("🇺🇿 Faqat o‘zbekcha", "admto:uz"), ("🇷🇺 Faqat ruscha", "admto:ru")]:
        builder.button(text=text, callback_data=data)
    builder.adjust(1)
    return builder.as_markup()


def broadcast_confirm() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Ha, yuborilsin", callback_data="adm:send")
    builder.button(text="❌ Bekor", callback_data="adm:cancel")
    builder.adjust(2)
    return builder.as_markup()


def pay_links(payment_id: int, url: str, lang: str, invoice: bool = False) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=t("btn_pay_open", lang), url=url)
    if invoice:
        builder.button(text=t("btn_pay_invoice", lang), callback_data=f"payinv:{payment_id}")
    builder.button(text=t("btn_pay_check", lang), callback_data=f"paychk:{payment_id}")
    builder.button(text=t("btn_back", lang), callback_data="nav:menu")
    builder.adjust(1)
    return builder.as_markup()


def admin_payments(admin_pays: bool = False, optimistic: bool = False) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🧪 Sinov rejimi: YOQIQ" if admin_pays else "🧪 Sinov rejimi: o‘chiq", callback_data="adm:testmode")
    builder.button(text="⚡️ Chekdan oldin ochish: YOQIQ" if optimistic else "⚡️ Chekdan oldin ochish: o‘chiq",
                   callback_data="adm:optimistic")
    builder.button(text="🧾 Oxirgi to‘lovlar", callback_data="adm:paylist")
    builder.button(text="💰 Narxlarni o‘zgartirish", callback_data="adm:prices")
    builder.button(text="🎁 To‘liq tahlil: pullik / bepul", callback_data="adm:freetests")
    builder.button(text="🔓 To‘liq tahlilni qo‘lda ochish", callback_data="adm:grant")
    builder.button(text="🔎 Click to‘ldirishlarini tekshirish", callback_data="adm:reconcile")
    builder.button(text="⬅️ Admin panel", callback_data="adm:home")
    builder.adjust(1)
    return builder.as_markup()


def admin_prices(products: list[tuple[str, str, int]]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for key, title, price in products:
        builder.button(text=f"{title} — {money(price)} so‘m", callback_data=f"admprice:{key}")
    builder.button(text="⬅️ To‘lovlar", callback_data="adm:pay")
    builder.adjust(1)
    return builder.as_markup()


def admin_paid_tests(free: set[str]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for key in ORDER:
        test = REGISTRY[key]
        mark = "🎁" if key in free else "💳"
        builder.button(text=f"{mark} {test.emoji} {tr(test.title, 'uz')}", callback_data=f"admfree:{key}")
    mark = "🎁" if IQ_KEY in free else "💳"
    builder.button(text=f"{mark} {IQ_EMOJI} IQ testi", callback_data=f"admfree:{IQ_KEY}")
    builder.button(text="⬅️ To‘lovlar", callback_data="adm:pay")
    builder.adjust(1)
    return builder.as_markup()
