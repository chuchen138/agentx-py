from fastapi import APIRouter
from app.api.v1.files import router as files_router

api_router = APIRouter()

# 注册文件存储相关路由
api_router.include_router(files_router, prefix="/files", tags=["files"])
