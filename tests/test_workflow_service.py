import pytest
from unittest.mock import Mock, MagicMock

from app.application.workflow.workflow_app_service import WorkflowAppService
from app.application.workflow.task_app_service import TaskAppService
from app.application.workflow.summary_app_service import SummaryAppService
from app.domain.workflow.state_machine import AgentWorkflowStateMachine
from app.domain.workflow.constant.workflow_state import WorkflowState


class TestWorkflowAppService:
    """测试工作流应用服务"""
    
    def setup_method(self):
        """设置测试环境"""
        self.workflow_repository = Mock()
        self.workflow_service = WorkflowAppService(self.workflow_repository)
    
    def test_create_workflow(self):
        """测试创建工作流"""
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
        
        # 调用服务方法
        workflow = self.workflow_service.create_workflow(
            user_id="user-123",
            agent_id="agent-123",
            session_id="session-123"
        )
        
        # 验证结果
        assert workflow.workflow_id is not None
        assert workflow.status == "ACTIVE"
        assert workflow.current_state == "INIT"
    
    def test_get_workflow(self):
        """测试获取工作流"""
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
        
        self.workflow_repository.get_by_id.return_value = mock_workflow
        
        # 调用服务方法
        workflow = self.workflow_service.get_workflow("wf-123")
        
        # 验证结果
        assert workflow is not None
        assert workflow.workflow_id == "wf-123"


class TestTaskAppService:
    """测试任务应用服务"""
    
    def setup_method(self):
        """设置测试环境"""
        self.task_repository = Mock()
        self.task_service = TaskAppService(self.task_repository)
    
    def test_get_task(self):
        """测试获取任务"""
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
        
        # 调用服务方法
        task = self.task_service.get_task("task-123")
        
        # 验证结果
        assert task is not None
        assert task.task_id == "task-123"
        assert task.task_name == "Test Task"


class TestSummaryAppService:
    """测试摘要应用服务"""
    
    def setup_method(self):
        """设置测试环境"""
        self.summary_repository = Mock()
        self.summarize_handler = Mock()
        self.summary_service = SummaryAppService(self.summary_repository, self.summarize_handler)
    
    def test_get_summary(self):
        """测试获取摘要"""
        # 模拟仓储方法
        mock_summary = Mock()
        mock_summary.id = "1"
        mock_summary.summary_id = "sum-123"
        mock_summary.session_id = "session-123"
        mock_summary.workflow_id = "wf-123"
        mock_summary.summary_text = "Test summary"
        mock_summary.token_count = 100
        mock_summary.created_at = Mock()
        
        self.summary_repository.get_by_session_id.return_value = mock_summary
        
        # 调用服务方法
        summary = self.summary_service.get_summary("session-123")
        
        # 验证结果
        assert summary is not None
        assert summary.summary_id == "sum-123"
        assert summary.summary_text == "Test summary"


class TestAgentWorkflowStateMachine:
    """测试工作流状态机"""
    
    def setup_method(self):
        """设置测试环境"""
        self.workflow_repository = Mock()
        self.state_machine = AgentWorkflowStateMachine(
            initial_state=WorkflowState.INIT,
            workflow_id="wf-123",
            workflow_repository=self.workflow_repository
        )
    
    def test_initial_state(self):
        """测试初始状态"""
        assert self.state_machine.get_current_state() == WorkflowState.INIT
    
    def test_state_transition(self):
        """测试状态转换"""
        # 测试从INIT到ANALYZING
        result = self.state_machine.transition_to(WorkflowState.ANALYZING)
        assert result is True
        assert self.state_machine.get_current_state() == WorkflowState.ANALYZING
        
        # 测试从ANALYZING到SPLITTING
        result = self.state_machine.transition_to(WorkflowState.SPLITTING)
        assert result is True
        assert self.state_machine.get_current_state() == WorkflowState.SPLITTING
        
        # 测试从SPLITTING到EXECUTING
        result = self.state_machine.transition_to(WorkflowState.EXECUTING)
        assert result is True
        assert self.state_machine.get_current_state() == WorkflowState.EXECUTING
