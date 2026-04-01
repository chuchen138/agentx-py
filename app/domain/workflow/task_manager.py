import asyncio
from concurrent.futures import ThreadPoolExecutor
from queue import PriorityQueue
from typing import Dict, List, Optional, Any
import uuid

from app.domain.workflow.constant.task_status import TaskStatus
from app.domain.workflow.constant.event_type import WorkflowEventType, EventPriority
from app.domain.workflow.repository import TaskRepository
from app.domain.workflow.event_bus import event_bus


class TaskInfo:
    """任务信息"""
    def __init__(self, task_id: str):
        self.task_id = task_id
        self.start_time = None
        self.status = TaskStatus.PENDING


class TaskManager:
    """任务管理器"""
    
    def __init__(self, task_repository: TaskRepository, max_workers: int = 16):
        self.task_repository = task_repository
        self._task_queue = PriorityQueue()
        self._executing_tasks: Dict[str, TaskInfo] = {}
        self._thread_pool = ThreadPoolExecutor(max_workers=max_workers)
        self._event_loop = asyncio.get_event_loop()
    
    def create_task(self, workflow_id: str, task_definition: Dict[str, Any]) -> Dict[str, Any]:
        """创建任务"""
        task_id = str(uuid.uuid4())
        task_data = {
            "task_id": task_id,
            "workflow_id": workflow_id,
            "task_name": task_definition.get("task_name"),
            "task_type": task_definition.get("task_type"),
            "description": task_definition.get("description"),
            "priority": task_definition.get("priority", 0),
            "depends_on": task_definition.get("depends_on", []),
            "status": TaskStatus.PENDING.value
        }
        
        task = self.task_repository.create(task_data)
        
        # 发布任务创建事件
        event_bus.publish(
            WorkflowEventType.TASK_CREATED,
            workflow_id,
            {
                "task_id": task.task_id,
                "task_name": task.task_name,
                "task_type": task.task_type
            }
        )
        
        # 调度任务
        self.schedule_task(task.task_id, task.priority)
        
        return {
            "task_id": task.task_id,
            "status": task.status
        }
    
    def schedule_task(self, task_id: str, priority: int = 0):
        """调度任务"""
        self._task_queue.put((-priority, task_id))  # 负数表示优先级高
        self._event_loop.create_task(self._process_task_queue())
    
    async def _process_task_queue(self):
        """处理任务队列"""
        while not self._task_queue.empty():
            _, task_id = self._task_queue.get()
            if task_id not in self._executing_tasks:
                await self.execute_task(task_id)
            self._task_queue.task_done()
    
    async def execute_task(self, task_id: str):
        """执行任务"""
        task = self.task_repository.get_by_id(task_id)
        if not task:
            return
        
        # 检查依赖是否满足
        if not self.check_dependencies_satisfied(task):
            # 依赖未满足，重新加入队列
            self.schedule_task(task_id, task.priority)
            return
        
        # 更新任务状态为运行中
        self.task_repository.update_status(task_id, TaskStatus.RUNNING.value)
        self._executing_tasks[task_id] = TaskInfo(task_id)
        
        try:
            # 在线程池中执行任务
            future = self._thread_pool.submit(self._execute_task_sync, task)
            result = await self._event_loop.run_in_executor(None, future.result)
            
            # 更新任务状态为完成
            self.complete_task(task_id, result)
        except Exception as e:
            # 更新任务状态为失败
            self.fail_task(task_id, str(e))
        finally:
            if task_id in self._executing_tasks:
                del self._executing_tasks[task_id]
    
    def _execute_task_sync(self, task) -> Dict[str, Any]:
        """同步执行任务"""
        # 这里应该根据任务类型执行不同的逻辑
        # 暂时返回模拟结果
        return {
            "result": f"Task {task.task_name} executed successfully",
            "task_type": task.task_type
        }
    
    def complete_task(self, task_id: str, result_data: Dict[str, Any]):
        """完成任务"""
        self.task_repository.update_status(
            task_id, 
            TaskStatus.COMPLETED.value, 
            result_data=result_data
        )
        
        # 发布任务完成事件
        task = self.task_repository.get_by_id(task_id)
        if task:
            event_bus.publish(
                WorkflowEventType.TASK_COMPLETED,
                task.workflow_id,
                {
                    "task_id": task.task_id,
                    "task_name": task.task_name,
                    "result_data": result_data
                }
            )
    
    def fail_task(self, task_id: str, error_message: str, should_retry: bool = True):
        """失败任务"""
        task = self.task_repository.get_by_id(task_id)
        if task:
            # 增加重试次数
            self.task_repository.increment_retry(task_id)
            
            if should_retry and task.retry_count < 5:
                # 重试任务
                self.schedule_task(task_id, task.priority)
            else:
                # 任务最终失败
                self.task_repository.update_status(
                    task_id, 
                    TaskStatus.FAILED.value, 
                    error_message=error_message
                )
                
                # 发布任务失败事件
                event_bus.publish(
                    WorkflowEventType.TASK_FAILED,
                    task.workflow_id,
                    {
                        "task_id": task.task_id,
                        "task_name": task.task_name,
                        "error_message": error_message,
                        "retry_count": task.retry_count
                    }
                )
    
    def cancel_task(self, task_id: str):
        """取消任务"""
        self.task_repository.update_status(
            task_id, 
            TaskStatus.CANCELLED.value,
            error_message="Task cancelled by user"
        )
        
        # 从执行队列中移除
        if task_id in self._executing_tasks:
            del self._executing_tasks[task_id]
    
    def get_task_status(self, task_id: str) -> Optional[TaskStatus]:
        """获取任务状态"""
        task = self.task_repository.get_by_id(task_id)
        if task:
            return TaskStatus(task.status)
        return None
    
    def get_pending_tasks(self, workflow_id: str) -> List[Dict[str, Any]]:
        """获取待执行任务列表"""
        tasks = self.task_repository.get_pending_tasks(workflow_id)
        return [
            {
                "task_id": task.task_id,
                "task_name": task.task_name,
                "task_type": task.task_type,
                "priority": task.priority,
                "depends_on": task.depends_on
            }
            for task in tasks
        ]
    
    def check_dependencies_satisfied(self, task) -> bool:
        """检查任务依赖是否满足"""
        if not task.depends_on:
            return True
        
        dependencies = self.task_repository.get_task_dependencies(task.task_id)
        for dep in dependencies:
            if dep.status != TaskStatus.COMPLETED.value:
                return False
        return True
    
    def shutdown(self):
        """关闭线程池"""
        self._thread_pool.shutdown(wait=True)
