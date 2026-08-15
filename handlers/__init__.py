from aiogram import Router

from . import admin, user
from .middleware import UserContext


def build_router() -> Router:
    router = Router()
    router.message.middleware(UserContext())
    router.callback_query.middleware(UserContext())
    # Admin birinchi: u o'z filtri bilan cheklangan, mos kelmasa
    # boshqaruv user routerga o'tadi.
    router.include_router(admin.router)
    router.include_router(user.router)
    return router
