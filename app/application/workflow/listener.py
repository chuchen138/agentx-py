from typing import Dict, Any

from app.domain.workflow.constant.event_type import WorkflowEventType
from app.domain.workflow.event_bus import event_bus
from app.domain.workflow.repository import WorkflowRepository, TaskRepository, SummaryRepository


class WorkflowEventListener:
    """工作流事件监听器"""
    
    def __init__(self, workflow_repository: WorkflowRepository):
        self.workflow_repository = workflow_repository
        self._register_listeners()
    
    def _register_listeners(self):
        """注册事件监听器"""
        event_bus.subscribe(WorkflowEventType.WORKFLOW_CREATED, self.on_workflow_created)
        event_bus.subscribe(WorkflowEventType.WORKFLOW_STATE_CHANGED, self.on_workflow_state_changed)
        event_bus.subscribe(WorkflowEventType.WORKFLOW_COMPLETED, self.on_workflow_completed)
        event_bus.subscribe(WorkflowEventType.WORKFLOW_FAILED, self.on_workflow_failed)
    
    async def on_workflow_created(self, event):
        """处理工作流创建事件"""
        workflow_id = event.workflow_id
        data = event.data
        print(f"Workflow created: {workflow_id}, data: {data}")
        # 记录工作流创建日志
        # 初始化工作流状态
    
    async def on_workflow_state_changed(self, event):
        """处理工作流状态变更事件"""
        workflow_id = event.workflow_id
        data = event.data
        print(f"Workflow state changed: {workflow_id}, data: {data}")
        # 持久化状态变更
        # 触发下一步处理
    
    async def on_workflow_completed(self, event):
        """处理工作流完成事件"""
        workflow_id = event.workflow_id
        data = event.data
        print(f"Workflow completed: {workflow_id}, data: {data}")
        # 记录完成时间
        # 发送完成通知
    
    async def on_workflow_failed(self, event):
        """处理工作流失败事件"""
        workflow_id = event.workflow_id
        data = event.data
        print(f"Workflow failed: {workflow_id}, data: {data}")
        # 记录错误信息
        # 触发告警
        # 尝试降级处理


class TaskEventListener:
    """任务事件监听器"""
    
    def __init__(self, task_repository: TaskRepository):
        self.task_repository = task_repository
        self._register_listeners()
    
    def _register_listeners(self):
        """注册事件监听器"""
        event_bus.subscribe(WorkflowEventType.TASK_CREATED, self.on_task_created)
        event_bus.subscribe(WorkflowEventType.TASK_COMPLETED, self.on_task_completed)
        event_bus.subscribe(WorkflowEventType.TASK_FAILED, self.on_task_failed)
    
    async def on_task_created(self, event):
        """处理任务创建事件"""
        workflow_id = event.workflow_id
        data = event.data
        print(f"Task created: {data.get('task_id')}, workflow: {workflow_id}")
        # 调度任务执行
        # 检查依赖关系
    
    async def on_task_completed(self, event):
        """处理任务完成事件"""
        workflow_id = event.workflow_id
        data = event.data
        print(f"Task completed: {data.get('task_id')}, workflow: {workflow_id}")
        # 更新任务状态
        # 触发依赖任务检查
        # 收集任务结果
    
    async def on_task_failed(self, event):
        """处理任务失败事件"""
        workflow_id = event.workflow_id
        data = event.data
        print(f"Task failed: {data.get('task_id')}, workflow: {workflow_id}, error: {data.get('error_message')}")
        # 记录失败日志
        # 判断是否重试
        # 传播失败到工作流


class ToolCallEventListener:
    """工具调用事件监听器"""
    
    def __init__(self):
        self._register_listeners()
    
    def _register_listeners(self):
        """注册事件监听器"""
        event_bus.subscribe(WorkflowEventType.TOOL_CALLED, self.on_tool_called)
    
    async def on_tool_called(self, event):
        """处理工具调用事件"""
        workflow_id = event.workflow_id
        data = event.data
        print(f"Tool called: {data.get('tool_name')}, task: {data.get('task_id')}")
        # 记录工具调用日志
        # 统计工具使用频率


class SummaryEventListener:
    """摘要生成事件监听器"""
    
    def __init__(self, summary_repository: SummaryRepository):
        self.summary_repository = summary_repository
        self._register_listeners()
    
    def _register_listeners(self):
        """注册事件监听器"""
        event_bus.subscribe(WorkflowEventType.SUMMARY_GENERATED, self.on_summary_generated)
    
    async def on_summary_generated(self, event):
        """处理摘要生成事件"""
        workflow_id = event.workflow_id
        data = event.data
        print(f"Summary generated: {data.get('summary_id')}, token count: {data.get('token_count')}")
        # 保存摘要到数据库
        # 更新上下文
        # 记录Token节省统计


# 注册监听器的函数
def register_event_listeners(
    workflow_repository: WorkflowRepository,
    task_repository: TaskRepository,
    summary_repository: SummaryRepository
):
    """注册所有事件监听器"""
    WorkflowEventListener(workflow_repository)
    TaskEventListener(task_repository)
    ToolCallEventListener()
    SummaryEventListener(summary_repository)
