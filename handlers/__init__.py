from aiogram import Router

import locales_patch  # noqa: F401
import database_attempts_patch  # noqa: F401  # one paid purchase = one completed attempt

from . import admin_cms, admin, admin_premium, admin_users, iq, payment, shop, user, user_cms_patch, wallet, wallet_admin, wallet_click
from .middleware import UserContext


def build_router() -> Router:
    router = Router()
    router.message.middleware(UserContext())
    router.callback_query.middleware(UserContext())
    # CMS and wallet admin states must run before the general admin handlers.
    router.include_router(admin_cms.router)
    router.include_router(wallet_admin.router)
    router.include_router(admin.router)
    router.include_router(admin_premium.router)
    router.include_router(admin_users.router)
    router.include_router(wallet.admin_router)
    router.include_router(wallet_click.router)
    router.include_router(payment.router)
    router.include_router(wallet.router)
    router.include_router(shop.router)
    router.include_router(iq.router)
    router.include_router(user.router)
    return router
