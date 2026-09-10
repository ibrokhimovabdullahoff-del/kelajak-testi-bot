from aiogram import Router

# Patch legacy human-facing copy before handlers start serving messages.
import locales_patch  # noqa: F401

from . import admin, iq, payment, user, wallet
from .middleware import UserContext


def build_router() -> Router:
    router = Router()
    router.message.middleware(UserContext())
    router.callback_query.middleware(UserContext())
    router.include_router(admin.router)
    router.include_router(wallet.admin_router)
    router.include_router(payment.router)
    router.include_router(wallet.router)
    router.include_router(iq.router)
    router.include_router(user.router)
    return router
