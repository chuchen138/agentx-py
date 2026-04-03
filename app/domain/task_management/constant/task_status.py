from enum import Enum


class TaskStatus(Enum):
    """任务状态枚举"""
    WAITING = "WAITING"  # 等待中
    IN_PROGRESS = "IN_PROGRESS"  # 进行中
    COMPLETED = "COMPLETED"  # 已完成
    FAILED = "FAILED"  # 失败


# 任务状态转换规则
TASK_STATUS_TRANSITIONS = {
    TaskStatus.WAITING: [TaskStatus.IN_PROGRESS],
    TaskStatus.IN_PROGRESS: [TaskStatus.COMPLETED, TaskStatus.FAILED],
    TaskStatus.COMPLETED: [],
    TaskStatus.FAILED: [],
}


def is_valid_status_transition(from_status: TaskStatus, to_status: TaskStatus) -> bool:
    """验证状态转换是否合法"""
    return to_status in TASK_STATUS_TRANSITIONS.get(from_status, [])
