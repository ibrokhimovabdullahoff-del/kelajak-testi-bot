from aiogram import Router

from . import admin, payment, user
from .middleware import UserContext


def build_router() -> Router:
    router = Router()
    router.message.middleware(UserContext())
    router.callback_query.middleware(UserContext())
    # Admin birinchi: u o'z filtri bilan cheklangan, mos kelmasa
    # boshqaruv keyingi routerga o'tadi.
    router.include_router(admin.router)
    # To'lov user'dan OLDIN turishi shart: user.py oxirida hamma xabarni
    # ushlaydigan fallback bor, u telefon raqamini yutib yuborardi.
    router.include_router(payment.router)
    router.include_router(user.router)
    return router
