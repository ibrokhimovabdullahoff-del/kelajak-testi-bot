from aiogram import Router

import locales_patch  # noqa: F401

from . import admin, admin_premium, iq, payment, shop, user, wallet, wallet_admin
from .middleware import UserContext


def build_router() -> Router:
    router = Router()
    router.message.middleware(UserContext())
    router.callback_query.middleware(UserContext())
    router.include_router(admin.router)
    router.include_router(admin_premium.router)
    router.include_router(wallet.admin_router)
    router.include_router(wallet_admin.router)
    router.include_router(payment.router)
    router.include_router(wallet.router)
    router.include_router(shop.router)
    router.include_router(iq.router)
    router.include_router(user.router)
    return router
