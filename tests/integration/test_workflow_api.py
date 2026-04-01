import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock

from app.application.workflow.workflow_app_service import WorkflowAppService
from app.application.workflow.task_app_service import TaskAppService
from app.application.workflow.summary_app_service import SummaryAppService
from app.api.v1.workflow.workflow_routes import router as workflow_router
from app.api.v1.workflow.task_routes import router as task_router
from app.api.v1.workflow.summary_routes import router as summary_router
from app.api.v1.workflow.event_routes import router as event_router
from fastapi import FastAPI


@pytest.fixture
def app():
    """创建测试应用"""
    app = FastAPI()
    app.include_router(workflow_router)
    app.include_router(task_router)
    app.include_router(summary_router)
    app.include_router(event_router)
    return app


@pytest.fixture
def client(app):
    """创建测试客户端"""
    return TestClient(app)


@pytest.fixture
def workflow_service():
    """创建工作流服务模拟"""
    return Mock(spec=WorkflowAppService)


@pytest.fixture
def task_service():
    """创建任务服务模拟"""
    return Mock(spec=TaskAppService)


@pytest.fixture
def summary_service():
    """创建摘要服务模拟"""
    return Mock(spec=SummaryAppService)


# 测试工作流API
def test_create_workflow(client, workflow_service, monkeypatch):
    """测试创建工作流API"""
    # 模拟服务方法
    def mock_create_workflow(user_id, agent_id, session_id):
        mock_workflow = Mock()
        mock_workflow.id = "1"
        mock_workflow.workflow_id = "wf-123"
        mock_workflow.session_id = session_id
        mock_workflow.user_id = user_id
        mock_workflow.agent_id = agent_id
        mock_workflow.status = "ACTIVE"
        mock_workflow.current_state = "INIT"
        mock_workflow.created_at = Mock()
        mock_workflow.updated_at = Mock()
        mock_workflow.completed_at = None
        return mock_workflow
    
    workflow_service.create_workflow = mock_create_workflow
    
    # 替换依赖注入
    def get_workflow_service():
        return workflow_service
    
    monkeypatch.setattr("app.api.v1.workflow.workflow_routes.WorkflowAppService", get_workflow_service)
    
    # 发送请求
    response = client.post("/api/v1/workflows", json={
        "session_id": "session-123",
        "user_id": "user-123",
        "agent_id": "agent-123"
    })
    
    # 验证响应
    assert response.status_code == 200
    data = response.json()
    assert data["workflow_id"] == "wf-123"
    assert data["status"] == "ACTIVE"


def test_get_workflow(client, workflow_service, monkeypatch):
    """测试获取工作流详情API"""
    # 模拟服务方法
    def mock_get_workflow(workflow_id):
        mock_workflow = Mock()
        mock_workflow.id = "1"
        mock_workflow.workflow_id = workflow_id
        mock_workflow.session_id = "session-123"
        mock_workflow.user_id = "user-123"
        mock_workflow.agent_id = "agent-123"
        mock_workflow.status = "ACTIVE"
        mock_workflow.current_state = "INIT"
        mock_workflow.created_at = Mock()
        mock_workflow.updated_at = Mock()
        mock_workflow.completed_at = None
        return mock_workflow
    
    workflow_service.get_workflow = mock_get_workflow
    
    # 替换依赖注入
    def get_workflow_service():
        return workflow_service
    
    monkeypatch.setattr("app.api.v1.workflow.workflow_routes.WorkflowAppService", get_workflow_service)
    
    # 发送请求
    response = client.get("/api/v1/workflows/wf-123")
    
    # 验证响应
    assert response.status_code == 200
    data = response.json()
    assert data["workflow_id"] == "wf-123"
    assert data["status"] == "ACTIVE"


def test_list_workflow_tasks(client, task_service, monkeypatch):
    """测试获取工作流任务列表API"""
    # 模拟服务方法
    def mock_list_workflow_tasks(workflow_id):
        mock_task = Mock()
        mock_task.id = "1"
        mock_task.task_id = "task-123"
        mock_task.workflow_id = workflow_id
        mock_task.task_name = "Test Task"
        mock_task.task_type = "DATA_ANALYSIS"
        mock_task.status = "PENDING"
        mock_task.priority = 0
        mock_task.depends_on = []
        mock_task.retry_count = 0
        mock_task.created_at = Mock()
        mock_task.started_at = None
        mock_task.completed_at = None
        return [mock_task]
    
    task_service.list_workflow_tasks = mock_list_workflow_tasks
    
    # 替换依赖注入
    def get_task_service():
        return task_service
    
    monkeypatch.setattr("app.api.v1.workflow.task_routes.TaskAppService", get_task_service)
    
    # 发送请求
    response = client.get("/api/v1/workflows/wf-123/tasks")
    
    # 验证响应
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["task_id"] == "task-123"
    assert data[0]["task_name"] == "Test Task"
