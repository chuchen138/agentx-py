from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.auth.routes import router as auth_router
from app.api.v1.users.routes import router as users_router
from app.api import api_router as file_router
from app.core.database import create_tables

# 创建数据库表
create_tables()

app = FastAPI(
    title="AgentX API",
    description="AgentX 核心 API",
    version="1.0.0"
)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有来源，生产环境应该设置具体的域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(auth_router, prefix="/api/v1/auth", tags=["认证"])
app.include_router(users_router, prefix="/api/v1/users", tags=["用户管理"])
app.include_router(file_router, prefix="/api")

@app.get("/")
def root():
    return {"message": "AgentX API"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}
