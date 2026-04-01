from enum import Enum


class TaskStatus(Enum):
    """任务状态枚举"""
    PENDING = "PENDING"  # 待执行
    RUNNING = "RUNNING"  # 执行中
    COMPLETED = "COMPLETED"  # 完成
    FAILED = "FAILED"  # 失败
    CANCELLED = "CANCELLED"  # 已取消


# 任务状态转换规则
TASK_STATE_TRANSITIONS = {
    TaskStatus.PENDING: [TaskStatus.RUNNING, TaskStatus.CANCELLED],
    TaskStatus.RUNNING: [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED],
    TaskStatus.COMPLETED: [],
    TaskStatus.FAILED: [],
    TaskStatus.CANCELLED: [],
}


def can_task_transition(from_status: TaskStatus, to_status: TaskStatus) -> bool:
    """验证任务状态转换是否合法"""
    return to_status in TASK_STATE_TRANSITIONS.get(from_status, [])
