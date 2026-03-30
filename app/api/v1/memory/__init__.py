from fastapi import APIRouter
from app.api.v1.memory.routes import router as memory_router

router = APIRouter()
router.include_router(memory_router, prefix="/memories", tags=["memory"])
