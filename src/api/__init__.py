from fastapi import APIRouter

from .books import router as books_router
#from src.api.users import router as users_router

main_router = APIRouter()

main_router.include_router(books_router)


