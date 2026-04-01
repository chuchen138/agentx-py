import pytest
from unittest.mock import Mock
import time

from app.application.workflow.workflow_app_service import WorkflowAppService
from app.application.workflow.task_app_service import TaskAppService
from app.domain.workflow.event_bus import event_bus


class TestWorkflowPerformance:
    """测试工作流性能"""
    
    def setup_method(self):
        """设置测试环境"""
        self.workflow_repository = Mock()
        self.task_repository = Mock()
        self.workflow_service = WorkflowAppService(self.workflow_repository)
        self.task_service = TaskAppService(self.task_repository)
    
    def test_workflow_creation_performance(self):
        """测试工作流创建性能"""
        # 模拟仓储方法
        mock_workflow = Mock()
        mock_workflow.id = "1"
        mock_workflow.workflow_id = "wf-123"
        mock_workflow.session_id = "session-123"
        mock_workflow.user_id = "user-123"
        mock_workflow.agent_id = "agent-123"
        mock_workflow.status = "ACTIVE"
        mock_workflow.current_state = "INIT"
        mock_workflow.created_at = Mock()
        mock_workflow.updated_at = Mock()
        mock_workflow.completed_at = None
        
        self.workflow_repository.create.return_value = mock_workflow
        
        # 测试创建100个工作流的时间
        start_time = time.time()
        for i in range(100):
            self.workflow_service.create_workflow(
                user_id=f"user-{i}",
                agent_id="agent-123",
                session_id=f"session-{i}"
            )
        end_time = time.time()
        
        # 验证性能
        elapsed_time = end_time - start_time
        print(f"Created 100 workflows in {elapsed_time:.2f} seconds")
        assert elapsed_time < 5.0  # 5秒内完成
    
    def test_task_execution_performance(self):
        """测试任务执行性能"""
        # 模拟仓储方法
        mock_task = Mock()
        mock_task.id = "1"
        mock_task.task_id = "task-123"
        mock_task.workflow_id = "wf-123"
        mock_task.task_name = "Test Task"
        mock_task.task_type = "DATA_ANALYSIS"
        mock_task.status = "PENDING"
        mock_task.priority = 0
        mock_task.depends_on = []
        mock_task.retry_count = 0
        mock_task.created_at = Mock()
        mock_task.started_at = None
        mock_task.completed_at = None
        
        self.task_repository.get_by_id.return_value = mock_task
        
        # 测试获取100个任务的时间
        start_time = time.time()
        for i in range(100):
            self.task_service.get_task(f"task-{i}")
        end_time = time.time()
        
        # 验证性能
        elapsed_time = end_time - start_time
        print(f"Retrieved 100 tasks in {elapsed_time:.2f} seconds")
        assert elapsed_time < 2.0  # 2秒内完成
    
    def test_event_bus_performance(self):
        """测试事件总线性能"""
        # 测试发布1000个事件的时间
        start_time = time.time()
        for i in range(1000):
            event_bus.publish(
                Mock(),
                f"wf-{i}",
                {"test": "data"}
            )
        end_time = time.time()
        
        # 验证性能
        elapsed_time = end_time - start_time
        print(f"Published 1000 events in {elapsed_time:.2f} seconds")
        assert elapsed_time < 1.0  # 1秒内完成
