from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
import os
from dotenv import load_dotenv

load_dotenv()

# 从环境变量中读取数据库URL
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///test.db")
# 对于PostgreSQL，不需要check_same_thread参数
connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}
engine = create_engine(DATABASE_URL, connect_args=connect_args)

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
    from app.domain.file.file_record import FileRecord
    from app.domain.auth.model import AuthSettingModel, VerificationCode
    Base.metadata.create_all(bind=engine)
