import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from app.core.database import Base
from app.application.task_management.task_app_service import TaskAppService
from app.domain.task_management.constant.task_status import TaskStatus

# 测试数据库URL
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture
async def db_session():
    """创建测试数据库会话"""
    engine = create_async_engine(TEST_DATABASE_URL, echo=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    AsyncSessionLocal = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with AsyncSessionLocal() as session:
        yield session
    
    await engine.dispose()


class TestTaskAppService:
    """测试 TaskAppService 类"""
    
    async def test_create_task(self, db_session):
        """测试创建任务"""
        app_service = TaskAppService(db_session)
        
        # 创建任务
        result = await app_service.create_task(
            session_id="session-123",
            user_id="user-123",
            task_name="Test Task",
            description="Test Description"
        )
        
        assert result["session_id"] == "session-123"
        assert result["user_id"] == "user-123"
        assert result["task_name"] == "Test Task"
        assert result["description"] == "Test Description"
        assert result["status"] == TaskStatus.WAITING.value
        assert result["progress"] == 0
    
    async def test_update_task_status(self, db_session):
        """测试更新任务状态"""
        app_service = TaskAppService(db_session)
        
        # 创建任务
        task = await app_service.create_task(
            session_id="session-123",
            user_id="user-123",
            task_name="Test Task"
        )
        
        # 更新状态为 IN_PROGRESS
        updated_task = await app_service.update_task_status(
            task_id=task["id"],
            status=TaskStatus.IN_PROGRESS.value,
            user_id="user-123",
            version=0
        )
        
        assert updated_task["status"] == TaskStatus.IN_PROGRESS.value
        assert updated_task["version"] == 1
        assert updated_task["start_time"] is not None
        
        # 更新状态为 COMPLETED
        updated_task = await app_service.update_task_status(
            task_id=task["id"],
            status=TaskStatus.COMPLETED.value,
            user_id="user-123",
            version=1,
            progress=100,
            task_result="Task completed successfully"
        )
        
        assert updated_task["status"] == TaskStatus.COMPLETED.value
        assert updated_task["version"] == 2
        assert updated_task["progress"] == 100
        assert updated_task["task_result"] == "Task completed successfully"
        assert updated_task["end_time"] is not None
    
    async def test_update_task_progress(self, db_session):
        """测试更新任务进度"""
        app_service = TaskAppService(db_session)
        
        # 创建任务
        task = await app_service.create_task(
            session_id="session-123",
            user_id="user-123",
            task_name="Test Task"
        )
        
        # 更新进度
        updated_task = await app_service.update_task_progress(
            task_id=task["id"],
            progress=50,
            user_id="user-123"
        )
        
        assert updated_task["progress"] == 50
    
    async def test_get_current_session_tasks(self, db_session):
        """测试获取当前会话任务"""
        app_service = TaskAppService(db_session)
        
        # 创建父任务
        parent_task = await app_service.create_task(
            session_id="session-123",
            user_id="user-123",
            task_name="Parent Task"
        )
        
        # 创建子任务
        await app_service.create_task(
            session_id="session-123",
            user_id="user-123",
            task_name="Sub Task 1",
            parent_task_id=parent_task["id"]
        )
        
        await app_service.create_task(
            session_id="session-123",
            user_id="user-123",
            task_name="Sub Task 2",
            parent_task_id=parent_task["id"]
        )
        
        # 获取当前会话任务
        result = await app_service.get_current_session_tasks(
            session_id="session-123",
            user_id="user-123"
        )
        
        assert result is not None
        assert "task" in result
        assert "sub_tasks" in result
        assert len(result["sub_tasks"]) == 2
    
    async def test_delete_task(self, db_session):
        """测试删除任务"""
        app_service = TaskAppService(db_session)
        
        # 创建任务
        task = await app_service.create_task(
            session_id="session-123",
            user_id="user-123",
            task_name="Test Task"
        )
        
        # 删除任务
        await app_service.delete_task(
            task_id=task["id"],
            user_id="user-123"
        )
        
        # 尝试获取已删除的任务
        result = await app_service.get_current_session_tasks(
            session_id="session-123",
            user_id="user-123"
        )
        
        assert result is None
