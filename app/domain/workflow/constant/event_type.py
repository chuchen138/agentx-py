from enum import Enum


class WorkflowEventType(Enum):
    """工作流事件类型枚举"""
    WORKFLOW_CREATED = "WORKFLOW_CREATED"  # 工作流创建
    WORKFLOW_STATE_CHANGED = "WORKFLOW_STATE_CHANGED"  # 工作流状态变更
    TASK_CREATED = "TASK_CREATED"  # 任务创建
    TASK_COMPLETED = "TASK_COMPLETED"  # 任务完成
    TASK_FAILED = "TASK_FAILED"  # 任务失败
    TOOL_CALLED = "TOOL_CALLED"  # 工具调用
    SUMMARY_GENERATED = "SUMMARY_GENERATED"  # 摘要生成
    WORKFLOW_COMPLETED = "WORKFLOW_COMPLETED"  # 工作流完成
    WORKFLOW_FAILED = "WORKFLOW_FAILED"  # 工作流失败
    TASK_PROGRESS = "TASK_PROGRESS"  # 任务进度


class EventPriority(Enum):
    """事件优先级枚举"""
    HIGH = 0  # 高优先级
    NORMAL = 1  # 正常优先级
    LOW = 2  # 低优先级
