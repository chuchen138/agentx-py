import pytest
from datetime import datetime
from app.domain.task_management.model.task_entity import TaskEntity, OptimisticLockException, InvalidStatusTransitionException
from app.domain.task_management.constant.task_status import TaskStatus


class TestTaskEntity:
    """测试 TaskEntity 类"""
    
    def test_task_creation(self):
        """测试任务创建"""
        task = TaskEntity(
            session_id="session-123",
            user_id="user-123",
            task_name="Test Task",
            description="Test Description"
        )
        
        assert task.session_id == "session-123"
        assert task.user_id == "user-123"
        assert task.task_name == "Test Task"
        assert task.description == "Test Description"
        assert task.status == TaskStatus.WAITING.value
        assert task.progress == 0
        assert task.version == 0
    
    def test_update_status_to_in_progress(self):
        """测试更新状态为 IN_PROGRESS"""
        task = TaskEntity(
            session_id="session-123",
            user_id="user-123",
            task_name="Test Task"
        )
        
        # 更新状态为 IN_PROGRESS
        task.update_status(TaskStatus.IN_PROGRESS, 0)
        
        assert task.status == TaskStatus.IN_PROGRESS.value
        assert task.version == 1
        assert task.start_time is not None
    
    def test_update_status_to_completed(self):
        """测试更新状态为 COMPLETED"""
        task = TaskEntity(
            session_id="session-123",
            user_id="user-123",
            task_name="Test Task"
        )
        
        # 先更新为 IN_PROGRESS
        task.update_status(TaskStatus.IN_PROGRESS, 0)
        start_time = task.start_time
        
        # 再更新为 COMPLETED
        task.update_status(TaskStatus.COMPLETED, 1)
        
        assert task.status == TaskStatus.COMPLETED.value
        assert task.version == 2
        assert task.start_time == start_time
        assert task.end_time is not None
    
    def test_update_status_to_failed(self):
        """测试更新状态为 FAILED"""
        task = TaskEntity(
            session_id="session-123",
            user_id="user-123",
            task_name="Test Task"
        )
        
        # 先更新为 IN_PROGRESS
        task.update_status(TaskStatus.IN_PROGRESS, 0)
        start_time = task.start_time
        
        # 再更新为 FAILED
        task.update_status(TaskStatus.FAILED, 1)
        
        assert task.status == TaskStatus.FAILED.value
        assert task.version == 2
        assert task.start_time == start_time
        assert task.end_time is not None
    
    def test_invalid_status_transition(self):
        """测试无效状态转换"""
        task = TaskEntity(
            session_id="session-123",
            user_id="user-123",
            task_name="Test Task"
        )
        
        # 直接从 WAITING 转换到 COMPLETED 应该失败
        with pytest.raises(InvalidStatusTransitionException):
            task.update_status(TaskStatus.COMPLETED, 0)
    
    def test_optimistic_lock_exception(self):
        """测试乐观锁异常"""
        task = TaskEntity(
            session_id="session-123",
            user_id="user-123",
            task_name="Test Task"
        )
        
        # 使用错误的版本号
        with pytest.raises(OptimisticLockException):
            task.update_status(TaskStatus.IN_PROGRESS, 1)
    
    def test_to_dict(self):
        """测试转换为字典"""
        task = TaskEntity(
            session_id="session-123",
            user_id="user-123",
            task_name="Test Task",
            description="Test Description"
        )
        
        task_dict = task.to_dict()
        
        assert task_dict["session_id"] == "session-123"
        assert task_dict["user_id"] == "user-123"
        assert task_dict["task_name"] == "Test Task"
        assert task_dict["description"] == "Test Description"
        assert task_dict["status"] == TaskStatus.WAITING.value
        assert task_dict["progress"] == 0
        assert task_dict["version"] == 0
