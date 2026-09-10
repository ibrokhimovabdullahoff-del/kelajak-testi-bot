from aiogram import Router

from . import admin, iq, payment, user, wallet
from .middleware import UserContext


def build_router() -> Router:
    router = Router()
    router.message.middleware(UserContext())
    router.callback_query.middleware(UserContext())
    # Admin first: its filter is restrictive, so unmatched callbacks continue.
    router.include_router(admin.router)
    # Wallet includes manual top-up states and its admin review router.
    router.include_router(wallet.admin_router)
    # Payment before user because user.py has a catch-all fallback.
    router.include_router(payment.router)
    router.include_router(wallet.router)
    router.include_router(iq.router)
    router.include_router(user.router)
    return router
