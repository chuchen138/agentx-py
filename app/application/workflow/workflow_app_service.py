from typing import List, Optional, Dict, Any
import uuid

from app.domain.workflow.model.schemas import WorkflowDTO, WorkflowCreateRequest
from app.domain.workflow.repository import WorkflowRepository
from app.domain.workflow.state_machine import AgentWorkflowStateMachine
from app.domain.workflow.constant.workflow_state import WorkflowState
from app.domain.workflow.event_bus import event_bus
from app.domain.workflow.constant.event_type import WorkflowEventType


class WorkflowAppService:
    """工作流应用服务"""
    
    def __init__(self, workflow_repository: WorkflowRepository):
        self.workflow_repository = workflow_repository
    
    def create_workflow(self, user_id: str, agent_id: str, session_id: str) -> WorkflowDTO:
        """创建工作流"""
        workflow_id = str(uuid.uuid4())
        workflow_data = {
            "workflow_id": workflow_id,
            "session_id": session_id,
            "user_id": user_id,
            "agent_id": agent_id,
            "status": "ACTIVE",
            "current_state": WorkflowState.INIT.value
        }
        
        workflow = self.workflow_repository.create(workflow_data)
        
        # 发布工作流创建事件
        event_bus.publish(
            WorkflowEventType.WORKFLOW_CREATED,
            workflow_id,
            {
                "workflow_id": workflow_id,
                "session_id": session_id,
                "user_id": user_id
            }
        )
        
        return WorkflowDTO.model_validate(workflow)
    
    def get_workflow(self, workflow_id: str) -> Optional[WorkflowDTO]:
        """获取工作流详情"""
        workflow = self.workflow_repository.get_by_id(workflow_id)
        if workflow:
            return WorkflowDTO.model_validate(workflow)
        return None
    
    def list_user_workflows(self, user_id: str, page: int, size: int) -> List[WorkflowDTO]:
        """获取用户工作流列表"""
        workflows = self.workflow_repository.get_by_user_id(user_id, page, size)
        return [WorkflowDTO.model_validate(workflow) for workflow in workflows]
    
    def list_session_workflows(self, session_id: str) -> List[WorkflowDTO]:
        """获取会话工作流列表"""
        workflows = self.workflow_repository.get_by_session_id(session_id)
        return [WorkflowDTO.model_validate(workflow) for workflow in workflows]
    
    def get_active_workflow(self, session_id: str) -> Optional[WorkflowDTO]:
        """获取活跃工作流"""
        workflows = self.workflow_repository.get_by_session_id(session_id)
        for workflow in workflows:
            if workflow.status == "ACTIVE":
                return WorkflowDTO.model_validate(workflow)
        return None
    
    def cancel_workflow(self, workflow_id: str, reason: str):
        """取消工作流"""
        self.workflow_repository.update_status(
            workflow_id,
            "CANCELLED",
            WorkflowState.FAILED.value
        )
        
        # 发布工作流失败事件
        event_bus.publish(
            WorkflowEventType.WORKFLOW_FAILED,
            workflow_id,
            {
                "error": f"Workflow cancelled: {reason}"
            }
        )
    
    def retry_workflow(self, workflow_id: str) -> WorkflowDTO:
        """重试工作流"""
        workflow = self.workflow_repository.get_by_id(workflow_id)
        if not workflow:
            raise ValueError(f"Workflow {workflow_id} not found")
        
        # 创建新的工作流实例
        new_workflow = self.create_workflow(
            workflow.user_id,
            workflow.agent_id,
            workflow.session_id
        )
        
        return new_workflow
    
    def replay_workflow(self, workflow_id: str) -> WorkflowDTO:
        """重放工作流"""
        # 与重试类似，创建新的工作流实例
        return self.retry_workflow(workflow_id)
    
    def check_workflow_exists(self, workflow_id: str) -> bool:
        """检查工作流是否存在"""
        workflow = self.workflow_repository.get_by_id(workflow_id)
        return workflow is not None
