"""API 路由注册"""
from app.api.auth import router as auth_router
from app.api.courses import router as courses_router
from app.api.announcements import router as announcements_router
from app.api.chat import router as chat_router

__all__ = ["auth_router", "courses_router", "announcements_router", "chat_router"]
"""API 路由注册"""
from app.api.auth import router as auth_router
from app.api.courses import router as courses_router
from app.api.announcements import router as announcements_router
from app.api.chat import router as chat_router
from app.api.langchain_chat import router as langchain_chat_router

__all__ = [
    "auth_router",
    "courses_router",
    "announcements_router",
    "chat_router",
    "langchain_chat_router",
]
