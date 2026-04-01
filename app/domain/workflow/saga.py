from typing import List, Dict, Any
from datetime import datetime

from app.domain.workflow.event_bus import event_bus
from app.domain.workflow.constant.event_type import WorkflowEventType


class SagaCoordinator:
    """Saga协调器"""
    
    def __init__(self, workflow_id: str):
        self.workflow_id = workflow_id
        self.compensation_log = []
    
    def log_compensation(self, task: Dict[str, Any], result: Dict[str, Any]):
        """记录补偿操作"""
        self.compensation_log.append({
            'task_id': task.get('task_id'),
            'task_name': task.get('task_name'),
            'action': 'compensate',
            'original_result': result,
            'timestamp': datetime.now()
        })
    
    async def execute_compensation(self):
        """执行补偿"""
        for entry in reversed(self.compensation_log):
            await self._compensate_task(entry)
    
    async def _compensate_task(self, entry: Dict[str, Any], max_attempts: int = 3):
        """补偿单个任务"""
        for attempt in range(max_attempts):
            try:
                await self._do_compensate(entry)
                return
            except Exception as e:
                if attempt == max_attempts - 1:
                    print(f"Compensation failed after {max_attempts} attempts: {str(e)}")
                    # 发布补偿失败事件
                    event_bus.publish(
                        WorkflowEventType.WORKFLOW_FAILED,
                        self.workflow_id,
                        {
                            "error": f"Compensation failed for task {entry.get('task_id')}",
                            "task_name": entry.get('task_name')
                        }
                    )
                    raise
                import asyncio
                await asyncio.sleep(2 ** attempt)  # 指数退避
    
    async def _do_compensate(self, entry: Dict[str, Any]):
        """执行具体的补偿操作"""
        # 这里应该实现具体的补偿逻辑
        # 例如：删除临时文件、回滚数据库事务、发送取消通知等
        task_id = entry.get('task_id')
        task_name = entry.get('task_name')
        
        print(f"Compensating task {task_name} (ID: {task_id})")
        
        # 发布补偿事件
        event_bus.publish(
            WorkflowEventType.WORKFLOW_STATE_CHANGED,
            self.workflow_id,
            {
                "event": "compensation",
                "task_id": task_id,
                "task_name": task_name
            }
        )
    
    def get_compensation_log(self) -> List[Dict[str, Any]]:
        """获取补偿日志"""
        return self.compensation_log
