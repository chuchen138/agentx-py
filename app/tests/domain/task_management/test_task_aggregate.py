import pytest
from app.domain.task_management.model.task_entity import TaskEntity
from app.domain.task_management.model.task_aggregate import TaskAggregate
from app.domain.task_management.constant.task_status import TaskStatus


class TestTaskAggregate:
    """测试 TaskAggregate 类"""
    
    def test_aggregate_creation(self):
        """测试聚合根创建"""
        # 创建父任务
        parent_task = TaskEntity(
            session_id="session-123",
            user_id="user-123",
            task_name="Parent Task"
        )
        
        # 创建子任务
        sub_task1 = TaskEntity(
            session_id="session-123",
            user_id="user-123",
            task_name="Sub Task 1",
            parent_task_id=parent_task.id
        )
        
        sub_task2 = TaskEntity(
            session_id="session-123",
            user_id="user-123",
            task_name="Sub Task 2",
            parent_task_id=parent_task.id
        )
        
        # 创建聚合根
        aggregate = TaskAggregate(parent_task, [sub_task1, sub_task2])
        
        assert aggregate.task == parent_task
        assert len(aggregate.sub_tasks) == 2
        assert aggregate.sub_tasks[0] == sub_task1
        assert aggregate.sub_tasks[1] == sub_task2
    
    def test_is_all_completed_no_subtasks(self):
        """测试没有子任务时的 is_all_completed 方法"""
        # 创建任务
        task = TaskEntity(
            session_id="session-123",
            user_id="user-123",
            task_name="Test Task"
        )
        
        # 创建聚合根
        aggregate = TaskAggregate(task, [])
        
        # 任务未完成
        assert not aggregate.is_all_completed()
        
        # 任务完成
        task.update_status(TaskStatus.COMPLETED, 0)
        assert aggregate.is_all_completed()
    
    def test_is_all_completed_with_subtasks(self):
        """测试有子任务时的 is_all_completed 方法"""
        # 创建父任务
        parent_task = TaskEntity(
            session_id="session-123",
            user_id="user-123",
            task_name="Parent Task"
        )
        
        # 创建子任务
        sub_task1 = TaskEntity(
            session_id="session-123",
            user_id="user-123",
            task_name="Sub Task 1",
            parent_task_id=parent_task.id
        )
        
        sub_task2 = TaskEntity(
            session_id="session-123",
            user_id="user-123",
            task_name="Sub Task 2",
            parent_task_id=parent_task.id
        )
        
        # 创建聚合根
        aggregate = TaskAggregate(parent_task, [sub_task1, sub_task2])
        
        # 子任务未完成
        assert not aggregate.is_all_completed()
        
        # 一个子任务完成
        sub_task1.update_status(TaskStatus.COMPLETED, 0)
        assert not aggregate.is_all_completed()
        
        # 所有子任务完成
        sub_task2.update_status(TaskStatus.COMPLETED, 0)
        assert aggregate.is_all_completed()
    
    def test_to_dict(self):
        """测试转换为字典"""
        # 创建父任务
        parent_task = TaskEntity(
            session_id="session-123",
            user_id="user-123",
            task_name="Parent Task"
        )
        
        # 创建子任务
        sub_task = TaskEntity(
            session_id="session-123",
            user_id="user-123",
            task_name="Sub Task",
            parent_task_id=parent_task.id
        )
        
        # 创建聚合根
        aggregate = TaskAggregate(parent_task, [sub_task])
        
        # 转换为字典
        aggregate_dict = aggregate.to_dict()
        
        assert "task" in aggregate_dict
        assert "sub_tasks" in aggregate_dict
        assert len(aggregate_dict["sub_tasks"]) == 1
        assert aggregate_dict["task"]["task_name"] == "Parent Task"
        assert aggregate_dict["sub_tasks"][0]["task_name"] == "Sub Task"
