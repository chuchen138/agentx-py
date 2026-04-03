from fastapi import APIRouter
from .files import router as files_router
from .llm import llm_router
from .admin.llm import admin_llm_router
from .api_key.routes import router as api_key_router
from .rag.routes import router as rag_router
from .session import router as session_router
from .memory import router as memory_router
from .workflow import router as workflow_router
from .workflow import task_routes, summary_routes, event_routes
from .task_management import router as task_management_router
from .endpoints.sse_endpoints import router as sse_router
from .websocket.agent_websocket import router as agent_ws_router
from .execution_trace.routes import router as execution_trace_router
from .mcp import router as mcp_router

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

# 注册记忆相关路由
api_router.include_router(memory_router)

# 注册工作流相关路由
api_router.include_router(workflow_router)
api_router.include_router(task_routes.router)
api_router.include_router(summary_routes.router)
api_router.include_router(event_routes.router)

# 注册执行追踪相关路由
api_router.include_router(execution_trace_router)

# 注册SSE流式响应端点
api_router.include_router(sse_router, tags=["sse"])

# 注册WebSocket路由
api_router.include_router(agent_ws_router)

# 注册MCP相关路由
api_router.include_router(mcp_router)

# 注册任务管理相关路由
api_router.include_router(task_management_router)

# 注册定时任务相关路由
from .scheduledtask import router as scheduled_task_router
api_router.include_router(scheduled_task_router)

# 注册账户相关路由
from .account.routes import router as account_router
api_router.include_router(account_router)

# 注册计费相关路由
from .billing.routes import router as billing_router
api_router.include_router(billing_router)

# 注册订单相关路由
from .orders.routes import router as orders_router
api_router.include_router(orders_router)

# 注册规则引擎相关路由
from .rule import router as rule_router
api_router.include_router(rule_router)
