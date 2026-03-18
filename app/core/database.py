from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
import os
from dotenv import load_dotenv

load_dotenv()

# 检查是否在测试环境
TESTING = os.getenv("TESTING", "False").lower() == "true"

if TESTING:
    # 使用SQLite文件数据库进行测试
    DATABASE_URL = "sqlite:///test.db"
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    # 使用PostgreSQL数据库
    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://admin:password@localhost:5432/agentx")
    engine = create_engine(DATABASE_URL)

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 创建基类
Base = declarative_base()

# 依赖项：获取数据库会话
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 创建所有表
def create_tables():
    # 确保所有模型都已导入
    from app.domain.user.model import UserModel, UserSettingsModel
    Base.metadata.create_all(bind=engine)
