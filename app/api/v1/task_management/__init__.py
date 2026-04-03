from fastapi import APIRouter
from app.api.v1.task_management.routes import router as task_management_router

router = APIRouter()
router.include_router(task_management_router)
