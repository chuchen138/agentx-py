from abc import ABC, abstractmethod
from typing import Generic, TypeVar, Optional, Callable
from app.domain.workflow.constant.workflow_state import WorkflowState, can_transition
from app.domain.workflow.constant.event_type import WorkflowEventType
from app.domain.workflow.repository import WorkflowRepository


StateT = TypeVar('StateT')
EventT = TypeVar('EventT')


class StateMachine(ABC, Generic[StateT, EventT]):
    """状态机基类"""
    
    def __init__(self, initial_state: StateT):
        self._current_state = initial_state
        self._state_changed_callback: Optional[Callable[[StateT, StateT], None]] = None
    
    @abstractmethod
    def can_transition(self, to_state: StateT) -> bool:
        """验证是否可以转换到目标状态"""
        pass
    
    @abstractmethod
    def transition_to(self, new_state: StateT, trigger_event: Optional[EventT] = None) -> bool:
        """转换到新状态"""
        pass
    
    def get_current_state(self) -> StateT:
        """获取当前状态"""
        return self._current_state
    
    def on_state_changed(self, callback: Callable[[StateT, StateT], None]):
        """设置状态变更回调"""
        self._state_changed_callback = callback


class AgentWorkflowStateMachine(StateMachine[WorkflowState, WorkflowEventType]):
    """Agent工作流状态机"""
    
    def __init__(self, initial_state: WorkflowState, workflow_id: str, workflow_repository: WorkflowRepository):
        super().__init__(initial_state)
        self.workflow_id = workflow_id
        self.workflow_repository = workflow_repository
    
    def can_transition(self, to_state: WorkflowState) -> bool:
        """验证状态转换是否合法"""
        return can_transition(self._current_state, to_state)
    
    def transition_to(self, new_state: WorkflowState, trigger_event: Optional[WorkflowEventType] = None) -> bool:
        """转换到新状态"""
        if not self.can_transition(new_state):
            return False
        
        old_state = self._current_state
        self._current_state = new_state
        
        # 持久化状态
        self.persist_state()
        
        # 触发状态变更回调
        if self._state_changed_callback:
            self._state_changed_callback(old_state, new_state)
        
        return True
    
    def persist_state(self):
        """持久化状态到数据库"""
        try:
            self.workflow_repository.update_status(
                self.workflow_id,
                self._current_state.value,
                self._current_state.value
            )
        except Exception as e:
            # 记录错误但不影响状态转换
            print(f"Failed to persist workflow state: {e}")
    
    def restore_state(self, workflow_id: str):
        """从数据库恢复状态"""
        workflow = self.workflow_repository.get_by_id(workflow_id)
        if workflow:
            try:
                self._current_state = WorkflowState(workflow.current_state)
                return True
            except ValueError:
                # 状态值无效，使用初始状态
                self._current_state = WorkflowState.INIT
        return False
