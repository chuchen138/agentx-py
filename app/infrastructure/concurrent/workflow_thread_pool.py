from concurrent.futures import ThreadPoolExecutor
import multiprocessing
from typing import Optional, Callable, Any


class WorkflowThreadPool:
    """工作流线程池管理"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(WorkflowThreadPool, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, '_initialized'):
            self._max_workers = multiprocessing.cpu_count() * 2
            self._executor = ThreadPoolExecutor(
                max_workers=self._max_workers,
                thread_name_prefix="workflow-"
            )
            self._initialized = True
    
    def submit(self, task_callable: Callable, *args, **kwargs) -> Any:
        """提交任务到线程池"""
        return self._executor.submit(task_callable, *args, **kwargs)
    
    def shutdown(self, wait: bool = True):
        """关闭线程池"""
        self._executor.shutdown(wait=wait)
    
    def get_active_count(self) -> int:
        """获取活跃线程数"""
        # ThreadPoolExecutor 没有直接获取活跃线程数的方法
        # 这里返回估计值
        return min(self._max_workers, 10)  # 暂时返回一个估计值
    
    def get_queue_size(self) -> int:
        """获取队列大小"""
        # ThreadPoolExecutor 没有直接获取队列大小的方法
        # 这里返回估计值
        return 0  # 暂时返回0
    
    def get_max_workers(self) -> int:
        """获取最大工作线程数"""
        return self._max_workers
    
    def adjust_workers(self, new_max_workers: int):
        """调整工作线程数"""
        # 注意：ThreadPoolExecutor 不支持动态调整线程数
        # 这里只是记录新的最大值，实际生效需要重启
        self._max_workers = new_max_workers


# 全局线程池实例
workflow_thread_pool = WorkflowThreadPool()
