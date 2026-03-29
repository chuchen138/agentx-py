from fastapi import APIRouter
from .files import router as files_router
from .llm import llm_router
from .admin.llm import admin_llm_router
from .api_key.routes import router as api_key_router
from .rag.routes import router as rag_router
from .session import router as session_router

api_router = APIRouter()

# 注册文件存储相关路由
api_router.include_router(files_router, prefix="/files", tags=["files"])

# 注册LLM相关路由
api_router.include_router(llm_router)

# 注册API Key相关路由
api_router.include_router(api_key_router)

# 注册管理员LLM相关路由
api_router.include_router(admin_llm_router)

# 注册RAG相关路由
api_router.include_router(rag_router)

# 注册会话相关路由
api_router.include_router(session_router)
