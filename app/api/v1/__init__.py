from fastapi import APIRouter
from app.api.v1.files import router as files_router
from app.api.v1.llm import llm_router
from app.api.v1.admin.llm import admin_llm_router

api_router = APIRouter()

# 注册文件存储相关路由
api_router.include_router(files_router, prefix="/files", tags=["files"])

# 注册LLM相关路由
api_router.include_router(llm_router)

# 注册管理员LLM相关路由
api_router.include_router(admin_llm_router)
