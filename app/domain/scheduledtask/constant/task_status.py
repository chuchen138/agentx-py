from enum import Enum


class ScheduleTaskStatus(str, Enum):
    """任务状态枚举"""
    PENDING = "pending"          # 待执行
    RUNNING = "running"          # 执行中
    COMPLETED = "completed"      # 已完成
    FAILED = "failed"            # 执行失败
    PAUSED = "paused"            # 已暂停

    @classmethod
    def can_transition_to(cls, from_status: "ScheduleTaskStatus", to_status: "ScheduleTaskStatus") -> bool:
        """检查状态转换是否合法"""
        valid_transitions = {
            cls.PENDING: [cls.RUNNING, cls.FAILED, cls.PAUSED],
            cls.RUNNING: [cls.COMPLETED, cls.FAILED],
            cls.FAILED: [cls.PENDING],
            cls.PAUSED: [cls.PENDING],
            cls.COMPLETED: [cls.PENDING],  # 重复任务完成后变为待执行
        }
        return to_status in valid_transitions.get(from_status, [])
