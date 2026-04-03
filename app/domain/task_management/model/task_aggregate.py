from typing import List
from app.domain.task_management.model.task_entity import TaskEntity
from app.domain.task_management.constant.task_status import TaskStatus


class TaskAggregate:
    """任务聚合根"""
    
    def __init__(self, task: TaskEntity, sub_tasks: List[TaskEntity]):
        self.task = task  # 父任务或独立任务
        self.sub_tasks = sub_tasks  # 子任务列表（可为空）
    
    def is_all_completed(self) -> bool:
        """检查所有任务是否完成"""
        if not self.sub_tasks:
            return self.task.status == TaskStatus.COMPLETED.value
        return all(t.status == TaskStatus.COMPLETED.value for t in self.sub_tasks)
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "task": self.task.to_dict(),
            "sub_tasks": [task.to_dict() for task in self.sub_tasks]
        }
