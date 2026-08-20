from fastapi import APIRouter

from app.api import chat, decisions, resources, system


api_router = APIRouter()
api_router.include_router(system.router)
api_router.include_router(resources.router)
api_router.include_router(decisions.router)
api_router.include_router(chat.router)
