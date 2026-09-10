from aiogram import Router

import locales_patch  # noqa: F401

from . import admin, admin_premium, admin_users, iq, iq_ui_patch, payment, shop, user, wallet, wallet_admin, wallet_click
from .middleware import UserContext


def build_router() -> Router:
    router = Router()
    router.message.middleware(UserContext())
    router.callback_query.middleware(UserContext())
    router.include_router(admin.router)
    router.include_router(admin_premium.router)
    router.include_router(admin_users.router)
    router.include_router(wallet.admin_router)
    router.include_router(wallet_admin.router)
    # Put the method chooser before wallet.py so wallet:topup can offer
    # both Click and the existing manual UZCARD/HUMO flow.
    router.include_router(wallet_click.router)
    router.include_router(payment.router)
    router.include_router(wallet.router)
    router.include_router(shop.router)
    router.include_router(iq.router)
    router.include_router(user.router)
    return router
